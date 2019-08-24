from enum import Enum
from urllib.parse import urlparse

from . import encoding


class LoadBalanceMethod(Enum):
    wrr = "wrr"
    drr = "drr"


class Backend:
    def __init__(self, name, servers=None, load_balance_method=LoadBalanceMethod.wrr, cb_expression=None):
        """
        :param name: the name of backend to be referred to
        :param servers: list of backend servers objects `BackendServer`
        :param load_balance_method: the load balancing method to be used by traefik.
        it is either:
         - LoadBalanceMethod.WRR: weight round robin [the default]
         - LoadBalanceMethod.DRR: dynamic round robin
        :param cb_expression: str: the circuit breaker expression. It can be configured using:
            Methods: LatencyAtQuantileMS, NetworkErrorRatio, ResponseCodeRatio
            Operators: AND, OR, EQ, NEQ, LT, LE, GT, GE
        For example:
            'NetworkErrorRatio() > 0.5': watch error ratio over 10 second sliding window for a frontend.
            'LatencyAtQuantileMS(50.0) > 50': watch latency at quantile in milliseconds.
            'ResponseCodeRatio(500, 600, 0, 600) > 0.5': ratio of response codes in ranges [500-600) and [0-600).
        """
        self.name = name
        self.servers = servers or []
        if load_balance_method and not isinstance(load_balance_method, LoadBalanceMethod):
            raise j.exceptions.Value(
                "load_balance_method should be a LoadBalanceMethod enum not {}".format(type(load_balance_method))
            )
        self.load_balance_method = load_balance_method
        self.cb_expression = cb_expression  # TODO validate the cb_expression to be a valid one

    def server_add(self, url, weight="10"):
        server = BackendServer(url=url, weight=weight)
        self.servers.append(server)
        return server

    def __repr__(self):
        return "<Backend> {}".format(self.name)


class BackendServer:
    def __init__(self, url, weight="10"):
        if isinstance(url, bytes):
            url = url.decode()

        u = urlparse(url)
        self.ip = u.hostname
        self.port = u.port
        self.scheme = u.scheme
        self.weight = weight

    @property
    def url(self):
        return "%s:%s:%s" % (self.scheme, self.ip, self.port)

    def __repr__(self):
        return "<BackendServer> {}://{}:{}".format(self.scheme, self.ip, self.port)


class RoutingKind(Enum):
    Host = "Host"


class FrontendRule:
    def __init__(self, value, kind=RoutingKind.Host):
        """
        :param value: the value for this rule, it depends on the rule type
        :param kind:
        is the type of rule to be applied for url, you can use any rule of the matchers and modifiers:
            - matchers:
                - Headers, HeadersRegexp, Host, HostRegexp, Method, Path, PathStrip, PathStripRegex
                    PathPrefix, PathPrefixStrip, PathPrefixStripRegex, Query
            - modifiers:
                - AddPrefix, ReplacePath, ReplacePathRegex
        for more info: https://docs.traefik.io/basics/#modifiers
        """
        if not isinstance(kind, RoutingKind):
            raise j.exceptions.Value("type must be a RoutingKind enum not {}".format(type(kind)))
        self.value = value
        self.type = kind

    def __repr__(self):
        return "<FrontendRule> {}:{}".format(self.type.value, self.value)


class Frontend:
    def __init__(self, name, backend_name="", rules=None):
        """
        :param name: the name of backend to be referred to
        :param rules: the list of rules to be added for this frontend
        """
        self.name = name
        self.backend_name = backend_name
        self.rules = rules or []

    def rule_add(self, value, kind=RoutingKind.Host):
        """
        Add a routing rule

        :param value: the value for this rule, it depends on the rule type
        :param kind: is the type of rule to be applied for url, you can use any rule of the matchers and modifiers:
                    - matchers:
                        - Headers, HeadersRegexp, Host, HostRegexp, Method, Path, PathStrip, PathStripRegex
                            PathPrefix, PathPrefixStrip, PathPrefixStripRegex, Query
                    - modifiers:
                        - AddPrefix, ReplacePath, ReplacePathRegex
                    for more info: https://docs.traefik.io/basics/#modifiers
        :return: frontend rule
        :rtype: FrontendRule
        """

        rule = FrontendRule(value, kind)
        self.rules.append(rule)
        return rule

    def __repr__(self):
        return "<Frontend> {}".format(self.name)
