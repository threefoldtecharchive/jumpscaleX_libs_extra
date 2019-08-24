from Jumpscale import j
import yaml


class CloudInit:
    def __init__(self, container, networks):
        self.container = container
        self.networks = networks
        self.CONFIGPATH = "/etc/cloud-init"

    def apply_config(self):
        self.cleanup()
        for network in self.networks:
            for host in network.hosts:
                if not host.cloudinit.userdata["users"]:
                    continue
                data = {"userdata": host.cloudinit.userdata, "metadata": host.cloudinit.metadata}
                fpath = "%s/%s" % (self.CONFIGPATH, host.macaddress)
                self.container.upload_content(fpath, yaml.dump(data))
        if not self.is_running():
            self.start()

    def cleanup(self):
        macaddresses = []
        for network in self.networks:
            for host in network.hosts:
                macaddresses.append(host.macaddress)
        configs = self.container.client.filesystem.list(self.CONFIGPATH)
        for config in configs:
            if config["name"] not in macaddresses:
                self.container.client.filesystem.remove("%s/%s" % (self.CONFIGPATH, config["name"]))

    def start(self):
        if not self.is_running():
            self.container.client.system(
                "cloud-init-server \
                -bind 127.0.0.1:8080 \
                -config {config}".format(
                    config=self.CONFIGPATH
                ),
                id="cloudinit.{}".format(self.container.name),
            )

        if not j.tools.timer.execute_until(self.is_running, 10, 0.5):
            raise j.exceptions.Base("Failed to start cloudinit server")

    def is_running(self):
        for port in self.container.client.info.port():
            if port["network"] == "tcp" and port["port"] == 8080 and port["ip"] == "127.0.0.1":
                return True
        return False
