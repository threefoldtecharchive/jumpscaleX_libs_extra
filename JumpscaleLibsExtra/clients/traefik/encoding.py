from urllib.parse import urlparse

from .types import Backend, BackendServer, Frontend, FrontendRule, LoadBalanceMethod, RoutingKind


def backend_write(client, backend):
    # Set the load balance method
    if backend.load_balance_method:
        load_balance_key = "/traefik/backends/{}/loadBalancer/method".format(backend.name)
        client.put(load_balance_key, backend.load_balance_method.value)

    # Set the circuit breaker config if exists
    if backend.cb_expression:
        cb_key = "/traefik/backends/{}/circuitBreaker".format(backend.name)
        client.put(cb_key, backend.cb_expression)

    # Set the backend servers
    for i, server in enumerate(backend.servers):
        server_key = "/traefik/backends/{}/servers/server{}/url".format(backend.name, i)
        server_value = "{}://{}:{}".format(server.scheme, server.ip, server.port)
        client.put(server_key, server_value)
        server_weight_key = "/traefik/backends/{}/servers/server{}/weight".format(backend.name, i)
        client.put(server_weight_key, str(server.weight))


def backend_delete(client, backend):
    client.api.delete_prefix("/traefik/backends/{}".format(backend.name))


def frontend_write(client, frontend):
    key = "/traefik/frontends/{}/backend".format(frontend.name)
    value = frontend.backend_name
    client.put(key, value)

    for i, rule in enumerate(frontend.rules):
        key = "/traefik/frontends/{}/routes/rule{}/rule".format(frontend.name, i)
        value = "{}:{}".format(rule.type.value, rule.value)
        client.put(key, value)


def frontend_delete(client, frontend):
    client.api.delete_prefix("/traefik/frontends/{}".format(frontend.name))


def backend_load(client, name):
    backend = Backend(name)
    server_names = set()

    load_balancer, _ = client.api.get("/traefik/backends/{}/loadBalancer/method".format(name))
    if load_balancer:
        backend.load_balance_method = LoadBalanceMethod[load_balancer.decode()]

    cb_expression, _ = client.api.get("/traefik/backends/{}/circuitBreaker".format(name))
    if cb_expression:
        backend.cb_expression = cb_expression.decode()

    servers_info = client.api.get_prefix("/traefik/backends/{}/servers".format(name))
    for server, meta in servers_info:
        server_name = meta.key.decode().split("/")[5]
        if server_name in server_names:
            continue

        server_names.add(server_name)

        url, _ = client.api.get("/traefik/backends/{}/servers/{}/url".format(name, server_name))
        if not url:
            continue

        server = BackendServer(url)

        weight, _ = client.api.get("/traefik/backends/{}/servers/{}/weight".format(name, server_name))
        if weight:
            server.weight = weight.decode()
        backend.servers.append(server)
    return backend


def frontend_load(client, name):
    frontend = Frontend(name)

    backend, _ = client.api.get("/traefik/frontends/{}/backend".format(name))
    if backend:
        frontend.backend_name = backend.decode()

    routes = client.api.get_prefix("/traefik/frontends/{}/routes".format(name))
    for value, meta in routes:
        rule_name = meta.key.decode().split("/")[5]
        rule, _ = client.api.get("/traefik/frontends/{}/routes/{}/rule".format(name, rule_name))
        if rule:
            kind, value = rule.decode().split(":", 1)
            frontend.rules.append(FrontendRule(value, RoutingKind[kind]))

    return frontend


def proxy_list(client):
    """
    list all the proxy configuration present on etcd
    """
    backend_names = set()
    frontend_names = set()
    for _, meta in client.api.get_prefix("/traefik/backends"):
        ss = meta.key.decode().split("/")
        name = ss[3]
        backend_names.add(name)

    for _, meta in client.api.get_prefix("/traefik/frontends"):
        ss = meta.key.decode().split("/")
        name = ss[3]
        frontend_names.add(name)

    return sorted(list(backend_names.intersection()))


def load(client):
    backends = {}
    frontends = {}

    for _, meta in client.api.get_prefix("/traefik/backends"):
        ss = meta.key.decode().split("/")
        name = ss[3]
        if name not in backends:
            backends[name] = backend_load(client, name)

    for _, meta in client.api.get_prefix("/traefik/frontends"):
        ss = meta.key.decode().split("/")
        name = ss[3]
        if name not in frontends:
            frontends[name] = frontend_load(client, name)

    return frontends, backends
