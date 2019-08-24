import re
from xml.etree import ElementTree
from Jumpscale import j

JSBASE = j.baseclasses.object


class NetworkScanner(j.baseclasses.object):
    COMMAND = "nmap -n --disable-arp-ping -send-ip -Pn -sS -p{ports} -oX - {cidr}"

    def __init__(self, cidr, ports=[80]):
        JSBASE.__init__(self)
        code, _, _ = j.sal.process.execute("which nmap", showout=False, die=False)
        if code != 0:
            self._log_info("nmap not found, installing...")
            j.builders.system.package.install("nmap")

        self._ports = ",".join([str(port) for port in ports])
        self._cidr = cidr

    def scan(self):
        """nmap -n --disable-arp-ping -send-ip -Pn -sS -p22 -oX - 172.17.0.1/24"""

        cmd = self.COMMAND.format(ports=self._ports, cidr=self._cidr)
        code, output, err = j.sal.process.execute(cmd, showout=False, die=False)
        if code != 0:
            raise j.exceptions.RuntimeError("nmap scan failed")

        dom = ElementTree.fromstring(output)
        hosts = {}
        for host in dom.findall("host"):
            address = host.find("address").attrib["addr"]
            for port in host.findall("ports/port"):
                if port.find("state").attrib["state"] == "open":
                    hosts.setdefault(address, []).append(int(port.attrib["portid"]))
        return hosts
