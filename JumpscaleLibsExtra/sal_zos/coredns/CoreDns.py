import time
import json
from Jumpscale import j
from .. import templates
from ..abstracts import Nics, Service
from ..globals import TIMEOUT_DEPLOY


DEFAULT_PORT = 53


class Coredns(Service):
    """
    CoreDNS is a DNS server. It is written in Go
    """

    def __init__(
        self, name, node, etcd_endpoint, etcd_password, zt_identity=None, nics=None, backplane="backplane", domain=None
    ):
        super().__init__(name, node, "coredns", [DEFAULT_PORT])
        self.name = name
        self.node = node
        self._container = None
        self.flist = "https://hub.grid.tf/tf-official-apps/coredns.flist"
        self.etcd_endpoint = etcd_endpoint
        self.etcd_password = etcd_password
        self.domain = domain

        self._config_path = "/Corefile"
        self.zt_identity = zt_identity
        self.backplane = backplane
        self.nics = Nics(self)
        self.add_nics(nics)

    @property
    def _container_data(self):
        """
        :return: data used for coredns container
         :rtype: dict
        """
        ports = {str("{}:{}|udp".format(self.backplane, DEFAULT_PORT)): DEFAULT_PORT}
        self.authorize_zt_nics()

        return {
            "name": self._container_name,
            "flist": self.flist,
            "ports": ports,
            "nics": [nic.to_dict(forcontainer=True) for nic in self.nics],
            "identity": self.zt_identity,
            "env": {"ETCD_USERNAME": "root", "ETCD_PASSWORD": self.etcd_password},
        }

    def deploy(self, timeout=TIMEOUT_DEPLOY):
        """create coredns contianer and get ZT ip

        Keyword Arguments:
            timeout {int} -- timeout of get ZeroTier IP (default: {120})
        """

        # call the container property to make sure it gets created and the ports get updated
        self.container
        if not j.tools.timer.execute_until(lambda: self.container.mgmt_addr, timeout, 1):
            raise j.exceptions.Base("Failed to get zt ip for coredns {}".format(self.name))

    def create_config(self):
        """
        create configuration of coredns and upload it in the container
        """

        j.tools.logger._log_info("Creating coredns config for %s" % self.name)

        config = self._config_as_text()
        self.container.upload_content(self._config_path, config)

    def _config_as_text(self):
        """
        render the coredns config template
        """
        return templates.render("coredns.conf", etcd_endpoint=self.etcd_endpoint, domain=self.domain).strip()

    def start(self, timeout=TIMEOUT_DEPLOY):
        """
        Start coredns
        :param timeout: time in seconds to wait for the coredns to start
        """
        if self.is_running():
            return

        j.tools.logger._log_info("start coredns %s" % self.name)

        self.deploy()
        self.create_config()
        cmd = "/coredns -conf {}".format(self._config_path)
        # wait for coredns to start
        job = self.container.client.system(cmd, id=self._id)
        if not j.tools.timer.execute_until(self.is_running, timeout, 0.5):
            result = job.get()
            raise j.exceptions.Base("Failed to start CoreDns server {}: {}".format(self.name, result.stderr))
