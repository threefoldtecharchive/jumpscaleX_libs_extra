from Jumpscale import j
from ..abstracts import Collection, Nics
from ..utils import authorize_zerotiers
import requests

IPXEURL = "https://bootstrap.grid.tf/ipxe/master/0"


PUBLIC_THREEFOLD_NETWORK = "9bee8941b5717835"


class Disk:
    def __init__(self, name, url, mountpoint=None, filesystem=None, label=None):
        self.name = name
        self.url = url
        self.type = "disk"
        self.mountpoint = mountpoint
        self.filesystem = filesystem
        self.label = label or name

    def __str__(self):
        return "Disk <{}:{}>".format(self.name, self.url)

    __repr__ = __str__


class ZDBDisk(Disk):
    def __init__(self, zdb, name, mountpoint=None, filesystem="ext4", size=10, label=None):
        if zdb.mode == "direct":
            raise j.exceptions.Base("ZDB mode direct not support for disks")
        super().__init__(name, None, mountpoint, filesystem, label)
        self.zdb = zdb
        self.size = size
        self.node = None

    @property
    def url(self):
        if self.node is None:
            raise j.exceptions.Base("Can not get url when node is not set")
        else:
            if self.node == self.zdb.node:
                return self.private_url
            else:
                return self.public_url

    @url.setter
    def url(self, value):
        return

    def deploy(self):
        """
        Deploy disk

        Will create zdb namespace with specified limits and create filesystem (if specified) on the disk
        """
        if self.name in self.zdb.namespaces:
            namespace = self.zdb.namespaces[self.name]
            if namespace.size != self.size:
                raise j.exceptions.Value("namespace with name {} already exists".format(self.name))
        else:
            namespace = self.zdb.namespaces.add(self.name, self.size)

        self.zdb.deploy()
        self.public_url = namespace.url
        self.private_url = namespace.private_url
        if self.filesystem:
            tmpfile = "/var/cache/{}".format(j.data.idgenerator.generateGUID())
            try:
                res = self.zdb.node.client.system("truncate -s {}G {}".format(self.size, tmpfile)).get()
                if res.state != "SUCCESS":
                    raise j.exceptions.Base("Failed to create tmpfile")
                res = self.zdb.node.client.system("mkfs.{} -L {} {}".format(self.filesystem, self.label, tmpfile)).get()
                if res.state != "SUCCESS":
                    raise j.exceptions.Base("Failed to create fs")
                self.zdb.node.client.kvm.convert_image(tmpfile, self.private_url, "raw")
            finally:
                self.zdb.node.client.filesystem.remove(tmpfile)

    def __str__(self):
        return "ZDBDisk <{}:{}>".format(self.name, self.url)

    __repr__ = __str__


class Disks(Collection):
    def add(self, name_or_disk, url=None, mountpoint=None, filesystem=None, label=None):
        """
        Add disk to vm

        :param name_or_disk: name to give to disk or ZDBDisk instance
        :type name: str
        :param url: Disk url example: nbd://myip:port
        :type url: str
        :param mounpoint: Optional location to mount this disk on the vm
                          Only works in combination with filesystem
        :type mountpoint: str
        :param filesystem: Filesystem the disk contains
        :type filesystem: str
        :param label: label to use for disk
        :type label: str

        """
        if isinstance(name_or_disk, str):
            if url is None:
                raise j.exceptions.Value("Url is mandatory when disk name is given")
            super().add(name_or_disk)
            disk = Disk(name_or_disk, url, mountpoint, filesystem, label)
        elif isinstance(name_or_disk, ZDBDisk):
            super().add(name_or_disk.name)
            disk = name_or_disk
            disk.node = self._parent.node
        else:
            raise j.exceptions.Value("Unsupported type {}".format(name_or_disk))

        self._items.append(disk)
        return disk

    def get_by_url(self, url):
        for disk in self:
            if disk.url == url:
                return disk
        raise j.exceptions.NotFound("No disk found with url {}".format(url))


class Port:
    def __init__(self, name, source, target):
        self.name = name
        self.source = source
        self.target = target

    def __str__(self):
        return "Port <{}:{}:{}>".format(self.name, self.source, self.target)

    __repr__ = __str__


