from .healthcheck import HealthCheckRun


descr = """
Monitors if threads has high number of threads per hyperthread
"""


class Threads(HealthCheckRun):
    def __init__(self, node):
        resource = "/nodes/{}".format(node.node_id)
        super().__init__(id="threads", name="Node thread per hyperthread", category="System Load", resource=resource)
        self.node = node

    def run(self):
        hyperthread_count = len(self.node.client.info.cpu())

        thread_info = self.node.client.aggregator.query("machine.process.threads", type="phys")
        thread_info = thread_info.get("machine.process.threads", {})
        message = {}
        if not thread_info:
            message = {"status": "WARNING", "id": "THREADS", "text": "Number of threads is not available"}
            self.add_message(**message)
            return

        avg_thread = thread_info["current"]["300"]["avg"] / hyperthread_count
        message["id"] = "THREADS"
        if avg_thread > 300:
            message["status"] = "WARNING"
            message["text"] = "Average threads per hyperthread is high"
        elif avg_thread > 400:
            message["status"] = "ERROR"
            message["text"] = "Average threads per hyperthread is critical"
        else:
            message["status"] = "OK"
            message["text"] = "Average threads per hyperthread is normal"

        self.add_message(**message)
