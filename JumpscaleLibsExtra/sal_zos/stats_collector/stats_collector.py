import time
from Jumpscale import j


class StatsCollector:
    def __init__(self, container, ip, port, db, retention, jwt):

        self.container = container
        self.ip = ip
        self.port = port
        self.db = db
        self.retention = retention
        self.jwt = jwt
        self.job_id = "stats_collector.{}".format(self.container.node.node_id)

    def get_command(self):
        cmd = ["0-statscollector"]

        if self.jwt:
            cmd.extend(["--jwt", self.jwt])
        if self.ip:
            cmd.extend(["--ip", self.ip])
        if self.port:
            cmd.extend(["--port", str(self.port)])
        if self.db:
            cmd.extend(["--db", self.db])
        if self.retention:
            cmd.extend(["--retention", self.retention])

        return " ".join(cmd)

    def start(self):
        if not self.is_running():
            self.container.client.system(self.get_command(), id=self.job_id)

        start = time.time()
        while time.time() + 10 > start:
            if self.is_running():
                return
            time.sleep(0.5)
        raise j.exceptions.Base("Failed to start stats_collector")

    def is_running(self):
        for job in self.container.client.job.list():
            if job["cmd"]["id"] == self.job_id:
                return True
        return False

    def stop(self):
        if not self.is_running():
            return
        self.container.client.job.kill(self.job_id)
