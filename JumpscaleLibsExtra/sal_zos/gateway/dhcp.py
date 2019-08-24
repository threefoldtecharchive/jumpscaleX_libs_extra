from Jumpscale import j
import signal
from .. import templates

DNSMASQ = "/bin/dnsmasq --conf-file=/etc/dnsmasq.conf -d"


class DHCP:
    def __init__(self, container, domain, networks):
        self.container = container
        self.domain = domain
        self.networks = networks

    def apply_config(self):
        dnsmasq = templates.render("dnsmasq.conf", domain=self.domain, networks=self.networks)
        self.container.upload_content("/etc/dnsmasq.conf", dnsmasq)

        dhcp = templates.render("dhcp", networks=self.networks)
        self.container.upload_content("/etc/dhcp", dhcp)

        self.stop()

        self.container.client.system(DNSMASQ, id="dhcp.{}".format(self.container.name))
        # check if command is listening for dhcp
        if not j.tools.timer.execute_until(self.is_running, 10):
            raise j.exceptions.Base("Failed to run dnsmasq")

    def is_running(self):
        for port in self.container.client.info.port():
            if port["network"] == "udp" and port["port"] == 53:
                return True

    def stop(self):
        for process in self.container.client.process.list():
            if "dnsmasq" in process["cmdline"]:
                self.container.client.process.kill(process["pid"], signal.SIGKILL)
                if not j.tools.timer.execute_until(lambda: not self.is_running(), 10):
                    raise j.exceptions.Base("Failed to stop DNSMASQ")
