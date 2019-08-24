import time

from .healthcheck import HealthCheckRun


descr = """
Monitors if a number of interrupts
"""


class Interrupts(HealthCheckRun):
    def __init__(self, node, warn=180000, error=200000):
        resource = "/nodes/{}".format(node.node_id)
        super().__init__("interrupts", "CPU Interrupts", "Hardware", resource)
        self._warn = warn
        self._error = error
        self.node = node

    def _get(self):
        client = self.node.client

        state = client.aggregator.query("machine.CPU.interrupts").get("machine.CPU.interrupts")
        if state is None:
            # nothing to check yet
            return {"id": self.id, "status": "WARNING", "text": "Number of interrupts per second is not collected yet"}

        # time of last reported value
        last_time = state["last_time"]
        current = state["current"]["300"]
        # start time of the current 5min sample
        current_time = current["start"]
        if current_time < time.time() - (10 * 60):
            return {"id": self.id, "status": "WARNING", "text": "Last collected interrupts are too far in the past"}

        # calculate avg per second
        value = current["avg"] / (last_time - current_time)

        status = "OK"
        text = "Interrupts are okay"

        if value >= self._error:
            status = "ERROR"
            text = "Interrupts exceeded error threshold of {} ({})".format(self._error, value)
        elif value >= self._warn:
            status = "WARNING"
            text = "Interrupts exceeded warning threshold of {} ({})".format(self._warn, value)

        return {"id": self.id, "status": status, "text": text}

    def run(self):
        self.add_message(**self._get())
