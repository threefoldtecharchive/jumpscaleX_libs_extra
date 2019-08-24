import json
import os
import re
import time

import requests
from Jumpscale import j
from pssh.exceptions import ConnectionErrorException, SessionError

DEFAULT_SSHKEY_NAME = "id_rsa"
DEFAULT_BITCOIN_DIR = "/root/.bitcoin"
DEFAULT_BITCOIN_CONT_DIR = "/.bitcoin"
DEFAULT_BITCOIN_CONFIG = """
rpcuser=user
rpcpassword=pass
testnet=1
rpcport=8332
rpcallowip=127.0.0.1
prune=550
server=1
"""
DEFAULT_BITCOIN_CONFIG_PATH = "{}/bitcoin.conf".format(DEFAULT_BITCOIN_DIR)
DEFAULT_BITCOIN_CONT_CONFIG_PATH = "{}/bitcoin.conf".format(DEFAULT_BITCOIN_CONT_DIR)
DEFAULT_TFT_WALLET_PASSPHRASE = "pass"
DEFAULT_DATA_PATH = "/mnt/data"


def tft_wallet_unlock(prefab, passphrase):
    """
    Unlock a tft wallet

    @param passphrase: Phasephrase to unlock the wallet
    """
    cmd = 'curl -A "Rivine-Agent" "localhost:23110/wallet"'
    rc, out, err = prefab.core.run(cmd, die=False, showout=False)
    if rc:
        raise j.exceptions.Base("Failed to unlock tft wallet. Error {}".format(err))
    json_out = json.loads(out)
    if json_out.get("unlocked") is False and json_out.get("encrypted") is True:
        cmd = 'curl -A "Rivine-Agent" --data "passphrase={}" "localhost:23110/wallet/unlock"'.format(passphrase)
        _, out, _ = prefab.core.run(cmd, showout=False)
        if out:
            stdout_error = json.loads(out).get("message")
            if stdout_error:
                raise j.exceptions.Base("Failed to unlock wallet. Error {}".format(stdout_error))


def tft_wallet_init(prefab, passphrase, recovery_seed=None):
    """
    Initialize tft wallet using the passphrase and recovery seed if provided
    If the wallet is unlocked then nothing will happen
    """

    cmd = 'curl -A "Rivine-Agent" "localhost:23110/wallet"'
    rc, out, err = prefab.core.run(cmd, die=False, showout=False)
    if rc:
        raise j.exceptions.Base("Failed to unlock tft wallet. Error {}".format(err))
    json_out = json.loads(out)
    cmd_data = '--data "passphrase={}"'
    if json_out.get("unlocked") is False and json_out.get("encrypted") is False:
        if recovery_seed:
            entropy = entropy = j.data.encryption.mnemonic.to_entropy(recovery_seed)
            cmd_data = '--data "passphrase={}&seed={}"'.format(passphrase, entropy.hex())
        else:
            cmd_data = '--data "passphrase={}"'.format(passphrase)
        cmd = 'curl -A "Rivine-Agent" {} "localhost:23110/wallet/init"'.format(cmd_data)
        rc, out, err = prefab.core.run(cmd, die=False, showout=False)
        if rc:
            raise j.exceptions.Base("Failed to initialize tft wallet. Error {}".format(err))


def check_tfchain_synced(prefab, height_threeshold=10):
    """
    Check if the tfchain daemon is synced with the offical testnet
    @param prefab: prefab of the TFT node
    @param height_threeshold: The max difference between the testnet explorer and the local node to be considered in sync
    """
    testnet_explorer = "https://explorer.testnet.threefoldtoken.com/explorer"
    res = requests.get(testnet_explorer)
    if res.status_code == 200:
        expected_height = res.json()["height"]
        _, out, err = prefab.core.run(cmd="tfchainc", showout=False)
        out = "{}\n{}".format(out, err)
        match = re.search("^Synced:\s+(?P<synced>\w+)\n*.*\n*Height:\s*(?P<height>\d+)", out)
        if match:
            match_info = match.groupdict()
            if match_info["synced"] == "Yes" and expected_height - int(match_info["height"]) <= height_threeshold:
                return True
    return False


def check_btc_synced(prefab, height_threeshold=10):
    """
    Check if the BTC node is synced with the offical testnet3
    @param prefab: prefab of the BTC node
    @param height_threeshold: The max difference between the testnet and the local node to be considered in sync
    """
    testnet_url = "https://api.blockcypher.com/v1/btc/test3"
    res = requests.get(testnet_url)
    if res.status_code == 200:
        expected_height = res.json()["height"]
        _, out, _ = prefab.core.run(cmd="bitcoin-cli -getinfo", showout=False)
        current_height = json.loads(out)["blocks"]
        if expected_height - current_height <= height_threeshold:
            return True
    return False


