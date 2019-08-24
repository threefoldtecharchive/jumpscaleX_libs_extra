import hashlib

from Jumpscale import j

from .healthcheck import HealthCheckRun


descr = """
Check on vm logs for errors.
"""


class QemuVMLogs(HealthCheckRun):
    def __init__(self, node):
        resource = "/nodes/{}".format(node.node_id)
        super().__init__("qemu-vm-logs", "Qemu VM Logs", "Qemu Logs", resource)
        self.node = node

    def run(self):
        search_phrases = ["error", "failed"]
        try:
            vmlogpath = "/var/log/libvirt/qemu/{vm_name}.log"
            domains_list = []
            # go for multiprocessing.
            results = []

            def report_domain(domain):
                logpath = vmlogpath.format(vm_name=domain)
                if self.node.client.filesystem.exists(logpath):
                    out = self.node.client.system("tail %s" % logpath).get()
                    last10 = out.stdout.splitlines()
                    for line in last10:
                        for phrase in search_phrases:
                            if phrase in line.lower():
                                message_id = hashlib.md5(str.encode(line)).hexdigest()
                                results.append(message_id)
                                self.add_message(id=message_id, status="ERROR", text=line)
                                return

            for machine in self.node.client.kvm.list():
                name = machine.get("name")
                if name:
                    domains_list.append(name)

            list(map(report_domain, domains_list))

            if len(results) == 0:
                message = "QEMU Logs are OK."
                message_id = hashlib.md5(str.encode(message)).hexdigest()
                self.add_message(id=message_id, status="OK", text=message)

        except Exception as e:
            text = "Error occured in health check for qemu_vm_check."
            status = "ERROR"
            self.add_message(self.id, status, text)
