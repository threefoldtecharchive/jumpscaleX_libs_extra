import time
from Jumpscale import j
from .. import templates
from ..abstracts import Nics, Service
from ..globals import TIMEOUT_DEPLOY


DEFAULT_PORT_HTTP = 80
DEFAULT_PORT_HTTPS = 443


class Traefik(Service):
    """
    Traefik a modern HTTP reverse proxy
    """

    def __init__(self, name, node, etcd_endpoint, etcd_password, etcd_watch=True, zt_identity=None, nics=None):
        super().__init__(name, node, "traefik", [DEFAULT_PORT_HTTP, DEFAULT_PORT_HTTPS])
        self.name = name
        self.node = node
        self._container = None
        self.flist = "https://hub.grid.tf/tf-official-apps/traefik-v1.7.0-rc5.flist"
        self.etcd_endpoint = etcd_endpoint
        self.etcd_watch = etcd_watch
        self.etcd_password = etcd_password
        self.node_port = None

        self._config_path = "/usr/bin/traefik.toml"
        self.zt_identity = zt_identity
        self.nics = Nics(self)
        self.add_nics(nics)

    @property
    def _container_data(self):
        """
        :return: data used for traefik container
         :rtype: dict
        """
        self.node_port = DEFAULT_PORT_HTTP
        ports = {str(DEFAULT_PORT_HTTP): DEFAULT_PORT_HTTP, str(DEFAULT_PORT_HTTPS): DEFAULT_PORT_HTTPS}  # HTTPS
        self.authorize_zt_nics()

        return {
            "name": self._container_name,
            "flist": self.flist,
            "ports": ports,
            "nics": [nic.to_dict(forcontainer=True) for nic in self.nics],
            "identity": self.zt_identity,
        }

    def deploy(self, timeout=TIMEOUT_DEPLOY):
        """create traefik contianer and get ZT ip

        Keyword Arguments:
            timeout {int} -- timeout of get ZeroTier IP (default: {120})
        """

        # call the container property to make sure it gets created and the ports get updated
        self.container
        if not j.tools.timer.execute_until(lambda: self.container.mgmt_addr, timeout, 1):
            raise j.exceptions.Base("Failed to get zt ip for traefik {}".format(self.name))

    def container_port(self, port):

        return self._container.get_forwarded_port(port)

    def create_config(self):
        """
        create configuration of traefik and upload it in the container
        """
        j.tools.logger._log_info("Creating traefik config for %s" % self.name)
        config = self._config_as_text()
        self.container.upload_content(self._config_path, config)

    def _config_as_text(self):
        """
        render traefik config template using etcd endpoint, user, password
        """
        return templates.render(
            "traefik.conf", etcd_endpoint=self.etcd_endpoint, user="root", passwd=self.etcd_password
        ).strip()

    def start(self, timeout=TIMEOUT_DEPLOY):
        """
        Start traefik
        store config in etcd
        :param timeout: time in seconds to wait for the traefik to start
        """
        if self.is_running():
            return

        j.tools.logger._log_info("start traefik %s" % self.name)

        self.deploy()
        self.create_config()

        cmd = "/usr/bin/traefik storeconfig -c {}".format(self._config_path)
        result = self.container.client.system(cmd).get()
        if result.state != "SUCCESS":
            raise j.exceptions.Base("fail to store traefik configuration in etcd: %s" % result.stderr)

        # wait for traefik to start
        cmd = "/usr/bin/traefik -c {}".format(self._config_path)
        job = self.container.client.system(cmd, id=self._id)
        if not j.tools.timer.execute_until(self.is_running, timeout, 0.5):
            result = job.get()
            raise j.exceptions.Base("Failed to start Traefik server {}: {}".format(self.name, result.stderr))
