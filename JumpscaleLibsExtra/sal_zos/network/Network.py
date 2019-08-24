import re
import time

import netaddr
from Jumpscale import j

OVS_FLIST = "https://hub.grid.tf/tf-autobuilder/threefoldtech-openvswitch-plugin-master.flist"


def combine(ip1, ip2, mask):
    """
    >>> combine('10.0.3.11', '192.168.1.10', 24)
    '10.0.3.10'
    """
    iip1 = netaddr.IPNetwork("{}/{}".format(ip1, mask))
    iip2 = netaddr.IPNetwork("{}/{}".format(ip2, mask))
    ires = iip1.network + int(iip2.ip & (~int(iip2.netmask)))
    net = netaddr.IPNetwork(ires)
    net.prefixlen = mask
    return net


class Network:
    def __init__(self, node):
        self.node = node

    @property
    def client(self):
        return self.node.client

    def get_management_info(self):
        def get_nic_ip(nics, name):
            for nic in nics:
                if nic["name"] == name:
                    for ip in nic["addrs"]:
                        return netaddr.IPNetwork(ip["addr"])
                    return

        defaultgwdev = self.client.bash("ip route | grep default | awk '{print $5}'").get().stdout.strip()
        nics = self.client.info.nic()
        mgmtaddr = None
        if defaultgwdev:
            ipgwdev = get_nic_ip(nics, defaultgwdev)
            if ipgwdev:
                mgmtaddr = str(ipgwdev.ip)
        if not mgmtaddr:
            mgmtaddr = self.node.addr

        return mgmtaddr

    def _ensure_ovs_container(self, name):
        try:
            container = self.node.containers.get(name)
        except LookupError:
            container = self.node.containers.create(name, OVS_FLIST, "ovs", host_network=True, privileged=True)
        return container

    def get_addresses(self, network):
        mgmtaddr = self.get_management_info()
        return {
            "storageaddr": combine(str(network.ip), mgmtaddr, network.prefixlen),
            "vxaddr": combine("10.240.0.0", mgmtaddr, network.prefixlen),
        }

    def get_free_nics(self):
        devices = []
        for device in self.client.ip.link.list():
            if device["type"] == "device":
                if device["up"] is False:
                    self.client.ip.link.up(device["name"])
                devices.append(device["name"])
        nics = list(filter(lambda nic: nic["name"] in devices, self.client.info.nic()))
        nics.sort(key=lambda nic: nic["speed"])
        availablenics = {}
        for nic in nics:
            # skip all interface that have an ipv4 address
            if any(netaddr.IPNetwork(addr["addr"]).version == 4 for addr in nic["addrs"] if "addr" in addr):
                continue
            if nic["speed"] <= 0:
                continue
            availablenics.setdefault(nic["speed"], []).append(nic["name"])
        return sorted(availablenics.items(), reverse=True)

    def reload_driver(self, driver):
        self.node.client.system("modprobe -r {}".format(driver)).get()
        devs = {link["name"] for link in self.node.client.ip.link.list()}
        self.node.client.system("modprobe {}".format(driver)).get()
        # brings linsk up
        alldevs = {link["name"] for link in self.node.client.ip.link.list()}
        driverdevs = alldevs - devs
        for link in driverdevs:
            self.node.client.ip.link.up(link)

        # wait max 10 seconds for these nics to become up (speed available)
        now = time.time()
        while time.time() - 10 < now:
            for nic in self.node.client.info.nic():
                if nic["speed"] and nic["name"] in driverdevs:
                    driverdevs.remove(nic["name"])
            if not driverdevs:
                break
            time.sleep(1)

    def restart_bond(self, ovs_container_name="ovs", bond="bond0"):
        """
        Some time the bond gets stuck, it helps restarting the bond links (down then up)
        """
        container = self.node.containers.get(ovs_container_name)
        result = container.client.system("ovs-appctl bond/show %s" % bond).get()
        if result.state != "SUCCESS":
            raise Exception(result.stderr)

        for link in re.findall("^slave ([^:]+):", result.stdout, re.M):
            container.client.ip.link.down(link)
            container.client.ip.link.up(link)

    def _unconfigure_ovs(self, ovs_container_name="ovs"):
        nicmap = {nic["name"]: nic for nic in self.node.client.info.nic()}
        if "backplane" not in nicmap:
            return

        try:
            container = self.node.containers.get(ovs_container_name)
        except LookupError:
            return

        container.client.json("ovs.bridge-del", {"bridge": "backplane"})
        container.stop()

    def _unconfigure_native(self):
        cl = self.node.client

        if "backplane" in cl.ip.bond.list():
            cl.ip.bond.delete("backplane")

    def unconfigure(self, ovs_container_name="ovs", mode="ovs"):
        if not mode or mode == "ovs":
            return self._unconfigure_ovs(ovs_container_name)
        elif mode == "native":
            return self._unconfigure_native()
        else:
            raise j.exceptions.Value("unknown mode %s" % mode)

    def configure(
        self,
        cidr,
        vlan_tag,
        ovs_container_name="ovs",
        bonded=False,
        mtu=9000,
        mode="ovs",
        interfaces=None,
        balance_mode=None,
        lacp=None,
    ):
        interfaces = self._get_interfaces(bonded=bonded, interfaces=interfaces)

        if mode == "ovs" or not mode:
            return self._configure_ovs(
                cidr=cidr,
                vlan_tag=vlan_tag,
                ovs_container_name="ovs",
                bonded=bonded,
                mtu=mtu,
                interfaces=interfaces,
                balance_mode=balance_mode,
                lacp=lacp,
            )
        elif mode == "native":
            return self._configure_native(cidr=cidr, bonded=bonded, mtu=mtu, interfaces=interfaces)
        else:
            raise j.exceptions.Value("unknown mode %s" % mode)

    def _get_free_interfaces(self, bonded=False):
        freenics = self.node.network.get_free_nics()
        if not freenics:
            raise j.exceptions.RuntimeError("Could not find available nic")

        interfaces = None
        if not bonded:
            interfaces = [freenics[0][1][0]]
        else:
            for speed, interfaces in freenics:
                if len(interfaces) >= 2:
                    interfaces = interfaces[:2]
                    break
            else:
                raise j.exceptions.RuntimeError("Could not find two equal available nics")

        return interfaces

    def _get_interfaces(self, bonded=False, interfaces=None):
        # if we don't explicitly pass the interfaces to use
        # try to autodiscover somme usable interfaces
        if not interfaces:
            interfaces = self._get_free_interfaces(bonded=bonded)
        else:
            if bonded and len(interfaces) != 2:
                raise j.exceptions.Value("should have 2 interfaces specified when using bonding")

            all_nics_names = [nic["name"] for nic in self.node.client.ip.link.list()]
            for name in interfaces:
                if name not in all_nics_names:
                    raise j.exceptions.Value("interface %s does not exist on the node" % name)

        return interfaces

    def _configure_native(self, cidr, interfaces, bonded=False, mtu=9000):
        network = netaddr.IPNetwork(cidr)
        addresses = self.get_addresses(network)

        cl = self.node.client

        used_interfaces = []
        if not bonded:
            used_interfaces.append(interfaces[0])
            cl.ip.link.mtu(interfaces[0], mtu)
            cl.ip.link.up(interfaces[0])
            cl.ip.addr.add(interfaces[0], str(addresses["storageaddr"]))
            return

        # bonded
        for interface in interfaces:
            used_interfaces = interfaces
            cl.ip.link.mtu(interface, mtu)
            cl.ip.link.up(interface)

        cl.ip.bond.add("backplane", interfaces, mtu=mtu)
        cl.ip.addr.add("backplane", str(addresses["storageaddr"]))

        # return a list of nic used by the storage network
        used_interfaces.append("backplane")
        return used_interfaces

    def _configure_ovs(
        self, cidr, vlan_tag, interfaces, ovs_container_name="ovs", bonded=False, mtu=9000, balance_mode=None, lacp=None
    ):
        if balance_mode and balance_mode not in ["tcp", "slb"]:
            raise j.exceptions.Value("balance mode can only be 'tcp' or 'slb'")

        if not balance_mode:
            balance_mode = "slb"

        container = self._ensure_ovs_container(ovs_container_name)
        if not container.is_running():
            container.start()

        network = netaddr.IPNetwork(cidr)
        addresses = self.get_addresses(network)

        cl = self.node.client

        try:
            container.client.json("ovs.bridge-add", {"bridge": "backplane"})
        except Exception as e:
            if e.message.find("bridge named backplane already exists") == -1:
                raise
            return  # bridge already exists in ovs subsystem (TODO: implement ovs.bridge-list)

        used_interfaces = []
        if not bonded:
            used_interfaces.append(interfaces[0])
            cl.ip.link.mtu(interfaces[0], mtu)
            container.client.json("ovs.port-add", {"bridge": "backplane", "port": interfaces[0], "vlan": 0})
        else:
            used_interfaces = interfaces
            for interface in interfaces:
                cl.ip.link.mtu(interface, mtu)
                cl.ip.link.up(interface)
            container.client.json(
                "ovs.bond-add",
                {
                    "bridge": "backplane",
                    "port": "bond0",
                    "links": interfaces,
                    "lacp": lacp or False,
                    "mode": "balance-%s" % balance_mode,
                    "options": {"other_config:updelay": "2000"},
                },
            )

        cl.ip.link.up("backplane")
        cl.ip.link.mtu("backplane", mtu)
        cl.ip.addr.add("backplane", str(addresses["storageaddr"]))

        # hack. We don't figure out why, but ovs is not happy if we don't
        # turn it off and on again...
        interface = interfaces[0]
        cl.ip.link.down(interface)
        time.sleep(2)
        cl.ip.link.up(interface)

        # return a list of nic used by the storage network
        used_interfaces.append("backplane")
        return used_interfaces
