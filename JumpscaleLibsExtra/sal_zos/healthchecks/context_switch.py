import time

from .healthcheck import HealthCheckRun


descr = """
Monitors CPU context switching
"""


class ContextSwitch(HealthCheckRun):
    def __init__(self, node, warn=600000, error=1000000):
        super().__init__("context-switch", "Context Switch", "Hardware", "/nodes/{}".format(node.node_id))
        self.node = node
        self._warn = warn
        self._error = error

    def run(self):
        client = self.node.client

        state = client.aggregator.query("machine.CPU.contextswitch").get("machine.CPU.contextswitch")
        if state is None:
            # nothing to check yet
            return self.add_message(self.id, "WARNING", "Number of context-switches per second is not collected yet")

        # time of last reported value
        last_time = state["last_time"]
        current = state["current"]["300"]
        # start time of the current 5min sample
        current_time = current["start"]
        if current_time < time.time() - (10 * 60):
            return self.add_message(self.id, "WARNING", "Last collected context-switch are too far in the past")

        # calculate avg per second
        value = current["avg"] / (last_time - current_time)

        status = "OK"
        text = "Context-switches are okay"

        if value >= self._error:
            status = "ERROR"
            text = "Contex-switches exceeded error threshold of {} ({})".format(self._error, value)
        elif value >= self._warn:
            status = "WARNING"
            text = "Contex-switches exceeded warning threshold of {} ({})".format(self._warn, value)

        return self.add_message(self.id, status, text)
