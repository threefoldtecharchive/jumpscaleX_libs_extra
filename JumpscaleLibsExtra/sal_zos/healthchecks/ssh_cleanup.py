from Jumpscale import j

from .healthcheck import HealthCheckRun


descr = """
Clean up ssh deamons and tcp services from migration
"""


class SSHCleanup(HealthCheckRun):
    def __init__(self, node, service):
        resource = "/nodes/{}".format(node.node_id)
        super().__init__("ssh-cleanup", "SSH Cleanup", "System Cleanup", resource)
        self.node = node

    def run(self):
        status = "OK"
        text = "Migration Cleanup Succesful"
        finished = []
        try:
            for job in self.service.aysrepo.jobsList():
                job_dict = job.to_dict()
                if job_dict["actionName"] == "processChange" and job_dict["actorName"] == "vm":
                    if job_dict["state"] == "running":
                        continue
                    vm = self.service.aysrepo.serviceGet(instance=job_dict["serviceName"], role=job_dict["actorName"])
                    tcp_services = vm.producers.get("tcp", [])
                    for tcp_service in tcp_services:
                        if "migrationtcp" not in tcp_service.name:
                            continue
                        tcp_service.executeAction("drop", context=self.job.context)
                        tcp_service.delete()
                    finished.append("ssh.config_%s" % vm.name)

            for proc in self.node.client.process.list():
                for partial in finished:
                    if partial not in proc["cmdline"]:
                        continue
                    config_file = proc["cmdline"].split()[-1]
                    self.node.client.process.kill(proc["pid"])
                    if self.node.client.filesystem.exists("/tmp"):
                        self.node.client.filesystem.remove(config_file)

        except Exception as e:
            text = "Error happened, Can not clean ssh process "
            status = "ERROR"

        self.add_message(self.id, status, text)
