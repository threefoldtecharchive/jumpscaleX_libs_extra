from builtins import isinstance
from collections.abc import KeysView, MutableMapping

from Jumpscale import j

from . import encoding
from .error import ProxyNameConflictError
from .types import Backend, BackendServer, Frontend, FrontendRule, LoadBalanceMethod, RoutingKind

JSConfigBase = j.baseclasses.object_config


class TraefikClient(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.traefik.client
    name** = "" (S)
    etcd_instance = "main" (S)
    """

    def _init(self, **kwargs):
        self._etcd_client = None
        self._etcd_instance = self.etcd_instance
        self.proxies = ProxyMap(self)
        self._frontends = {}
        self._backends = {}

    @property
    def etcd_client(self):
        if not self._etcd_client:
            self._etcd_client = j.clients.etcd.get(self._etcd_instance)
        return self._etcd_client

    def proxy_create(self, name):
        """
        create a new reverse proxy

        :param name: name of your proxy, it needs to be unique inside the etcd cluster
        :type name: str
        :raises ProxyNameConflictError: Proxy name already exists
        :return: reverse proxy
        :rtype: Object
        """
        if name in self.proxies:
            raise ProxyNameConflictError("a proxy named %s already exists")

        self.proxies[name] = Proxy(self.etcd_client, name)
        return self.proxies[name]


class Proxy:
    """
    The main class to use for adding/deleting reverse proxy forwarding into etcd
    """

    def __init__(self, etcd_client, name, frontend=None, backend=None):
        """
        :param etcd_client: etcd client instance (j.clients.etcd.get())
        """
        self.etcd_client = etcd_client
        self.name = name
        self.frontend = frontend
        self.backend = backend

    def frontend_set(self, domain):
        """
        set a frontend on the proxy.
        The frontend will redirect requests coming to domain to the backend of this proxy

        :param domain: domain name
        :type domain: str
        :return: return a frontend object on which you can fine tune the frontend routing rules
        :rtype: sal.traefik.types.Frontend
        """

        # remove previous frontend if any
        if self.frontend:
            encoding.frontend_delete(self.etcd_client, self.frontend)

        self.frontend = Frontend(name=self.name, backend_name=self.name)
        self.frontend.rule_add(domain)
        return self.frontend

    def backend_set(self, endpoints=None):
        """
        set a backend on the proxy.
        The backend will receive all the equests coming to domain configured in the frontend of this proxy

        :param endpoints: if provided, a list of url to the backend servers
        :type endpoints: list
        :return: return a backend object on which you can configure more backend server
        :rtype: sal.traefik.types.Backend
        """
        # remove previous backend if any
        if self.backend:
            encoding.backend_delete(self.etcd_client, self.backend)

        if not isinstance(endpoints, list):
            endpoints = [endpoints]

        self.backend = Backend(self.name)
        for endpoint in endpoints or []:
            self.backend.server_add(endpoint)
        return self.backend

    def deploy(self):
        """
        write the configuration of this proxy to etcd
        """
        # register the backends and frontends for traefik use
        if self.backend:
            encoding.backend_write(self.etcd_client, self.backend)
        if self.frontend:
            encoding.frontend_write(self.etcd_client, self.frontend)

    def delete(self):
        """
        remove backends or frontends from etcd
        """
        if self.backend:
            encoding.backend_delete(self.etcd_client, self.backend)
        if self.frontend:
            encoding.frontend_delete(self.etcd_client, self.frontend)

        self.backend = None
        self.frontend = None

    def __repr__(self):
        return "<Proxy> %s" % self.name


class ProxyMap(MutableMapping):
    def __init__(self, traefik):
        super().__init__()
        self._traefik = traefik
        self.__names = []
        self._proxies = {}

    @property
    def _names(self):
        if not self.__names:
            self.__names = encoding.proxy_list(self._traefik.etcd_client)
        return self.__names

    def _load_proxy(self, name):
        proxy = Proxy(self._traefik.etcd_client, name)
        proxy.frontend = encoding.frontend_load(self._traefik.etcd_client, name)
        proxy.backend = encoding.backend_load(self._traefik.etcd_client, name)
        self._proxies[name] = proxy
        return proxy

    def keys(self):
        return KeysView(self._names)

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise j.exceptions.Value("index should be a str, not %s" % type(key))

        if key not in self._names:
            raise IndexError()

        if key not in self._proxies:
            self._load_proxy(key)
        return self._proxies[key]

    def __setitem__(self, key, value):
        if not isinstance(value, Proxy):
            raise j.exceptions.Value()
        if not isinstance(key, str):
            raise j.exceptions.Value()

        self._names.append(key)
        self._names.sort()
        self._proxies[key] = value

    def __delitem__(self, key):
        if not isinstance(key, str):
            raise j.exceptions.Value("index should be a string, not %s" % type(key))

        if key not in self._names:
            raise j.exceptions.NotFound()

        self._names.remove(key)
        if key in self._proxies:
            del self._proxies[key]

    def __len__(self):
        return len(self._names)

    def __iter__(self):
        for name in self._names:
            if name in self._proxies:
                yield self._proxies[name]
            else:
                yield self._load_proxy(name)

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self._names
        if isinstance(item, Proxy):
            return item.name in self._names
        return False

    def __repr__(self):
        d = {}
        for name in self._names:
            d[name] = "<Proxy> %s" % name
        return repr(d)

    def __str__(self):
        d = {}
        for name in self._names:
            d[name] = "<Proxy> %s" % name
        return str(d)
