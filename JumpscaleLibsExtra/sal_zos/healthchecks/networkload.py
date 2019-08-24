from .healthcheck import HealthCheckRun


descr = """
Check the bandwith consumption of the network
"""


class NetworkLoad(HealthCheckRun):
    def __init__(self, node):
        self.node = node
        resource = "/nodes/{}".format(node.node_id)
        super().__init__(id="network-load", name="Network Load Check", category="Hardware", resource=resource)

    def run(self):
        results = []
        nics_speed = {nic["name"]: nic["speed"] for nic in self.node.client.info.nic()}
        self.get_network_data("incoming", nics_speed)
        self.get_network_data("outgoing", nics_speed)

    def get_network_data(self, direction, nics_speed):
        throughput = self.node.client.aggregator.query("network.throughput.%s" % direction)
        for nic in throughput:
            throughput_history = throughput[nic].get("history", {}).get("3600", [])
            if throughput_history:
                last_throughput = throughput_history[-1].get("avg", 0)
                nic_name = nic.split("/")[-1]
                nic_speed = nics_speed.get(nic_name, 0)
                if nic_speed > 0:
                    nic_speed = nic_speed / 8
                    percent = (last_throughput / float(nic_speed)) * 100
                    if percent > 90:
                        self.add_message(
                            id="%s_%s" % (nic_name, direction),
                            status="ERROR",
                            text="Nic {} {} bandwith is {:.2f}%".format(nic_name, direction, percent),
                        )
                    elif percent > 80:
                        self.add_message(
                            id="%s_%s" % (nic_name, direction),
                            status="WARNING",
                            text="Nic {} {} bandwith is {:.2f}%".format(nic_name, direction, percent),
                        )
                    else:
                        self.add_message(
                            id="%s_%s" % (nic_name, direction),
                            status="OK",
                            text="Nic {} {} bandwith is {:.2f}%".format(nic_name, direction, percent),
                        )
