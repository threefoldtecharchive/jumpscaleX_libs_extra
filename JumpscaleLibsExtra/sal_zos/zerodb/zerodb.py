import redis
import time

from Jumpscale import j

from ..abstracts import Nics, Service
from ..disks.Disks import Disk
from .namespace import Namespaces


DEFAULT_PORT = 9900
PUBLIC_THREEFOLD_NETWORK = "9bee8941b5717835"

GiB = 1024 ** 3


class Zerodb(Service):
    def __init__(self, node, name, node_port, path=None, mode="user", sync=False, admin=""):
        """
        Create zerodb object

        To deploy zerodb invoke .deploy method

        :param node: the node on which the zerodb is created
        :type: node: node sal object
        :param name: Name of the zerodb
        :type name: str
        :param node_port: public port on the node that is forwarded to the zerodb listening port in the container
        :type node_port: int
        :param pat: path zerodb stores data on
        :type path: str
        :param mode: zerodb running mode (seq, user)
        :type mode: str
        :param sync: zerodb sync
        :type sync: bool
        :param admin: zerodb admin password
        :type admin: str
        :param node_port: the port the zerodb container will forward to. If this port is not free, the deploy will find the next free port.
        :type: int
        """
        super().__init__(name, node, "zerodb", [DEFAULT_PORT])

        self.node_port = node_port
        self.zt_identity = None
        self.flist = "https://hub.grid.tf/tf-official-apps/threefoldtech-0-db-release-1.0.0.flist"

        self._mode = mode
        self._sync = sync
        self._admin = admin
        self._path = None

        # call setters to enforce validation
        self.mode = mode
        self.admin = admin
        self.sync = sync

        if path:
            self.path = path

        self.namespaces = Namespaces(self)
        self.nics = Nics(self)
        self.nics.add("nat0", "default")
        public_threefold_nic = False
        for nic in self.nics:
            nic_dict = nic.to_dict()
            if nic_dict["id"] == PUBLIC_THREEFOLD_NETWORK:
                public_threefold_nic = True
                break
        if not public_threefold_nic:
            self.nics.add("threefold", "zerotier", PUBLIC_THREEFOLD_NETWORK)

        self.__redis = None

    @property
    def _redis(self):
        """
        Get redis connection

        :return: redis client used to execute commands on zerodb
        :rtype: Redis class
        """
        if self.__redis is None:
            ip = self.container.node.addr
            port = DEFAULT_PORT
            password = self.admin

            if ip == "127.0.0.1":
                ip = self.container.default_ip().ip.format()
            else:
                # use the connection below if you want to test a dev setup and to execute it from outside the node
                port = self.node_port

            self.__redis = redis.Redis(host=ip, port=port, password=password)
            self.__redis.ping()

        return self.__redis

    @property
    def info(self):
        info = self.node.client.btrfs.info(self.node.get_mount_path(self.path))
        used = 0
        total = 0
        reserved = 0
        devicename = None
        for device in info["devices"]:
            used += device["used"]
            total += device["size"]
            devicename = device["path"]

        device = self.node.disks.get_device(devicename)
        devicetype = None
        if isinstance(device, Disk):
            devicetype = device.type.value
        else:
            devicetype = device.disk.type.value
        for namespace in self.namespaces:
            reserved += namespace.size * GiB

        return {
            "used": used,
            "reserved": reserved,
            "total": total,
            "free": total - reserved,
            "path": self.path,
            "mode": self.mode,
            "sync": self.sync,
            "type": devicetype,
        }

    @property
    def _container_data(self):
        """
        :return: data used for zerodb container
        :rtype: dict
        """
        self.authorize_zt_nics()

        return {
            "name": self._container_name,
            "flist": self.flist,
            "identity": self.zt_identity,
            "mounts": {self.path: "/zerodb"},
            "ports": {str(self.node_port): DEFAULT_PORT},
            "nics": [nic.to_dict(forcontainer=True) for nic in self.nics],
        }

    def load_from_reality(self, container=None):
        """
        loads zerodb data from reality.
        Loads node_port, path, sync, mode and admin

        :param container: zerodb container
        :type container: container sal object
        """
        if not container:
            container = self.node.containers.get(self._container_name)

        for k, v in container.mounts.items():
            if v == "/zerodb":
                self.path = k

        self.node_port = container.get_forwarded_port(DEFAULT_PORT)

        if self.is_running():
            jobs = self._container.client.job.list(self._id)
            if not jobs:
                return
            args = jobs[0]["cmd"]["arguments"]["args"]
            for arg in args:
                if arg == "--sync":
                    self.sync = True
                if arg == "--mode":
                    self.mode = args[args.index(arg) + 1]
                if arg == "--admin":
                    self.admin = args[args.index(arg) + 1]

    def from_dict(self, data):
        """
        Update zerodb from data.
        Updates mode, admin, sync, path, node_port, and namespaces.

        :param data: zerodb data
        :type data: dict
        """
        self.nics = Nics(self)
        self.mode = data.get("mode", "user")
        self.admin = data.get("admin", "")
        self.zt_identity = data.get("ztIdentity")
        self.sync = data.get("sync", False)
        self.path = data["path"]
        for namespace in data.get("namespaces", []):
            self.namespaces.add(
                namespace["name"], namespace.get("size"), namespace.get("password"), namespace.get("public", True)
            )
        self.add_nics(data.get("nics", []))
        self.node_port = data.get("nodePort")

    def to_dict(self):
        """
        Convert zerodb object to dict
        :return: dict containing zerodb data
        :rtype: dict
        """
        namespaces = []
        for namespace in self.namespaces:
            namespaces.append(
                {
                    "name": namespace.name,
                    "size": namespace.size if namespace.size else 0,
                    "password": namespace.password,
                    "public": namespace.public,
                }
            )

        return {
            "mode": self.mode,
            "sync": self.sync,
            "admin": self.admin,
            "ztIdentity": self.zt_identity,
            "path": self.path,
            "nics": [nic.to_dict() for nic in self.nics],
            "namespaces": namespaces,
            "node_port": self.node_port,
        }

    def to_json(self):
        """
        json serialize zerodb dict

        :return: a json formatted string of self.to_dict
        :rtype: str
        """
        return j.data.serializers.json.dumps(self.to_dict())

    def deploy(self):
        """
        Deploy zerodb by creating a container and running zerodb in the container, creating the namespaces in self.namespaces and
        removing namespaces that are not in self.namespaces.
        """
        total_namespaces_sizes = sum([ns.size * GiB for ns in self.namespaces])
        self._filesystem.quota = total_namespaces_sizes

        self.start()

        live_namespaces = self._live_namespaces()

        for namespace in self.namespaces:
            namespace.deploy(live_namespaces)

        for namespace in live_namespaces:
            if namespace not in self.namespaces and namespace != "default":
                self._redis.execute_command("NSDEL", namespace)

    def start(self, timeout=15):
        """
        Start zero db server
        :param timeout: time in seconds to wait for the zerodb server to start
        :type timeout: int
        """
        if self.is_running():
            return

        j.tools.logger._log_info("start zerodb %s" % self.name)

        cmd = "/bin/zdb \
            --port {port} \
            --data /zerodb/data \
            --index /zerodb/index \
            --mode {mode} \
            ".format(
            port=DEFAULT_PORT, mode=self.mode
        )
        if self.sync:
            cmd += " --sync"
        if self.admin:
            cmd += " --admin {}".format(self.admin)

        # wait for zerodb to start
        self.container.client.system(cmd, id=self._id)
        if not j.tools.timer.execute_until(self.is_running, timeout, 0.5):
            raise j.exceptions.Base("Failed to start zerodb server: {}".format(self.name))

    def _live_namespaces(self):
        """
        List the namespaces created on zerodb.

        :return: a list of namespaces
        :rtype: list of strings
        """
        result = self._redis.execute_command("NSLIST")
        return [namespace.decode("utf-8") for namespace in result]

    def destroy(self):
        super().destroy()

        for sp in self.node.storagepools.list():
            for fs in sp.list():
                if fs.path == self.path:
                    fs.delete()
                    return

    @property
    def _storage_pool(self):
        return self.node.storagepools.get(self.path.split("/")[3])

    @property
    def _filesystem(self):
        return self._storage_pool.get(self.path.split("/")[-1])

    @property
    def disk_type(self):
        return self._storage_pool.type

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if not value:
            raise j.exceptions.Value("path can't be empty")
        if type(value) != str:
            raise j.exceptions.Value("path must be a string")
        self._path = value

    @property
    def admin(self):
        return self._admin

    @admin.setter
    def admin(self, value):
        self._admin = value

    @property
    def sync(self):
        return self._sync

    @sync.setter
    def sync(self, value):
        if type(value) != bool:
            raise j.exceptions.Value("sync must be a boolen")
        self._sync = value

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        if value not in ["user", "seq", "direct"]:
            raise j.exceptions.Value("mode must be user, seq or direct")
        self._mode = value

    def __str__(self):
        return "Zerodb {}".format(self.name)

    def __repr__(self):
        return str(self)
