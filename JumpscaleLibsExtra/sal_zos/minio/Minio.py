import signal
import time

from Jumpscale import j

from .. import templates
from ..abstracts import Service


DEFAULT_PORT = 9000


class Minio(Service):
    """
    Minio gateway
    """

    def __init__(
        self,
        name,
        node,
        login,
        password,
        zdbs,
        namespace,
        private_key,
        node_port,
        namespace_secret="",
        block_size=1048576,
        meta_private_key="",
        nr_datashards=1,
        nr_parityshards=0,
        tlog_namespace=None,
        tlog_address=None,
        master_namespace=None,
        master_address=None,
    ):
        """
        :param name: instance name
        :param node: sal of the node to deploy minio on
        :param login: minio access key
        :param password minio secret key
        :param zdbs: a list of zerodbs addresses ex: ['0.0.0.0:9100']
        :param namespace: name of the zerodb namespace
        :param private_key: encryption private key
        :param node_port: public port on the node that if forwarded to the minio listening port in the container
        :param namespace_secret: secret of the zerodb namespace
        :param nr_datashards: number of datashards.
        :param nr_parityshards: number of parityshards (if it's zero it will make the mode replication otherwise mode is distribution)
        :param tlog_namespace: name of the zerodb namespace used as tlog
        :param tlog_address: ip:port of the zerodb namespace used as tlog
        :param master_namespace: name of the zerodb namespace used as master
        :param master_address: ip:port of the zerodb namespace used as master
        """
        super().__init__(name, node, "minio", [DEFAULT_PORT])

        self.flist = "https://hub.grid.tf/tf-official-apps/minio-1.5.0.flist"
        self.zdbs = zdbs
        self._nr_datashards = nr_datashards
        self._nr_parityshards = nr_parityshards
        self.namespace = namespace
        self.private_key = private_key
        self.node_port = node_port
        self.namespace_secret = namespace_secret
        self.block_size = block_size
        self.login = login
        self.password = password
        self.meta_private_key = meta_private_key
        self.tlog = None
        self.master = None
        if tlog_namespace and tlog_address:
            self.tlog = {"namespace": tlog_namespace, "address": tlog_address, "password": namespace_secret}
        if master_namespace and master_address:
            self.master = {"namespace": master_namespace, "address": master_address, "password": namespace_secret}

        self._config_dir = "/bin"
        self._config_name = "zerostor.yaml"

    @property
    def _container_data(self):
        """
        :return: data used for zerodb container
         :rtype: dict
        """
        metadata_path = "/minio_metadata"
        envs = {
            "MINIO_ACCESS_KEY": self.login,
            "MINIO_SECRET_KEY": self.password,
            "MINIO_ZEROSTOR_META_PRIVKEY": self.meta_private_key,
            "MINIO_ZEROSTOR_META_DIR": metadata_path,
        }

        # select a storage pool where to create subvolume to mount into the container
        # we want only the storage pool on top of an SSD
        pools = filter(lambda p: p.type.value == "SSD", self.node.storagepools.list())
        # sort all the SSD storage pool by ussage
        pools = sorted(pools, key=lambda p: p.used)
        fs = None
        for sp in pools:
            try:
                fs = sp.get(self._id)
            except ValueError:
                try:
                    fs = sp.create(self._id)
                except Exception as err:
                    j.tools.logger._log_warning(
                        "couldn create storage pool filesystem: %s\nTrying another disk" % str(err)
                    )
                    continue
            if fs:
                break

        if fs is None:
            raise j.exceptions.Base("couldn't find a disk to use to mount in the container")

        return {
            "name": self._container_name,
            "flist": self.flist,
            "ports": {self.node_port: DEFAULT_PORT},
            "nics": [{"type": "default"}],
            "env": envs,
            "mounts": {fs.path: metadata_path},
            "cpu": 2,
            "memory": 4906,  # 4GiB
        }

    def start(self, timeout=15):
        """
        Start minio gatway
        :param timeout: time in seconds to wait for the minio gateway to start
        """
        if self.is_running():
            return

        j.tools.logger._log_info("start minio %s" % self.name)

        def test_started():
            self._container = None
            return self.container.is_running()

        if not j.tools.timer.execute_until(test_started, 10, 1):
            raise j.exceptions.Base("failed to start container")

        self.create_config()

        logo_path = None
        if self.logo_url:
            logo_path = self.download_logo()

        cmd = "/bin/minio gateway "
        if logo_path:
            cmd += " --logo %s" % logo_path

        cmd += " zerostor --address 0.0.0.0:{port} --config-dir {dir}".format(port=DEFAULT_PORT, dir=self._config_dir)

        # wait for minio to start
        job = self.container.client.system(cmd, id=self._id, recurring_period=10)
        if not j.tools.timer.execute_until(self.is_running, 30, 0.5):
            result = job.get()
            raise j.exceptions.Base("Failed to start minio server {}: {}".format(self.name, result.stderr))

    def stream(self, callback):
        if not self.is_running:
            raise Exception("minio is not running")

        self.container.client.subscribe(self._id, "%s.logs" % self._id).stream(callback)

    @property
    def mode(self):
        return "replication" if self._nr_parityshards <= 0 else "distribution"

    def create_config(self):
        j.tools.logger._log_info("Creating minio config for %s" % self.name)
        config = self._config_as_text()
        self.container.upload_content(j.sal.fs.joinPaths(self._config_dir, self._config_name), config)

    def download_logo(self):
        dest = os.path.join("/mnt/containers", str(self.container.id), "minio_metadata", "logo.svg")
        resp = self.node.client.web.download(self.logo_url, dest).get()
        if resp.state != "SUCCESS":
            raise j.exceptions.Base("impossible to download the minio logo: %s" % resp.stderr)
        return "/minio_metadata/logo.svg"

    def _config_as_text(self):
        return templates.render(
            "minio.conf",
            namespace=self.namespace,
            namespace_secret=self.namespace_secret,
            zdbs=self.zdbs,
            private_key=self.private_key,
            block_size=self.block_size,
            nr_datashards=self._nr_datashards,
            nr_parityshards=self._nr_parityshards,
            tlog=self.tlog,
            master=self.master,
        ).strip()

    def reload(self):
        """
        tell minio process to reload its configuration by reading the config file again
        """
        if not self.is_running():
            j.tools.logger._log_error("cannot reload when minio is not running")
            return

        self.container.client.job.kill(self._id, signal.SIGHUP)

    def destroy(self):
        super().destroy()

        for sp in self.node.storagepools.list():
            try:
                fs = sp.get(self._id)
                fs.delete()
                break
            except ValueError:
                continue

    def check_and_repair(self):
        cmd = "/bin/minio gateway zerostor-repair --config-dir {dir}".format(dir=self._config_dir)

        job = self.container.client.system(cmd)
        while job.running:
            time.sleep(10)
            j.tools.logger._log_info("Check and repair still running")

        result = job.get()
        if result.state == "ERROR":
            raise j.exceptions.Base("Failed to do check and repair")
