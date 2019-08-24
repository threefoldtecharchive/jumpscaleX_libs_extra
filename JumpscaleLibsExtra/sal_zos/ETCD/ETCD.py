from io import BytesIO

import etcd3
import yaml

from .. import templates
from ..abstracts import Nics, Service
from ..globals import TIMEOUT_DEPLOY


CLIENT_PORT = 2379
PEER_PORT = 2380


class ETCD(Service):
    """etced server"""

    def __init__(
        self,
        node,
        name,
        password,
        data_dir="/mnt/data",
        zt_identity=None,
        nics=None,
        token=None,
        cluster=None,
        host_network=False,
    ):
        super().__init__(name, node, "etcd", [CLIENT_PORT, PEER_PORT])
        self.flist = "https://hub.grid.tf/tf-official-apps/etcd-3.3.4.flist"
        self.data_dir = data_dir
        self.zt_identity = zt_identity
        self._config_path = "/bin/etcd_{}.config".format(self.name)
        self.token = token
        self.cluster = cluster
        self.password = password
        self.host_network = host_network
        self.nics = Nics(self)
        self.add_nics(nics)

    def connection_info(self):
        return {
            "ip": self.container.mgmt_addr,
            "client_port": CLIENT_PORT,
            "peer_port": PEER_PORT,
            "peer_url": self.peer_url,
            "client_url": self.client_url,
            "password": self.password,
            "cluster_entry": self.cluster_entry,
        }

    @property
    def cluster_entry(self):
        return "{}={}".format(self.name, self.peer_url)

    @property
    def client_url(self):
        """
        return client url
        """
        return "http://{}:{}".format(self.container.mgmt_addr, CLIENT_PORT)

    @property
    def peer_url(self):
        """
        return peer url
        """
        return "http://{}:{}".format(self.node.storage_addr, PEER_PORT)

    @property
    def _container_data(self):
        """
        :return: data used for etcd container
         :rtype: dict
        """
        sp = self.node.find_persistance()
        try:
            fs = sp.get(self._container_name)
        except ValueError:
            fs = sp.create(self._container_name)

        self.authorize_zt_nics()

        data = {
            "name": self._container_name,
            "flist": self.flist,
            "nics": [nic.to_dict(forcontainer=True) for nic in self.nics],
            "mounts": {fs.path: self.data_dir},
            "identity": self.zt_identity,
            "env": {"ETCDCTL_API": "3"},
            "host_network": self.host_network,
        }
        if not self.host_network:
            data["ports"] = {"2380": 2380, "2379": 2379}
        else:
            self.node.client.nft.open_port(2379)
            self.node.client.nft.open_port(2380)

        return data

    def create_config(self):
        """
        create configuration of Etcd and upload it in container
        """

        self.container.upload_content(self._config_path, self._config_as_text())

    def _config_as_text(self):
        """
        render etcd config template
        """

        cluster = self.cluster or self.cluster_entry
        config = {
            "name": self.name,
            "initial_peer_urls": self.peer_url,
            "listen_peer_urls": "http://0.0.0.0:{}".format(PEER_PORT),
            "listen_client_urls": "http://0.0.0.0:{}".format(CLIENT_PORT),
            "advertise_client_urls": self.client_url,
            "data_dir": self.data_dir,
            "token": self.token,
            "cluster": cluster,
        }
        return templates.render("etcd.conf", **config).strip()

    def deploy(self, timeout=TIMEOUT_DEPLOY):
        # call the container property to make sure it gets created and the ports get updated
        self.container
        if not j.tools.timer.execute_until(lambda: self.container.mgmt_addr, timeout, 1):
            raise j.exceptions.Base("Failed to get zt ip for etcd {}".format(self.name))

    def start(self):
        if self.is_running():
            return

        j.tools.logger._log_info("start etcd {}".format(self.name))
        self.deploy()
        self.create_config()
        cmd = "/bin/etcd --config-file {}".format(self._config_path)
        self.container.client.system(cmd, id=self._id)
        if not j.tools.timer.execute_until(self.is_running, 30, 0.5):
            raise j.exceptions.Base("Failed to start etcd server: {}".format(self.name))

    def stop(self):
        super().stop()
        if self.host_network:
            self.node.client.nft.open_port(2379)
            self.node.client.nft.open_port(2380)

    def enable_auth(self):
        """
        enable authentication of etcd user
        """

        commands = [
            "/bin/etcdctl --endpoints={} user add root:{}".format(self.client_url, self.password),
            "/bin/etcdctl --endpoints={} auth enable".format(self.client_url),
        ]

        for command in commands:
            result = self.container.client.system(command).get()
            if result.state == "ERROR":
                if "already exists" in result.stderr or "user name not found" in result.stderr:
                    # this command has been executed before
                    continue
                else:
                    raise j.exceptions.Base(result.stderr)

    def prepare_traefik(self):
        result = self.container.client.system(
            '/bin/etcdctl --endpoints={} --user=root:{} put "traefik/acme/account" "foo"'.format(
                self.client_url, self.password
            )
        ).get()
        if result.state != "SUCCESS":
            raise j.exceptions.Base("fail to prepare traefik configuration: %s" % result.stderr)
