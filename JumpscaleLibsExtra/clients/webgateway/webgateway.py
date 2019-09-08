from Jumpscale import j

from .service import Service
from .errors import ServiceExistError, ServiceNotFoundError

JSConfigBase = j.baseclasses.object_config


class WebGateway(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.webgateway.client
    name** = "" (S)
    etcd_instance = "main" (S)
    public_ips = [] (LS)
    """

    def _init(self, **kwargs):

        self.etcd = j.clients.etcd.get(self.etcd_instance)
        self.traefik = j.clients.traefik.get(
            self.name,
            host=self.etcd.host,
            port=self.etcd.port,
            user=self.etcd.user,
            password=self.etcd.password_,
            etcd_instance=self.etcd_instance,
        )
        self.coredns = j.clients.coredns.get(
            self.name,
            host=self.etcd.host,
            port=self.etcd.port,
            user=self.etcd.user,
            password=self.etcd.password_,
            etcd_instance=self.etcd_instance,
        )
        self.public_ips = self.public_ips or []
        self._services = None

    def public_ips_set(self, public_ips):
        """
        change the public ip that are used by the webgateway

        this method will update the webgateway config wit the new pulic ips
        and update all the configuration of the existing service to use the new ips

        :param public_ips: list of public ips to be used by te webgateway
        :type public_ips: [str]
        """
        self.public_ips = public_ips
        self.save

        # update
        for service in self.services:
            service.public_ips = public_ips
            service.deploy()

    @property
    def services(self):
        """
        list all the service exposed by the webgateway

        :return: list of service
        :rtype: list
        """
        if not self._services:
            self._services = self._load_services()
        return self._services

    def _load_services(self):
        services = []
        for name in self.traefik.proxies.keys():
            services.append(Service(name, self.public_ips, self.traefik, self.coredns))
        return services

    def service_create(self, name):
        """
        create a new service that you want to expose using the webgateway
        :param name: name of your service
        :type name: str
        :raises ServiceExistError: raised if  service with the same name already exists
        :return: service object
        :rtype: sal.webgateway.service.Service
        """
        if name in [s.name for s in self.services]:
            raise ServiceExistError(
                "a service with name %s already exist. maybe you are looking for `service_get(%s)`" % (name, name)
            )

        service = Service(name, self.public_ips, self.traefik, self.coredns)
        self.services.append(service)
        return service

    def service_get(self, name):
        """
        retrieve an existing service

        :param name: name of the service
        :type name: str
        :raises ServiceNotFoundError: raised when not service with the name provided is found
        :return: service object
        :rtype: sal.webgateway.service.Service
        """

        for service in self.services:
            if service.name == name:
                return service
        raise ServiceNotFoundError("no service named %s found" % name)
