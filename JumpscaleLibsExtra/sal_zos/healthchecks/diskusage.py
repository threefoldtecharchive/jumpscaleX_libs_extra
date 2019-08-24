import re

from .healthcheck import HealthCheckRun


descr = """
Monitors if disk usage is too high
"""


class DiskUsage(HealthCheckRun):
    def __init__(self, node):
        resource = "/nodes/{}".format(node.node_id)
        super().__init__("disk-usage", "Disk Usage Check", "Hardware", resource)
        self.node = node

    def run(self):
        fs = self.node.client.btrfs.list()
        disks = {d["path"]: d for f in fs for d in f["devices"]}
        for path, disk in disks.items():
            usage = 100.0 * disk["used"] / disk["size"]
            if usage > 95:
                self.add_message(
                    "{}_usage".format(path), "ERROR", "Disk usage of {} is {:.2%}".format(path, usage / 100)
                )
            elif usage > 90:
                self.add_message(
                    "{}_usage".format(path), "WARNING", "Disk usage of {} is {:.2%}".format(path, usage / 100)
                )
            else:
                self.add_message("{}_usage".format(path), "OK", "Disk usage of {} is {:.2%}".format(path, usage / 100))