class Ports(Collection):
    def add(self, name, source, target):
        """
        Add portforward

        This is only valid incase your vm connects to te default nic

        :param name: Name for the port
        :type name: str
        :param source: Source port (port on host)
        :type source: int
        :param target: Target port (port on vm)
        :type target: int
        """
        super().add(name)
        for nic in self._parent.nics:
            if nic.type == "default":
                break
        else:
            raise j.exceptions.Value("Can not add ports when no default nic is added")
        port = Port(name, source, target)
        self._items.append(port)
        return port


class MountBind:
    def __init__(self, name, sourcepath, targetpath):
        self.name = name
        self.sourcepath = sourcepath
        self.targetpath = targetpath

    def __str__(self):
        return "MountBind <{}:{}:{}>".format(self.name, self.sourcepath, self.targetpath)

    __repr__ = __str__


class Mounts(Collection):
    def add(self, name, sourcepath, targetpath):
        """
        Add mount

        Target is only mounted when vm is created from flist otherwise one will need to mount
        the bind manually

        :param name: Name for the mount
        :type name: str
        :param sourcepath: Source path (path on host)
        :type sourcepath: str
        :param targetpath: Target, tag to used to mount plan9 fs inside vm
        :type targetpath: str
        """
        super().add(name)
        if name == "root" or " " in name:
            raise j.exceptions.Value("Name can not be 'root' and can not contain spaces")
        mount = MountBind(name, sourcepath, targetpath)
        self._items.append(mount)
        return mount


class Config:
    def __init__(self, name, path, content):
        self.name = name
        self.path = path
        self.content = content

    def __str__(self):
        return "Config <{}:{}>".format(self.name, self.path)

    __repr__ = __str__


class Configs(Collection):
    def add(self, name, path, content):
        """
        Add (config) files to rootfs


        :param name: Name for the config
        :type name: str
        :param path: Path under the rootfs of the guest
        :type pat: str
        :param content: Content of the config file
        :type content: str
        """
        super().add(name)
        if not self._parent.flist:
            raise j.exceptions.Value("Config is only supported when booting from flist")
        config = Config(name, path, content)
        self._items.append(config)
        return config


class KernelArg:
    def __init__(self, name, key, value=""):
        self.name = name
        self.key = key
        self.value = value

    def parameter(self):
        return "=".join([self.key, self.value]) if self.value else self.key

    def __str__(self):
        return "Kernel Argument <{}:{}>".format(self.name, self.parameter())

    __repr__ = __str__


class KernelArgs(Collection):
    def add(self, name, key, value=""):
        """
        Add kernel cmdline arguments

        :param name: Name for the kernel argument
        :type name: str
        :param key: left side of the kernel argument
        :type key: str
        :param value: right side of the kernel argument
        :type value: str
        """
        super().add(name)
        kernel_arg = KernelArg(name, key, value)
        self._items.append(kernel_arg)
        return kernel_arg


class VMNics(Nics):
    def add(self, name, type_, networkid=None, hwaddr=None):
        """
        Add nic to VM

        :param name: name to give to the nic
        :type name: str
        :param type_: Nic type vlan, vxlan, zerotier, bridge or default
        :type type_: str
        :param hwaddr: Hardware address of the NIC (MAC)
        :param hwaddr: str
        """
        if not self._parent.loading and self._parent.is_running() and type_ == "zerotier":
            raise j.exceptions.Base("Zerotier can not be added when the VM is running")
        return super().add(name, type_, networkid, hwaddr)

    def add_zerotier(self, network, name=None):
        """
        Add zerotier by zerotier network.

        :param network: Zerotier network instance (part of zerotierclient)
        :type network: Jumpscale.clients.zerotier.ZerotierClient.ZeroTierNetwork
        :param name: Name for the nic if left blank will be the name of the network
        :type name: str
        """
        if not self._parent.loading and self._parent.is_running():
            raise j.exceptions.Base("Zerotier can not be added when the VM is running")
        return super().add_zerotier(network, name)


class VMNotRunningError(RuntimeError):
    pass


