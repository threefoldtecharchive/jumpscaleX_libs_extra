from io import StringIO
from urllib.parse import urlparse

from Jumpscale import j
from clients.coredns.ResourceRecord import RecordType


class Service:
    def __init__(self, name, public_ips, traefik, coredns):
        self.name = name
        self.public_ips = public_ips
        self._traefik = traefik
        self._coredns = coredns
        self._proxy = None

    @property
    def proxy(self):
        if not self._proxy:
            try:
                self._proxy = self._traefik.proxies.get(self.name)
            except:
                pass
        return self._proxy

    def _deploy_dns(self, domain):
        for ip in self.public_ips:
            self._coredns.zone_create(domain, ip)

    def _deploy_reverse_proxy(self, domain, endpoints):
        for endpoint in endpoints:
            u = urlparse(endpoint)
            if not all([u.hostname, u.port, u.scheme]):
                raise j.exceptions.Value("wrong format for endpoint %s" % endpoint)

        if not self.proxy:
            self._proxy = self._traefik.proxy_create(self.name)

        self.proxy.backend_set(endpoints)
        self.proxy.frontend_set(domain)

    def expose(self, domain, endpoints):
        """
        High level method to easily expose a service over a domain

        This method will do 2 things:
        1. configure coredns to handle the domain and point it to the public of the webgateway
        2. configure traefik to create a reverse proxy from the domain to all the endpoints

        :param domain: domain name you want to use to expose your service
        :type domain: str
        :param endpoints: list of URL used by the reverse proxy needs to use as backend
        :type endpoints: [str]
        """

        self._deploy_dns(domain)
        self._deploy_reverse_proxy(domain, endpoints)
        self.deploy()

    def deploy(self):
        """
        write all the configuration of the service to etcd
        use this method when you have manually change some configuration of the service
        and want to make it reality by writting it into etcd
        """
        if self.proxy:
            self.proxy.deploy()
        if self._coredns:
            self._coredns.deploy()

    def delete(self):
        """
        delete all trace from this service from etcd

        it will remove all traefik and all coredns configuration
        """
        if self.proxy:
            self.proxy.delete()
        # if self._coredns: TODO
        #     self._coredns.deploy()

    def summary(self):
        """
        helper method to print a summary of the configuration of your service
        :return: printable representation of the service
        :rtype: str
        """

        buf = StringIO()
        buf.write("Service %s\n" % self.name)
        if self.proxy:
            buf.write("frontend:\n")
            for rule in self.proxy.frontend.rules:
                buf.write("  %s\n" % rule.value)
            buf.write("backend:\n")
            for server in self.proxy.backend.servers:
                buf.write("  %s\n" % (server.url))
        return buf.getvalue()

    def __repr__(self):
        return "<WebGateway Service> %s" % self.name
