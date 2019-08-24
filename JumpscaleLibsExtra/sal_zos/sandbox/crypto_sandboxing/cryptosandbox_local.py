import json
import os

from jose.jwt import get_unverified_claims
from Jumpscale import j


def get_prefab_prepared():
    # TODO: for now build on the local machine.
    return j.tools.local.prefab


iyo_client = j.clients.itsyouonline.get()
claims = get_unverified_claims(iyo_client.jwt)
username = claims.get("username", None)


def do_pkgsandbox_and_push(prefabpkg, flistname="cryptosandbox", bins=None):
    prefab = prefabpkg.prefab
    DATA_DIR = "/tmp/pkgsandbox"
    prefab.core.dir_remove(DATA_DIR)
    if prefabpkg.NAME == "tfchain":
        prefabpkg.build(tag=os.environ.get("{}_TAG".format(prefabpkg.NAME.upper())), reset=True)
        prefabpkg.install(tag=os.environ.get("{}_TAG".format(prefabpkg.NAME.upper())), reset=True)
    else:
        prefabpkg.build()
        prefabpkg.install()

    for b in bins:
        j.tools.sandboxer.sandbox_chroot(b, DATA_DIR)

    prefab.core.execute_bash("cd {} && tar -czf /tmp/{}.tar.gz .".format(DATA_DIR, flistname))
    prefab.core.execute_bash(
        """curl -b 'caddyoauth={}' -F file=@/tmp/{}.tar.gz https://hub.grid.tf/api/flist/me/upload""".format(
            iyo_client.jwt, flistname
        )
    )
    prefab.core.execute_bash(
        """curl -b 'caddyoauth={}' -F file=@/tmp/{}.tar.gz http://192.168.20.132:8080/api/flist/me/upload""".format(
            iyo_client.jwt, flistname
        )
    )
    return "{}/{}.flist".format(username, flistname)


def merge(client, target, sources):
    url = "{}/flist/me/merge/{}".format(client.api.base_url, target)
    resp = client.api.post(
        uri=url, data=json.dumps(sources), headers=None, params=None, content_type="application/json"
    )
    if resp.status_code != 200:
        raise j.exceptions.Base("Failed to merge flists {}".format(sources))
    return "{}/{}".format(username, target)


if __name__ == "__main__":
    try:
        prefab = j.tools.prefab.local
        bitcoinbins = ["/opt/bin/bitcoind", "/opt/bin/bitcoin-cli", "/opt/bin/bitcoin-tx"]
        tfchainbins = ["/opt/bin/tfchaind", "/opt/bin/tfchainc"]
        ethbins = ["/opt/bin/geth"]
        atomicswapbins = ["/opt/bin/btcatomicswap"]
        electrumbins = ["/opt/bin/electrum"]

        btcflist = do_pkgsandbox_and_push(prefab.blockchain.bitcoin, flistname="bitcoinflist", bins=bitcoinbins)
        tfchainflist = do_pkgsandbox_and_push(prefab.blockchain.tfchain, flistname="tfchainflist", bins=tfchainbins)
        ethereumflist = do_pkgsandbox_and_push(prefab.blockchain.ethereum, flistname="ethereumflist", bins=ethbins)
        atomicswapflist = do_pkgsandbox_and_push(
            prefab.blockchain.atomicswap, flistname="atomicswapflist", bins=atomicswapbins
        )
        cryptosources = [btcflist, tfchainflist, ethereumflist, atomicswapflist]

        cryptosandboxtarget = "cryptosandbox.flist"

        zhub_data = {"token_": iyo_client.jwt_get(), "username": username, "url": "https://hub.grid.tf/api"}
        zhub_client = j.clients.zhub.get(instance="mainbe", data=zhub_data)
        if hasattr(zhub_client, "authentificate"):
            zhub_client.authentificate()
        else:
            zhub_client.authenticate()

        cryptoflist = merge(zhub_client, cryptosandboxtarget, cryptosources)
        ubuntucryptotarget = "ubuntucrypto.flist"
        # can't use cryptoflist as source here because
        ubuntucryptosources = [btcflist, tfchainflist, ethereumflist, atomicswapflist, "gig-bootable/ubuntu:lts.flist"]

        ubuntucryptoflist = merge(zhub_client, ubuntucryptotarget, ubuntucryptosources)

        print("https://hub.grid.tf/{}".format(ubuntucryptoflist))

        # try to do localhub
        zhub_dataeg = {"token_": iyo_client.jwt_get(), "username": username, "url": "http://192.168.20.132:8080/api"}
        zhub_clienteg = j.clients.zhub.get(instance="maineg", data=zhub_dataeg)
        if hasattr(zhub_client, "authentificate"):
            zhub_client.authentificate()
        else:
            zhub_client.authenticate()

        # merge(zhub_clienteg, cryptosandboxtarget, cryptosources)
        merge(zhub_clienteg, ubuntucryptotarget, ubuntucryptosources)
    except Exception:
        import IPython

        IPython.embed()
