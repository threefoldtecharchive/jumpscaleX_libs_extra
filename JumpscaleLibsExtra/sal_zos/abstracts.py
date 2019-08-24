from Jumpscale import j
from JumpscaleLibsExtra.sal_zos.utils import authorize_zerotiers


class Mountable:
    """
    Abstract implementation for devices that are mountable.
    Device should have attributes devicename and mountpoint
    """

    def mount(self, target, options=["defaults"]):
        """
        @param target: Mount point
        @param options: Optional mount options
        """
        if self.mountpoint == target:
            return

        self.client.bash("mkdir -p {}".format(target))

        self.client.disk.mount(source=self.devicename, target=target, options=options)

        self.mountpoint = target

    def umount(self):
        """
        Unmount disk
        """
        _mount = self.mountpoint
        if _mount:
            self.client.disk.umount(source=_mount)
            self.client.bash("rm -rf %s" % _mount).get()
        self.mountpoint = None


class Collection:
    def __init__(self, parent):
        self._parent = parent
        self._items = []

    def __iter__(self):
        for item in self._items:
            yield item

    def __getitem__(self, name):
        if isinstance(name, int):
            return self._items[name]
        for item in self._items:
            if item.name == name:
                return item
        raise j.exceptions.NotFound("Name {} does not exists".format(name))

    def __contains__(self, name):
        try:
            self[name]
            return True
        except KeyError:
            return False

    def add(self, name, *args, **kwargs):
        if name in self:
            raise j.exceptions.Value("Element with name {} already exists".format(name))

    def remove(self, item):
        """
        Remove item from collection

        :param item: Item can be the index, the name or the object itself to remove
        :type item: mixed
        """
        if isinstance(item, (str, int)):
            item = self[item]
        self._items.remove(item)

    def list(self):
        return list(self)

    def __str__(self):
        return str(self._items)

    __repr__ = __str__


class Nic:
    def __init__(self, name, type_, networkid, hwaddr, parent):
        self._type = None
        self.name = name
        self.networkid = networkid
        self.type = type_
        self.hwaddr = hwaddr
        self._parent = parent

    def __str__(self):
        return "{} <{}:{}:{}>".format(self.__class__.__name__, self.name, self.type, self.networkid)

    @property
    def type(self):
        return self._type

    @property
    def iface(self):
        return self.name

    @type.setter
    def type(self, value):
        if value not in ["vxlan", "vlan", "bridge", "default", "zerotier", "passthrough"]:
            raise j.exceptions.Value("Invalid nic type {}".format(value))
        self._type = value

    def to_dict(self, forvm=False, forcontainer=False):
        nicinfo = {"id": str(self.networkid), "type": self.type, "name": self.name}
        if forvm:
            nicinfo.pop("name")
        if self.hwaddr:
            nicinfo["hwaddr"] = self.hwaddr
        return nicinfo

    __repr__ = __str__


class ZTNic(Nic):
    def __init__(self, name, networkid, hwaddr, parent):
        super().__init__(name, "zerotier", networkid, hwaddr, parent)
        self._client = None
        self._client_name = None

    @property
    def client(self):
        if self._client is None and j.clients.zerotier.exists(self._client_name):
            self._client = j.clients.zerotier.get(self._client_name, create=False, die=True, interactive=False)
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def client_name(self):
        return self._client_name

    @client_name.setter
    def client_name(self, value):
        if value:
            self._client_name = value

        if not j.clients.zerotier.exists(self._client_name):
            return

        self._client_name = value
        self.client = j.clients.zerotier.get(value)

    def authorize(self, publicidentity):
        """
        Authorize zerotier network
        """
        if not self.client:
            return False
        j.tools.logger._log_info("authorizing {} on network {}".format(self._parent.name, self.networkid))
        network = self.client.network_get(self.networkid)
        network.member_add(publicidentity, self._parent.name)
        return True

    @property
    def iface(self):
        for network in self._parent.container.client.zerotier.list():
            if network["nwid"] == self.networkid:
                return network["portDeviceName"]
        raise j.exceptions.Base("Could not find devicename")

    def to_dict(self, forvm=False, forcontainer=False):
        data = super().to_dict(forvm, forcontainer)
        if forcontainer:
            return data

        if self.client:
            data["ztClient"] = self.client.config.instance
        elif self._client_name:
            data["ztClient"] = self._client_name
        return data


