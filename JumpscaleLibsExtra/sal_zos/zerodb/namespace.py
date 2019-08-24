from Jumpscale import j
from redis import ResponseError

from ..abstracts import Collection


class NamespaceInfo:
    def __init__(
        self,
        name,
        public,
        password,
        index_size_kb,
        index_size_bytes,
        entries,
        data_size_mb,
        data_size_bytes,
        data_limits_bytes,
        mode,
        **kwargs,
    ):
        self.name = name
        self.public = True if public == "yes" else False
        self.password = True if password == "yes" else False
        self.index_size_kb = float(index_size_kb)
        self.index_size_bytes = int(index_size_bytes)
        self.entries = int(entries)
        self.data_size_mb = float(data_size_mb)
        self.data_size_bytes = int(data_size_bytes)
        self.data_limits_bytes = int(data_limits_bytes)
        self.mode = mode

    def to_dict(self):
        return {
            "name": self.name,
            "public": "yes" if self.public else "no",
            "password": "yes" if self.password else "no",
            "index_size_kb": self.index_size_kb,
            "index_size_bytes": self.index_size_bytes,
            "entries": self.entries,
            "data_size_mb": self.data_size_mb,
            "data_size_bytes": self.data_size_bytes,
            "data_limits_bytes": self.data_limits_bytes,
            "mode": self.mode,
        }

    def __str__(self):
        return "Namespace Info <{}".format(self.name)

    def __repr__(self):
        return str(self)


class Namespace:
    def __init__(self, parent, name, size=None, password=None, public=True):
        """
        Namespace

        :param name: name of the namespace
        :type name: str
        :param size: maximum size of the namespace
        :type size: int
        :param password: namespace password
        :type password: str
        :param public: namespace public property
        :type public: bool
        """
        self.parent = parent
        self.name = name
        self.size = size
        self.password = password
        self.public = public

    @property
    def url(self):
        url = "zdb://{}:{}?size={}G&blocksize=4096&namespace={}".format(
            self.parent.node.public_addr, self.parent.node_port, self.size, self.name
        )
        if self.password:
            url += "&password={}".format(self.password)
        return url

    @property
    def private_url(self):
        url = "zdb://{}:9900?size={}G&blocksize=4096&namespace={}".format(
            self.parent.container.default_ip().ip, self.size, self.name
        )
        if self.password:
            url += "&password={}".format(self.password)
        return url

    def set_property(self, prop, value):
        """
        set a namespace propert
        :param prop: property name
        :type prop: str
        :param value: property value
        :type value: mixed
        """
        if prop not in ["maxsize", "password", "public"]:
            raise j.exceptions.Value("Property must be maxsize, password, or public")

        self.parent._redis.execute_command("NSSET", self.name, prop, value)

    def info(self):
        """
        Get the namespace info that results from executing NSINFO.
        Namespace must be deployed first.
        :return: namespace info
        :rtype:NamespaceInfo object
        """
        try:
            info = self.parent._redis.execute_command("NSINFO", self.name).decode("utf-8")
            info = info.replace("# namespace\n", "")
            info_lines = info.splitlines()
            result = {}
            for info_line in info_lines:
                info_split = info_line.split(":")
                result[info_split[0].strip()] = info_split[1].strip()
            return NamespaceInfo(**result)
        except ResponseError:
            raise j.exceptions.Base("Must deploy namespace before retrieving namespace info")

    def deploy(self, namespaces=None):
        """
        deploy a namespace by creating it in zerodb if it doesn't exist and setting all its properties
        :param namespaces: a list of namespaces that are currently on the running zerodb
        :type namespaces: list of str
        """
        if not namespaces:
            namespaces = self.parent._live_namespaces()

        if self.name not in namespaces:
            self.parent._redis.execute_command("NSNEW", self.name)

        if self.size:
            self.set_property("maxsize", self.size * 1024 ** 3)
        if self.password:
            self.set_property("password", self.password)
        self.set_property("public", int(self.public))

    def __str__(self):
        return "Namespace {}".format(self.name)

    def __repr__(self):
        return str(self)


class Namespaces(Collection):
    def add(self, name, size=None, password=None, public=True):
        """
        Add namespace name
        :param name: name of the namespace
        :type name: str
        :param size: maximum size of the namespace
        :type size: int
        :param password: namespace password
        :type password: str
        :param public: namespace public property
        :type public: bool

        :return: namespace
        :rtype: namespace object
        """
        super().add(name)
        namespace = Namespace(self._parent, name, size, password, public)
        self._items.append(namespace)
        return namespace
