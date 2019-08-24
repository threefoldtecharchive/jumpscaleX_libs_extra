import re

from .healthcheck import HealthCheckRun


descr = """
Monitors if a network bond (if there is one) has both (or more) interfaces properly active.
"""


class NetworkBond(HealthCheckRun):
    def __init__(self, node):
        resource = "/nodes/{}".format(node.node_id)
        super().__init__("network-bond", "Network Bond Check", "Hardware", resource)
        self.node = node

    def run(self):
        ovs = "{}_ovs".format(self.node.node_id)
        try:
            container = self.node.containers.get(ovs)
        except LookupError:
            # no ovs configured nothing to report on
            return
        jobresult = container.client.system("ovs-appctl bond/show").get()
        if jobresult.state == "ERROR":
            return
        output = jobresult.stdout
        bonds = []
        bond = {}
        for match in re.finditer(
            "(?:---- bond-(?P<bondname>\w+) ----)?.+?\n(?:slave (?:(?P<slavename>\w+): (?P<state>\w+)))",
            output,
            re.DOTALL,
        ):
            groups = match.groupdict()
            slave = {"name": groups["slavename"], "state": groups["state"]}
            if groups["bondname"]:
                if bond:
                    bonds.append(bond)
                bond = {"name": groups["bondname"]}
            bond.setdefault("slaves", []).append(slave)
        if bond:
            bonds.append(bond)

        for bond in bonds:
            badslaves = []
            for slave in bond["slaves"]:
                if slave["state"] != "enabled":
                    badslaves.append(slave["name"])
            state = "OK"
            if badslaves:
                msg = "Bond: {} has problems with slaves {}".format(bond["name"], ", ".join(badslaves))
                state = "ERROR" if len(badslaves) == len(bond["slaves"]) else "WARNING"
            else:
                msg = "Bond: {}, all slave are ok".format(bond["name"])

            self.add_message(bond, state, msg)