class Nics(Collection):
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
        super().add(name)
        if len(name) > 15 or name == "default":
            raise j.exceptions.Value("Invalid network name {} should be max 15 chars and not be 'default'".format(name))
        if networkid is None and type_ != "default":
            raise j.exceptions.Value("Missing required argument networkid for type {}".format(type_))
        if type_ == "zerotier":
            nic = ZTNic(name, networkid, hwaddr, self._parent)
        else:
            nic = Nic(name, type_, networkid, hwaddr, self._parent)
        self._items.append(nic)
        return nic

    def add_zerotier(self, network, name=None):
        """
        Add zerotier by zerotier network

        :param network: Zerotier network instance (part of zerotierclient)
        :type network: Jumpscale.clients.zerotier.ZerotierClient.ZeroTierNetwork
        :param name: Name for the nic if left blank will be the name of the network
        :type name: str
        """
        name = name or network.name
        nic = ZTNic(name, network.id, None, self._parent)
        nic.client = network.client
        self._items.append(nic)
        return nic

    def get_by_type_id(self, type_, networkid):
        for nic in self:
            if nic.networkid == str(networkid) and nic.type == type_:
                return nic
        raise j.exceptions.NotFound("No nic found with type id combination {}:{}".format(type_, networkid))


class DynamicCollection:
    def __iter__(self):
        for item in self.list():
            yield item

    def __getitem__(self, name):
        for item in self.list():
            if item.name == name:
                return item
        raise j.exceptions.NotFound("Name {} does not exists".format(name))

    def __contains__(self, name):
        try:
            self[name]
            return True
        except KeyError:
            return False

    def __str__(self):
        return str(self.list())

    __repr__ = __str__


class Service:
    """
    Abstract implementation of services that need to be managed on containers.
    This class assumes the following attributes exist on the inheriting class:
    _container: holds the container sal. Should be initialized with None
    _container_name: the name the will be used to create the container
    _id: the id of the job
    _type: the type of the service ex: minio
    _ports: a list of ports to check if the container is listening to. It is used to verify that the process is running
    name: the name of the service
    """

    def __init__(self, name, node, service_type, ports, autostart=False):
        self.name = name
        self.node = node
        self._type = service_type
        self._id = "{}.{}".format(self._type, self.name)
        self._container = None
        self._container_name = "{}_{}".format(self._type, self.name)
        self._ports = ports
        self._autostart = autostart

    def _container_exists(self):
        """
        Check if the container exists on the node
        :return: True if it exists, False if not
        :rtype: boolean
        """
        try:
            self.node.containers.get(self._container_name)
            return True
        except LookupError:
            return False

    def destroy(self):
        """
        Stop the service process and stop the container
        """
        self.stop()

    def is_running(self, timeout=15):
        """
        Check if the service is running and listening to the expected ports
        :return: True if running, False if not
        :rtype: boolean

        """
        if not self._container_exists():
            return False

        if not self._autostart:
            try:
                self.container.client.job.list(self._id)
            except:
                return False

        for port in self._ports:
            if not self.container.is_port_listening(port, timeout):
                return False
        return True

    def stop(self, timeout=30):
        """
        Stop the service process and stop the container
        """
        if not self._container_exists():
            return

        if self.is_running():
            self.container.client.job.unschedule(self._id)
            self.container.client.job.kill(self._id)
            if not j.tools.timer.execute_until(lambda: not self.is_running(), timeout, 0.5):
                j.tools.logger._log_warning("Failed to gracefully stop {} server: {}".format(self._type, self.name))

        self.container.stop()
        self._container = None

    @property
    def container(self):
        """
        Get/create service container
        :return: service container
        :rtype: container sal object
        """
        if self._container is None:
            try:
                self._container = self.node.containers.get(self._container_name)
            except LookupError:
                self._container = self.node.containers.create(**self._container_data)
        return self._container

    def add_nics(self, nics):
        if nics:
            for nic in nics:
                nicobj = self.nics.add(nic["name"], nic["type"], nic["id"], nic.get("hwaddr"))
                if nicobj.type == "zerotier":
                    nicobj.client_name = nic.get("ztClient")
        if "nat0" not in self.nics:
            self.nics.add("nat0", "default")

    def authorize_zt_nics(self):
        if not self.zt_identity:
            self.zt_identity = self.node.client.system("zerotier-idtool generate").get().stdout.strip()
        zt_public = (
            self.node.client.system("zerotier-idtool getpublic {}".format(self.zt_identity)).get().stdout.strip()
        )
        authorize_zerotiers(zt_public, self.nics)
