import psutil

from .healthcheck import HealthCheckRun


descr = """
Check open file descriptors for each node process, if it exceeds 90% of the soft limit, it raises a warning,
if it exceeds 90% of the hard limit, it raises an error.
"""


class OpenFileDescriptor(HealthCheckRun):
    def __init__(self, node):
        resource = "/nodes/{}".format(node.node_id)
        super().__init__("openfile-descriptors", "Open File Descriptors", "System Load", resource)
        self.node = node

    def run(self):
        for process in self.node.client.process.list():
            for rlimit in process["rlimit"]:
                if rlimit["resource"] == psutil.RLIMIT_NOFILE:
                    pid = str(process["pid"])
                    if (0.9 * rlimit["soft"]) <= process["ofd"] < (0.9 * rlimit["hard"]):
                        self.add_message(
                            pid, "WARNING", "Open file descriptors for process %s exceeded 90%% of the soft limit" % pid
                        )
                    elif process["ofd"] >= (0.9 * rlimit["hard"]):
                        self.add_message(
                            pid, "ERROR", "Open file descriptors for process %s exceeded 90%% of the hard limit" % pid
                        )
                    break

        if not self._messages:
            self.add_message("-1", "OK", "Open file descriptors for all processes are within limit")