def start_blockchains(prefab, node_name):
    """
    Start blockchains daemons on a node
    """
    # a bit unrelated but make sure that curl is installed
    prefab.core.run("apt-get update; apt-get install -y curl", die=False, showout=False)
    print("Starting tfchaind daemon on {}".format(node_name))
    tfchaind_cmd = "tfchaind --network testnet -M gctwe"
    tfchaind_cmd_check = 'ps fax | grep "{}" | grep -v grep'.format(tfchaind_cmd)
    rc, _, _ = prefab.core.run(cmd=tfchaind_cmd_check, die=False, showout=False)
    if rc:
        prefab.core.run("cd {}; {} >/dev/null 2>&1 &".format(DEFAULT_DATA_PATH, tfchaind_cmd), showout=False)

    # start bitcoind
    print("Starting btcoind daemon on {}".format(node_name))
    prefab.core.dir_ensure(DEFAULT_BITCOIN_DIR)
    prefab.core.file_write(location=DEFAULT_BITCOIN_CONFIG_PATH, content=DEFAULT_BITCOIN_CONFIG)
    btc_cmd = "bitcoind -daemon"
    btc_cmd_check = 'ps fax | grep "{}" | grep -v grep'.format(btc_cmd)
    rc, _, _ = prefab.core.run(cmd=btc_cmd_check, die=False, showout=False)
    if rc:
        prefab.core.run(cmd=btc_cmd, showout=False)


