from .healthcheck import IPMIHealthCheck


descr = """
Checks the power redundancy of a node using IPMItool.
Result will be shown in the "Hardware" section of the Grid Portal / Status Overview / Node Status page.
"""


class PowerSupply(IPMIHealthCheck):
    def __init__(self, node):
        resource = "/nodes/{}".format(node.node_id)
        super().__init__(id="pw-supply", name="Power Supply", category="Hardware", resource=resource)
        self.node = node
        self.ps_errmsgs = [
            "Power Supply AC lost",
            "Failure detected",
            "Predictive failure",
            "AC lost or out-of-range",
            "AC out-of-range, but present",
            "Config Erro",
            "Power Supply Inactive",
        ]

    def run(self, container):
        ps_errmsgs = [x.lower() for x in self.ps_errmsgs if x.strip()]
        linehaserrmsg = lambda line: any([x in line.lower() for x in ps_errmsgs])

        out = self.execute_ipmi(container, """ipmitool -c sdr type "Power Supply" """)
        if out:

            # SAMPLE 1:
            # root@du-conv-3-01:~# ipmitool -c sdr type "Power Supply"
            # PS1 Status , C8h , ok , 10.1 , Presence detected
            # PS2 Status,C9h , ok , 10.2 , Presence detected

            # SAMPLE 2:
            # root@stor-04:~# ipmitool -c sdr type "Power Supply"
            # PSU1_Status , DEh , ok , 10.1 , Presence detected
            # PSU2_Status , DFh , ns , 10.2 , No Reading
            # PSU3_Status , E0h , ok , 10.3 , Presence detected
            # PSU4_Status , E1h , ns , 10.4 , No Reading
            # PSU Redundancy , E6h , ok , 21.1 , Fully Redundant

            # SAMPLE 3:
            # root@stor-01:~# ipmitool -c sdr type "Power Supply"
            # PSU1_Status , DEh , ok , 10.1 , Presence detected ,  Power Supply AC lost
            # PSU2_Status , DFh , ns , 10.2 , No Reading
            # PSU3_Status , E0h , ok , 10.3 , Presence detected
            # PSU4_Status , E1h , ok , 10.4 , Presence detected
            # PSU Redundancy , E6h , ok , 21.1 , Redundancy Lost
            # PSU Alert , 16h , ns , 208.1 , Event-Only

            psu_redun_in_out = "PSU Redundancy".lower() in out.lower()
            is_fully_redundant = True if "fully redundant" in out.lower() else False
            for line in out.splitlines():
                if "status" in line.lower():
                    parts = [part.strip() for part in line.split(",")]
                    id_, presence = parts[0], parts[-1]
                    id_ = id_.strip("Status").strip("_").strip()  # clean the power supply name.
                    if linehaserrmsg(line):
                        if psu_redun_in_out and is_fully_redundant:
                            self.add_message(
                                id=id_, status="SKIPPED", text="Power redundancy problem on %s (%s)" % (id_, presence)
                            )
                        else:
                            self.add_message(
                                id=id_, status="WARNING", text="Power redundancy problem on %s (%s)" % (id_, presence)
                            )
                    else:
                        self.add_message(id=id_, status="OK", text="Power supply %s is OK" % id_)
        else:
            self.add_message(id="SKIPPED", status="SKIPPED", text="No data for Power Supplies")
