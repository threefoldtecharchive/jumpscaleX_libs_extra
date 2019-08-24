from . import encoding
from .TraefikClient import Proxy
from .types import Backend, BackendServer, Frontend, FrontendRule, LoadBalanceMethod, RoutingKind


class Meta:
    def __init__(self, key):
        self.key = key


class Api:
    def __init__(self, client):
        self._client = client

    def get(self, key):
        if isinstance(key, str):
            key = key.encode()
        value = self._client._data.get(key)
        return (value, Meta(key))

    def get_prefix(self, prefix):
        if isinstance(prefix, str):
            prefix = prefix.encode()
        for k, v in list(self._client._data.items()):
            if k.startswith(prefix):
                yield (v, Meta(k))

    def delete_prefix(self, prefix):
        if isinstance(prefix, str):
            prefix = prefix.encode()
        for k in list(self._client._data.keys()):
            if k.startswith(prefix):
                del self._client._data[k]


class EtcdClientMock:
    def __init__(self):
        self._data = {}
        self.api = Api(self)

    def put(self, key, value):
        if isinstance(value, str):
            value = value.encode()
        self._data[key.encode()] = value

    def get(self, key):
        return self._data.get(key)


def test_encoding_backend():
    client = EtcdClientMock()
    server1 = BackendServer("http://192.168.1.1:8080", 10)
    server2 = BackendServer("https://192.168.1.1:8081", 20)
    backend = Backend("backend1", servers=[server1, server2], load_balance_method=LoadBalanceMethod.drr)
    encoding.backend_write(client, backend)

    assert client._data == {
        b"/traefik/backends/backend1/loadBalancer/method": b"drr",
        b"/traefik/backends/backend1/servers/server0/url": b"http://192.168.1.1:8080",
        b"/traefik/backends/backend1/servers/server0/weight": b"10",
        b"/traefik/backends/backend1/servers/server1/url": b"https://192.168.1.1:8081",
        b"/traefik/backends/backend1/servers/server1/weight": b"20",
    }

    encoding.backend_delete(client, backend)
    assert client._data == {}


def test_encoding_frontend():
    client = EtcdClientMock()
    rule = FrontendRule("my.domain.com", RoutingKind.Host)
    frontend = Frontend("frontend1", "backend1", [rule])

    encoding.frontend_write(client, frontend)

    assert client._data == {
        b"/traefik/frontends/frontend1/backend": b"backend1",
        b"/traefik/frontends/frontend1/routes/rule0/rule": b"Host:my.domain.com",
    }

    encoding.frontend_delete(client, frontend)
    assert client._data == {}


def test_proxy_deploy_delete():
    client = EtcdClientMock()

    proxy1 = Proxy(client, "proxy1")
    backend = proxy1.backend_set(["http://192.168.1.1:8080"])
    server = backend.server_add("https://192.168.1.1:8081")
    server.weight = 20
    backend.load_balance_method = LoadBalanceMethod.drr
    frontend = proxy1.frontend_set("my.domain.com")
    proxy1.deploy()

    proxy2 = Proxy(client, "proxy2")
    backend = proxy2.backend_set(["http://192.168.2.1:8080"])
    server = backend.server_add("https://192.168.2.1:8081")
    server.weight = 20
    backend.load_balance_method = LoadBalanceMethod.wrr
    rule = FrontendRule("his.domain.com", RoutingKind.Host)
    frontend = proxy2.frontend_set("his.domain.com")
    proxy2.deploy()

    assert client._data == {
        b"/traefik/backends/proxy1/loadBalancer/method": b"drr",
        b"/traefik/backends/proxy1/servers/server0/url": b"http://192.168.1.1:8080",
        b"/traefik/backends/proxy1/servers/server0/weight": b"10",
        b"/traefik/backends/proxy1/servers/server1/url": b"https://192.168.1.1:8081",
        b"/traefik/backends/proxy1/servers/server1/weight": b"20",
        b"/traefik/frontends/proxy1/backend": b"proxy1",
        b"/traefik/frontends/proxy1/routes/rule0/rule": b"Host:my.domain.com",
        b"/traefik/backends/proxy2/loadBalancer/method": b"wrr",
        b"/traefik/backends/proxy2/servers/server0/url": b"http://192.168.2.1:8080",
        b"/traefik/backends/proxy2/servers/server0/weight": b"10",
        b"/traefik/backends/proxy2/servers/server1/url": b"https://192.168.2.1:8081",
        b"/traefik/backends/proxy2/servers/server1/weight": b"20",
        b"/traefik/frontends/proxy2/backend": b"proxy2",
        b"/traefik/frontends/proxy2/routes/rule0/rule": b"Host:his.domain.com",
    }

    proxy1.delete()
    assert client._data == {
        b"/traefik/backends/proxy2/loadBalancer/method": b"wrr",
        b"/traefik/backends/proxy2/servers/server0/url": b"http://192.168.2.1:8080",
        b"/traefik/backends/proxy2/servers/server0/weight": b"10",
        b"/traefik/backends/proxy2/servers/server1/url": b"https://192.168.2.1:8081",
        b"/traefik/backends/proxy2/servers/server1/weight": b"20",
        b"/traefik/frontends/proxy2/backend": b"proxy2",
        b"/traefik/frontends/proxy2/routes/rule0/rule": b"Host:his.domain.com",
    }
    proxy2.delete()
    assert client._data == {}


def test_frontend_load():
    client = EtcdClientMock()
    client._data = {
        b"/traefik/frontends/frontend1/backend": b"backend1",
        b"/traefik/frontends/frontend1/routes/rule0/rule": b"Host:my.domain.com",
    }
    frontend = encoding.frontend_load(client, "frontend1")
    assert frontend.name == "frontend1"
    assert frontend.backend_name == "backend1"
    assert len(frontend.rules) == 1
    assert frontend.rules[0].value == "my.domain.com"
    assert frontend.rules[0].type == RoutingKind.Host


def test_backend_load():
    client = EtcdClientMock()
    client._data = {
        b"/traefik/backends/backend1/loadBalancer/method": b"drr",
        b"/traefik/backends/backend1/servers/server0/url": b"http://192.168.1.1:8080",
        b"/traefik/backends/backend1/servers/server0/weight": b"10",
        b"/traefik/backends/backend1/servers/server1/url": b"https://192.168.1.1:8081",
        b"/traefik/backends/backend1/servers/server1/weight": b"20",
    }
    backend = encoding.backend_load(client, "backend1")
    assert backend.name == "backend1"
    assert backend.load_balance_method == LoadBalanceMethod.drr
    assert backend.cb_expression == None
    assert len(backend.servers) == 2
    assert backend.servers[0].ip == "192.168.1.1"
    assert backend.servers[0].port == 8080
    assert backend.servers[0].scheme == "http"
    assert backend.servers[0].weight == "10"
    assert backend.servers[1].ip == "192.168.1.1"
    assert backend.servers[1].port == 8081
    assert backend.servers[1].scheme == "https"
    assert backend.servers[1].weight == "20"