def create_blockchain_zos_vms(zos_node_name="main", sshkeyname=None):
    """
    Create 2 ZOS vms each running the crypto flist that cointains the blockchains binaries

    @param zos_node_name: Name of the Zero os client instance where the vms will be created
    @param sshkeyname: Name of the sshkey to use to authorize access to the created nodes
    """
    sshkey = j.clients.sshkey.get(sshkeyname)
    zrobot_cl = j.clients.zrobot.robots[zos_node_name]
    tft_node_name = "tft_node"
    tft_node_data = {
        "flist": "https://hub.grid.tf/abdelrahman_hussein_1/ubuntucryptoexchange.flist",
        "memory": 1024 * 14,
        "cpu": 2,
        "nics": [{"type": "default", "name": "nic01"}],
        "ports": [{"name": "ssh", "source": 2250, "target": 22}],
        "configs": [{"path": "/root/.ssh/authorized_keys", "content": sshkey.pubkey, "name": "sshauthorizedkeys"}],
    }
    data_disk = {
        "size": 100,
        "mountPoint": DEFAULT_DATA_PATH,
        "diskType": "ssd",
        "filesystem": "btrfs",
        "label": "data",
    }
    print("Creating TFT data disk service")
    disk_srv = zrobot_cl.services.find_or_create(
        "github.com/zero-os/0-templates/vdisk/0.0.1", "tft_data_disk", data_disk
    )
    disk_srv.schedule_action("install").wait(die=True)
    disk_url = disk_srv.schedule_action("private_url").wait(die=True).result
    # disk_info = disk_srv.schedule_action('info').wait(die=True).result
    # data_disk['name'] = disk_info['name']
    data_disk["url"] = disk_url
    data_disk["name"] = disk_srv.name

    tft_node_data["disks"] = [data_disk]

    print("Creating TFT node vm")
    tft_node_srv = zrobot_cl.services.find_or_create(
        "github.com/zero-os/0-templates/vm/0.0.1", tft_node_name, tft_node_data
    )
    task = tft_node_srv.schedule_action("install")
    try:
        task.wait(die=True)
    except Exception as ex:
        raise j.exceptions.Base(f"Failed to create a VM for TFT. Error: {ex}")

    timeout = 5 * 60
    tft_node_prefab = None
    while timeout > 0:
        try:
            tft_node_prefab = j.tools.prefab.getFromSSH(addr=zos_node_name, port=tft_node_data["ports"][0]["source"])
            break
        except (ConnectionErrorException, SessionError) as ex:
            print("Error while connectin to TFT node: {}".format(ex))
            j.clients.sshkey.key_load(sshkey.path)
            time.sleep(30)
            timeout -= 30

    if tft_node_prefab is None:
        raise j.exceptions.Base(
            "Failed to establish a connection to {} port: {}".format(zos_node_name, tft_node_data["ports"][0]["source"])
        )

    # add /opt/bin to the path
    tft_node_prefab.core.run('echo "export PATH=/opt/bin:$PATH" >> /root/.profile_js', profile=False, showout=False)

    start_blockchains(tft_node_prefab, tft_node_name)
    print("Initializing TFT wallet")
    passphrase = os.environ.get("TFT_WALLET_PASSPHRASE", DEFAULT_TFT_WALLET_PASSPHRASE)
    recovery_seed = os.environ.get("TFT_WALLET_RECOVERY_SEED")
    tft_wallet_init(prefab=tft_node_prefab, passphrase=passphrase, recovery_seed=recovery_seed)
    print("Unlocking TFT wallet")
    tft_wallet_unlock(prefab=tft_node_prefab, passphrase=passphrase)

    btc_node_name = "btc_node"

    btc_node_data = {
        "flist": "https://hub.grid.tf/abdelrahman_hussein_1/ubuntucryptoexchange.flist",
        "memory": 1024 * 14,
        "cpu": 2,
        "nics": [{"type": "default", "name": "nic01"}],
        "ports": [{"name": "ssh", "source": 2350, "target": 22}],
        "configs": [{"path": "/root/.ssh/authorized_keys", "content": sshkey.pubkey, "name": "sshauthorizedkeys"}],
    }
    data_disk = {
        "size": 100,
        "mountPoint": DEFAULT_DATA_PATH,
        "diskType": "ssd",
        "filesystem": "btrfs",
        "label": "data",
    }
    print("Creating BTC data disk service")
    disk_srv = zrobot_cl.services.find_or_create(
        "github.com/zero-os/0-templates/vdisk/0.0.1", "btc_data_disk", data_disk
    )
    disk_srv.schedule_action("install").wait(die=True)
    disk_url = disk_srv.schedule_action("private_url").wait(die=True).result
    disk_info = disk_srv.schedule_action("info").wait(die=True).result
    data_disk["url"] = disk_url
    data_disk["name"] = disk_srv.name

    btc_node_data["disks"] = [data_disk]

    print("Creating BTC node vm")
    btc_node_srv = zrobot_cl.services.find_or_create(
        "github.com/zero-os/0-templates/vm/0.0.1", btc_node_name, btc_node_data
    )
    task = btc_node_srv.schedule_action("install")
    task.wait()
    if task.state != "ok":
        raise j.exceptions.Base("Failed to create a VM for BTC")

    timeout = 5 * 60
    btc_node_prefab = None
    while timeout > 0:
        try:
            btc_node_prefab = j.tools.prefab.getFromSSH(addr=zos_node_name, port=btc_node_data["ports"][0]["source"])
            break
        except (ConnectionErrorException, SessionError) as ex:
            j.clients.sshkey.key_load(sshkey.path)
            time.sleep(30)
            timeout -= 30

    if btc_node_prefab is None:
        raise j.exceptions.Base(
            "Failed to establish a connection to {} port: {}".format(zos_node_name, btc_node_data["ports"][0]["source"])
        )

    # add /opt/bin to the path
    btc_node_prefab.core.run('echo "export PATH=/opt/bin:$PATH" >> /root/.profile_js', profile=False, showout=False)

    start_blockchains(btc_node_prefab, btc_node_name)

    print("Wait until TFT node is synced")
    while True:
        if check_tfchain_synced(tft_node_prefab):
            break
        time.sleep(20)

    print("Wait until BTC node is synced")
    while True:
        if check_btc_synced(btc_node_prefab):
            break
        time.sleep(20)


