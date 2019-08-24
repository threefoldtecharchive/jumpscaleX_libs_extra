import signal
import time

from .. import templates

from Jumpscale import j


class InfluxDB:
    def __init__(self, container, ip, port, rpcport):

        self.container = container
        self.ip = ip
        self.port = port
        # Only client-server port is forwarded
        self.rpcport = rpcport
        self._client = None

    @property
    def client(self):
        if not self._client:
            self._client = j.clients.influxdb.get(self.ip, port=self.port)
        return self._client

    def apply_config(self):
        influx_conf = templates.render("influxdb.conf", ip=self.ip, port=self.port, rpcport=self.rpcport)
        self.container.upload_content("/etc/influxdb/influxdb.conf", influx_conf)

    def is_running(self):
        for process in self.container.client.process.list():
            if "influxd" in process["cmdline"]:
                try:
                    self.list_databases()
                except:
                    return False, process["pid"]
                else:
                    return True, process["pid"]
        return False, None

    def stop(self, timeout=30):
        is_running, pid = self.is_running()
        if not is_running:
            return

        self.container.client.process.kill(pid, signal.SIGTERM)
        start = time.time()
        end = start + timeout
        is_running, _ = self.is_running()
        while is_running and time.time() < end:
            time.sleep(1)
            is_running, _ = self.is_running()

        if is_running:
            raise j.exceptions.Base("Failed to stop influxd.")

        if self.container.node.client.nft.rule_exists(self.port):
            self.container.node.client.nft.drop_port(self.port)

    def start(self, timeout=30):
        is_running, _ = self.is_running()
        if is_running:
            return

        self.apply_config()

        if not self.container.node.client.nft.rule_exists(self.port):
            self.container.node.client.nft.open_port(self.port)

        self.container.client.system("influxd")
        time.sleep(1)

        start = time.time()
        end = start + timeout
        is_running, _ = self.is_running()
        while not is_running and time.time() < end:
            time.sleep(1)
            is_running, _ = self.is_running()

        if not is_running:
            if self.container.node.client.nft.rule_exists(self.port):
                self.container.node.client.nft.drop_port(self.port)
            raise j.exceptions.Base("Failed to start influxd.")

    def list_databases(self):
        return self.client.get_list_database()

    def create_databases(self, databases):
        for database in databases:
            self.client.create_database(database)

    def drop_databases(self, databases):
        for database in databases:
            self.client.drop_database(database)
