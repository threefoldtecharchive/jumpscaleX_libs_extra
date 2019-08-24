from .healthcheck import IPMIHealthCheck


descr = """
Checks the fans of a node using IPMItool.
Result will be shown in the "Hardware" section of the Grid Portal / Status Overview / Node Status page.
"""


class Fan(IPMIHealthCheck):
    def __init__(self, node):
        self.node = node
        resource = "/nodes/{}".format(node.node_id)
        super().__init__(id="fan", name="Fan", category="Hardware", resource=resource)

    def run(self, container):
        out = self.execute_ipmi(container, """ipmitool sdr type "Fan" """)
        if out:
            # SAMPLE:
            # root@du-conv-3-01:~# ipmitool sdr type "Fan"
            # FAN1             | 41h | ok  | 29.1 | 5000 RPM
            # FAN2             | 42h | ns  | 29.2 | No Reading
            # FAN3             | 43h | ok  | 29.3 | 4800 RPM
            # FAN4             | 44h | ns  | 29.4 | No Reading

            for line in out.splitlines():
                parts = [part.strip() for part in line.split("|")]
                id_, sensorstatus, text = parts[0], parts[2], parts[-1]
                if sensorstatus == "ns" and "no reading" in text.lower():
                    self.add_message(
                        id=id_, status="SKIPPED", text="Fan {id} has no reading ({text})".format(id=id_, text=text)
                    )
                elif sensorstatus != "ok" and "no reading" not in text.lower():
                    self.add_message(
                        id=id_, status="WARNING", text="Fan {id} has problem ({text})".format(id=id_, text=text)
                    )
                elif sensorstatus == "ok":
                    self.add_message(
                        id=id_, status="OK", text="Fan {id} is working at ({text})".format(id=id_, text=text)
                    )
        else:
            self.add_message(id="SKIPPED", status="SKIPPED", text="NO fan information available")