# def create_packet_machines(sshkeyname=None):
#     """
#     This will create 4 nodes each running all the blockchains
#
#     @param sshkeyname: Name of the sshkey to use to authorize access to the created nodes
#
#     @returns: A dictionary with in the form {"btc": <prefab_obj>, "tft": <prefab_obj>, "eth": <prefab_obj>, "xrp": <prefab_obj>}
#     """
#     packet_cl = j.clients.packetnet.get()
#     sshkeyname = sshkeyname or (j.clients.sshkey._children_names_get()[0] if j.clients.sshkey._children_names_get() else DEFAULT_SSHKEY_NAME)
#     print("Creating packet machine for Bitcoin node")
#     btc_node = packet_cl.startDevice(hostname='hussein.btc', os='ubuntu_16_04', remove=False, sshkey=sshkeyname)
#     install_blockchains(prefab=btc_node.prefab)
#
#     # start bitcoind
#     btc_node.prefab.core.dir_ensure(DEFAULT_BITCOIN_DIR)
#     btc_node.prefab.core.file_write(location=DEFAULT_BITCOIN_CONFIG_PATH,
#                                     content=DEFAULT_BITCOIN_CONFIG)
#
#     start_blockchains(prefab=btc_node.prefab, node_name='hussein.btc')
#
#     print("Creating packet machine for TFTChain node")
#     tft_node = packet_cl.startDevice(hostname='hussein.tft', os='ubuntu_16_04', remove=False, sshkey=sshkeyname)
#     install_blockchains(prefab=tft_node.prefab)
#
#     start_blockchains(prefab=tft_node.prefab, node_name='hussein.tft')
#
#     return {
#     'btc': btc_node.prefab,
#     'tft': tft_node.prefab,
#     'eth': None,
#     'xrp': None,
#     }
#
#
# def install_blockchains(prefab):
#     """
#     Install TFT, BTC, ETH and XRP blockchains
#     """
#     print("Installing blockchains")
#     prefab.system.base.install(upgrade=True)
#     prefab.blockchain.tfchain.build()
#     prefab.blockchain.tfchain.install()
#     prefab.blockchain.bitcoin.build()
#     prefab.blockchain.bitcoin.install()
#     prefab.blockchain.atomicswap.build()
#     prefab.blockchain.atomicswap.install()
#     # prefab.blockchain.ethereum.install()


def create_packet_zos(
    sshkeyname=None, zt_netid="", zt_client_instance="main", packet_client_instance="main", hostname="atomicswap.test"
):
    """
    Creates a zos node on packet.net

    @param sshkeyname: Name of the sshkey to use to authorize access to the created node
    @param zt_netid: Zerotier network id
    @param zt_client_instance: Name of the zerotier client instance
    """
    zt_api_token = j.clients.zerotier.get(zt_client_instance).config.data["token_"]
    packet_cl = j.clients.packetnet.get(packet_client_instance)
    sshkeyname = sshkeyname or (
        j.clients.sshkey._children_names_get()[0] if j.clients.sshkey._children_names_get() else DEFAULT_SSHKEY_NAME
    )
    zos_packet_cl, packet_node, ipaddr = packet_cl.startZeroOS(
        hostname=hostname,
        zerotierId=zt_netid,
        plan="baremetal_1",
        zerotierAPI=zt_api_token,
        branch="development",
        params=["development", "console=ttyS1,115200"],
    )
    zos_node_name = ipaddr
    zrobot_data = {"url": "http://{}:6600".format(zos_node_name)}
    # the get call to create the client instance and then we get a more usefull robot instance
    zrobot_cl = j.clients.zrobot.get(zos_node_name, data=zrobot_data)
    zrobot_cl = j.clients.zrobot.robots[zos_node_name]
    # wait for 0-node reobot to be reachable services can be listed
    timeout = 5 * 60
    print("Waiting for 0-node robot to be ready")
    while timeout > 0:
        try:
            zrobot_cl.services.names
        except Exception:
            timeout -= 30
            time.sleep(30)
        else:
            break

    if not timeout:
        raise j.exceptions.Base("Z-node robot is not accessible")

    try:
        create_blockchain_zos_vms(zos_node_name=zos_node_name, sshkeyname=sshkeyname)
    except Exception:
        import IPython

        IPython.embed()
    return zos_node_name


def main():
    """
    Deploys the blockchains
    """
    print("Preparing blockchains environments")
    if not j.clients.sshkey.sshagent_available():
        j.clients.sshkey.sshagent_start()
    zt_netid_envvar = "ZT_NET_ID"
    zt_netid = os.environ.get(zt_netid_envvar)
    if zt_netid is None:
        raise j.exceptions.Base("Environtment variable {} is not set".format(zt_netid_envvar))
    sshkeyname = os.environ.get("SSHKEY_NAME")
    zt_client_instance = os.environ.get("ZT_CLIENT_INSTANCE", "main")
    packet_client_instance = os.environ.get("PACKET_CLIENT_INSTANCE", "main")
    zos_node_hostname = os.environ.get("ZOS_NODE_NAME", "atomicswap.test")
    zos_node_name = create_packet_zos(
        zt_netid=zt_netid,
        sshkeyname=sshkeyname,
        zt_client_instance=zt_client_instance,
        packet_client_instance=packet_client_instance,
        hostname=zos_node_hostname,
    )

    print("ZOS node ip address is: {}".format(zos_node_name))


if __name__ == "__main__":
    main()
    # import IPython
    # IPython.embed()
