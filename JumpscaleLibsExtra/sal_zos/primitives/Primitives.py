from Jumpscale import j
from ..vm.ZOS_VM import ZOS_VM, IpxeVM, ZDBDisk


BASEFLIST = "https://hub.grid.tf/tf-bootable/{}.flist"
ZEROOSFLIST = "https://hub.grid.tf/tf-autobuilder/{}.flist"


class Primitives:
    def __init__(self, node):
        self.node = node

    def create_virtual_machine(self, name, type_):
        """
        Create virtual machine

        :param name: Name of virtual machine
        :type name: str
        :param type_: Type of vm this defines the template to be used check
                      https://hub.grid.tf/tf-bootable

                      eg: ubuntu:16.04, zero-os:master
        """
        templatename, _, version = type_.partition(":")
        kwargs = {"name": name, "node": self.node}
        if templatename == "zero-os":
            version = version or "development"
            flistname = "{}-{}".format(templatename, version)
            kwargs["flist"] = ZEROOSFLIST.format(flistname)
        elif templatename == "ubuntu":
            version = version or "lts"
            flistname = "{}:{}".format(templatename, version)
            kwargs["flist"] = BASEFLIST.format(flistname)
        else:
            raise j.exceptions.Base("Invalid VM type {}".format(type_))
        return ZOS_VM(**kwargs)

    def create_disk(self, name, zdb, mountpoint=None, filesystem="ext4", size=10, label=None):
        """
        Create a disk on zdb and create filesystem

        :param name: Name of the disk/namespace in zdb
        :type name: str
        :param zdb: zerodb sal object
        :param filesystem: Filesystem to create on the disk
        :type filesystem: str
        :param size: Size of the disk in GiB
        :type size: int
        :param label: Label for the disk defaults to name
        :type label: str
        :return: Returns ZDBDisk
        :rtype: ZDBDisk
        """
        return ZDBDisk(zdb, name, mountpoint, filesystem, size, label)

    def create_gateway(self, name):
        """
        Create gateway object

        To deploy gatewy invoke .deploy method

        :param name: Name of the gateway
        :type name: str
        :return: Gateway object
        :rtype: Gateway object
        """
        return self.node.gateways.get(name)

    def drop_gateway(self, name):
        """
        Drop/delete a gateway

        :param name: Name of the gateway
        :type name: str
        """
        self.node.gateways.get(name).stop()

    def drop_virtual_machine(self, name):
        """
        Drop/delete a virtual machine

        :param name: Name of the vm
        :type name: str
        """
        self.node.hypervisor.get(name).destroy()

    def create_zerodb(self, name, node_port, path=None, mode="user", sync=False, admin=""):
        """
        Create zerodb object

        To deploy zerodb invoke .deploy method

        :param name: Name of the zerodb
        :type name: str
        :param node_port: public port on the node that is forwarded to the zerodb listening port in the container
        :type node_port: int
        :param path: path zerodb stores data on
        :type path: str
        :param mode: zerodb running mode
        :type mode: str
        :param sync: zerodb sync
        :type sync: bool
        :param admin: zerodb admin password
        :type admin: str

        :return: Zerodb object
        :rtype: Zerodb object
        """
        return self.node.zerodbs.create(name=name, node_port=node_port, path=path, mode=mode, sync=sync, admin=admin)

    def drop_zerodb(self, name):
        """
        Drop/delete a zerodb

        :param name: Name of the zerodb
        :type name: str
        """
        self.node.zerodbs.get(name).stop()

    def from_json(self, type_, json):
        """
        Load primitive from json string

        :param type_: Type of primitive
        :type type_: str
        :param json: json string
        :type json: str
        :return: primitive object
        :rtype: mixed
        """
        data = j.data.serializer.json.loads(json)
        return self.from_dict(type_, data)

    def from_dict(self, type_, data):
        """
        Load primitive from data dict

        :param type_: Type of primitive
        :type type_: str
        :param data: dict object
        :type data: dict
        :return: primitive object
        :rtype: mixed
        """
        if type_ == "gateway":
            gw = self.create_gateway(data["hostname"])
            gw.from_dict(data)
            return gw
        elif type_ == "vm":
            if data.get("ipxeUrl"):
                vm = IpxeVM(self.node, data["name"])
            else:
                vm = ZOS_VM(self.node, data["name"])
            vm.from_dict(data)
            return vm
        elif type_ == "zerodb":
            zdb = self.create_zerodb(data["name"], node_port=None)
            zdb.from_dict(data)
            return zdb
        raise j.exceptions.Base("Unkown type {}, supported types are gateway, vm and zerodb".format(type_))