class ZOS_VM:
    def __init__(self, node, name, flist=None, vcpus=2, memory=2048, kvm=False):
        self.node = node
        self._name = name
        self._memory = memory
        self._vcpus = vcpus
        self._flist = flist
        self._kvm = kvm
        self.loading = False
        self.disks = Disks(self)
        self.nics = VMNics(self)
        self.ports = Ports(self)
        self.mounts = Mounts(self)
        self.configs = Configs(self)
        self.kernel_args = KernelArgs(self)
        self.zt_identity = None
        self.tags = []

    def is_running(self):
        return bool(self.info)

    def drop_ports(self):
        for port in self.ports:
            self.node.client.nft.drop_port(port.source)

    @property
    def info(self):
        try:
            return self.node.client.kvm.get(name=self.name)
        except:
            return None

    @property
    def uuid(self):
        info = self.info
        if info:
            return info["uuid"]
        raise VMNotRunningError("VM is not running")

    def destroy(self):
        try:
            j.tools.logger._log_info("Destroying kvm with uuid %s" % self.uuid)
            self.node.client.kvm.destroy(self.uuid)
        except VMNotRunningError:
            # destroying something that doesn't exists is a noop
            pass
        self.drop_ports()

    def shutdown(self):
        j.tools.logger._log_info("Shuting down kvm with uuid %s" % self.uuid)
        self.node.client.kvm.shutdown(self.uuid)
        self.drop_ports()

    def pause(self):
        j.tools.logger._log_info("Pausing kvm with uuid %s" % self.uuid)
        self.node.client.kvm.pause(self.uuid)

    def reboot(self):
        j.tools.logger._log_info("Rebooting kvm with uuid %s" % self.uuid)
        self.node.client.kvm.reboot(self.uuid)

    def reset(self):
        j.tools.logger._log_info("Reseting kvm with uuid %s" % self.uuid)
        self.node.client.kvm.reset(self.uuid)

    def resume(self):
        j.tools.logger._log_info("Resuming kvm with uuid %s" % self.uuid)
        self.node.client.kvm.resume(self.uuid)

    def _get_zt_unit(self, networkid):
        return """\
[Unit]
Description=ZT Network Join
After=zerotier-one.service

[Service]
ExecStart=/usr/sbin/zerotier-cli join {}
RestartSec=5
Restart=on-failure
Type=simple
""".format(
            networkid
        )

    def start(self):
        media = []
        nics = []
        ports = {}
        mounts = []
        config = {}
        fstab = []
        haszerotier = False
        public_threefold_nic = False
        if not self.zt_identity:
            self.zt_identity = self.node.generate_zerotier_identity()
        publiczt = self.node.client.system("zerotier-idtool getpublic {}".format(self.zt_identity)).get().stdout.strip()
        for nic in self.nics:
            if nic.type == "zerotier":
                if nic.networkid == PUBLIC_THREEFOLD_NETWORK:
                    public_threefold_nic = True
                haszerotier = True
                config[
                    "/etc/systemd/system/multi-user.target.wants/zt-{}.service".format(nic.networkid)
                ] = self._get_zt_unit(nic.networkid)
                continue
            nics.append(nic.to_dict(True))
        if not public_threefold_nic:
            config[
                "/etc/systemd/system/multi-user.target.wants/zt-{}.service".format(PUBLIC_THREEFOLD_NETWORK)
            ] = self._get_zt_unit(PUBLIC_THREEFOLD_NETWORK)
        for port in self.ports:
            self.node.client.nft.open_port(port.source)
            ports[port.source] = port.target
        for configobj in self.configs:
            config[configobj.path] = configobj.content
        for disk in self.disks:
            if disk.mountpoint and disk.filesystem:
                fstab.append("LABEL={} {} {} defaults 0 0".format(disk.label, disk.mountpoint, disk.filesystem))
            media.append({"url": disk.url, "type": disk.type})
        for mount in self.mounts:
            mounts.append({"source": mount.sourcepath, "target": mount.name})
            fstab.append("{} {} 9p rw,cache=loose,trans=virtio 0 0".format(mount.name, mount.targetpath))
        if fstab:
            fstab.insert(0, "root / 9p rw,cache=loose,trans=virtio 0 0")
            fstab.append("")
            config["/etc/fstab"] = "\n".join(fstab)
        if haszerotier:
            config["/var/lib/zerotier-one/identity.secret"] = self.zt_identity
            config["/var/lib/zerotier-one/identity.public"] = publiczt
            if not nics:
                nics.append({"type": "default"})
            authorize_zerotiers(publiczt, self.nics)
        cmdline = " ".join([arg.parameter() for arg in self.kernel_args])
        self.node.client.kvm.create(
            self.name,
            media,
            self.flist,
            self.vcpus,
            self.memory,
            nics,
            ports,
            mounts,
            self.tags,
            config,
            cmdline=cmdline,
            share_cache=share_cache_enabled(self._flist),
            kvm=self.kvm,
        )

    def load_from_reality(self):
        info = self.info
        if not info:
            raise j.exceptions.Base("Can not load halted vm")
        self.loading = False
        self.disks = Disks(self)
        self.nics = VMNics(self)
        self.ports = Ports(self)
        self.mounts = Mounts(self)
        self.configs = Configs(self)
        self.kernel_args = KernelArgs(self)
        self.tags = info["params"]["tags"]
        self._vcpus = info["params"]["cpu"]
        self._memory = info["params"]["memory"]
        self._flist = info["params"]["flist"]
        for idx, nicinfo in enumerate(info["params"]["nics"]):
            name = "nic{}".format(idx)
            self.nics.add(name, nicinfo["type"], nicinfo["id"], nicinfo["hwaddr"])
        for idx, diskinfo in enumerate(info["params"]["media"]):
            name = "disk{}".format(idx)
            self.disks.add(name, diskinfo["url"], diskinfo["type"])
        for idx, mountinfo in enumerate(info["params"]["mount"]):
            name = "mount{}".format(idx)
            self.mounts.add(name, mountinfo["source"], mountinfo["target"])
        for idx, (srcport, dstport) in enumerate(info["params"]["port"].items()):
            name = "port{}".format(idx)
            self.ports.add(name, srcport, dstport)
        for idx, (path, content) in enumerate(info["params"]["config"].items()):
            name = "config{}".format(idx)
            self.configs.add(name, path, content)
        for idx, parameter in enumerate(info["params"]["cmdline"].split(" ")):
            name = "kernelarg{}".format(idx)
            key, _, value = parameter.partition("=")
            self.kernel_args.add(name, key, value)

    def to_dict(self):
        data = {
            "name": self.name,
            "memory": self.memory,
            "cpu": self.vcpus,
            "flist": self.flist,
            "ztIdentity": self.zt_identity,
            "tags": self.tags,
            "nics": [],
            "disks": [],
            "ports": [],
            "configs": [],
            "mounts": [],
            "kernelArgs": [],
            "kvm": self.kvm,
        }
        for nic in self.nics:
            data["nics"].append(nic.to_dict())
        for disk in self.disks:
            data["disks"].append(
                {"url": disk.url, "mountPoint": disk.mountpoint, "filesystem": disk.filesystem, "type": disk.type}
            )
        for config in self.configs:
            data["configs"].append({"path": config.path, "content": config.content})
        for mount in self.mounts:
            data["mounts"].append({"sourcePath": mount.sourcepath, "targetPath": mount.targetpath, "name": mount.name})
        for port in self.ports:
            data["ports"].append({"name": port.name, "source": port.source, "target": port.target})
        for arg in self.kernel_args:
            data["kernelArgs"].append({"name": arg.name, "key": arg.key, "value": arg.value})
        return data

    def to_json(self):
        return j.data.serializers.json.dumps(self.to_dict())

    def from_dict(self, data):
        self.loading = True
        try:
            self._name = data["name"]
            self.zt_identity = data.get("ztIdentity")
            self._flist = data["flist"]
            self._vcpus = data["cpu"]
            self._memory = data["memory"]
            self._kvm = data.get("kvm", False)
            self.tags = data["tags"]
            self.disks = Disks(self)
            self.nics = VMNics(self)
            self.configs = Configs(self)
            self.kernel_args = KernelArgs(self)
            for disk in data["disks"]:
                self.disks.add(
                    disk["name"], disk["url"], disk.get("mountPoint"), disk.get("filesystem"), disk.get("label")
                )
            for nic in data["nics"]:
                nicobj = self.nics.add(nic["name"], nic["type"], nic.get("id"), nic.get("hwaddr"))
                if "ztClient" in nic:
                    nicobj.client_name = nic["ztClient"]
            for config in data["configs"]:
                self.configs.add(config["name"], config["path"], config["content"])
            for port in data["ports"]:
                self.ports.add(port["name"], port["source"], port["target"])
            for mount in data["mounts"]:
                self.mounts.add(mount["name"], mount["sourcePath"], mount["targetPath"])
            for arg in data["kernelArgs"]:
                self.kernel_args.add(arg["name"], arg["key"], arg.get("value", ""))
        finally:
            self.loading = False

    def from_json(self, data):
        data = j.data.serializers.json.loads(data)
        self.from_dict(data)

    def deploy(self):
        if not self.is_running():
            self.start()
        else:
            # search for diskchanges
            realityinfo = self.info
            self.update_disks(realityinfo)
            self.update_nics(realityinfo)

    def update_disks(self, info=None):
        if not info:
            info = self.info
        toremove = []
        wanted = list(self.disks)
        for disk in info["params"]["media"] or []:
            try:
                disk = self.disks.get_by_url(disk["url"])
                wanted.remove(disk)
            except LookupError:
                toremove.append(disk)
        for disk in toremove:
            disk = {"url": disk["url"], "type": disk["type"]}
            self.node.client.kvm.detach_disk(self.uuid, disk)
        for disk in wanted:
            self.node.client.kvm.attach_disk(self.uuid, {"url": disk.url, "type": disk.type})

    def update_nics(self, info=None):
        if not info:
            info = self.info
        toremove = []
        wanted = list(filter(lambda n: n.type != "zerotier", self.nics))
        for nic in info["params"]["nics"] or []:
            try:
                nic = self.nics.get_by_type_id(nic["type"], nic["id"])
                wanted.remove(nic)
            except LookupError:
                toremove.append(nic)
        for nic in toremove:
            self.node.client.kvm.remove_nic(self.uuid, nic["type"], nic["id"], nic["hwaddr"])
        for nic in wanted:
            self.node.client.kvm.add_nic(self.uuid, nic.type, nic.networkid, nic.hwaddr)

    @property
    def vcpus(self):
        return self._vcpus

    @vcpus.setter
    def vcpus(self, value):
        if self.is_running():
            raise j.exceptions.Base("Can not change cpu of running vm")
        self._vcpus = value

    @property
    def memory(self):
        return self._memory

    @memory.setter
    def memory(self, value):
        if self.is_running():
            raise j.exceptions.Base("Can not change memory of running vm")
        self._memory = value

    @property
    def kvm(self):
        return self._kvm

    @kvm.setter
    def kvm(self, boolean):
        if not isinstance(boolean, bool):
            raise j.exceptions.Base("Provided value need to be of type boolean")
        if self.is_running():
            raise j.exceptions.Base("Can not change kvm flag of running vm")
        self._kvm = boolean

    @property
    def flist(self):
        return self._flist

    @flist.setter
    def flist(self, value):
        if self.is_running():
            raise j.exceptions.Base("Can not change flist of running vm")
        self._flist = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if self.is_running():
            raise j.exceptions.Base("Can not change name of running vm")
        self._name = value

    def enable_vnc(self):
        port = self.info["vnc"]
        if port:
            j.tools.logger._log_info("Enabling vnc for port %s" % port)
            self.node.client.nft.open_port(port)

    def disable_vnc(self):
        port = self.info["vnc"]
        if port:
            j.tools.logger._log_info("Disabling vnc for port %s" % port)
            self.node.client.nft.drop_port(port)

    def __str__(self):
        return "{} <{}>".format(self.__class__.__name__, self.name)

    def __repr__(self):
        return str(self)


class IpxeVM(ZOS_VM):
    def __init__(self, node, name, flist=None, vcpus=2, memory=2048, ipxe_url=IPXEURL):
        super().__init__(node, name, flist, vcpus, memory)
        self.ipxe_url = ipxe_url

    def deploy(self):
        if "ipxescript" in self.configs:
            self.configs.remove("ipxescript")
        resp = requests.get(self.ipxe_url)
        resp.raise_for_status()
        self.configs.add("ipxescript", "/boot/ipxe-script", resp.content.decode("utf-8"))
        super().deploy()

    def to_dict(self):
        data = super().to_dict()
        data["ipxeUrl"] = self.ipxe_url
        return data

    def from_dict(self, data):
        super().from_dict(data)
        self.ipxe_url = data.get("ipxeUrl")


def share_cache_enabled(flist):
    valid = [
        "https://hub.grid.tf/tf-autobuilder/zero-os-master.flist",
        "https://hub.grid.tf/tf-autobuilder/zero-os-development.flist",
    ]
    return flist in valid
