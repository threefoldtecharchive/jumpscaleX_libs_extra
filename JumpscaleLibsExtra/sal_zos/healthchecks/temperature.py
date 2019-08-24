from .healthcheck import IPMIHealthCheck


descr = """
Checks temperature of the system.
Result will be shown in the "Temperature" section of the Grid Portal / Status Overview / Node Status page.
"""


class Temperature(IPMIHealthCheck):
    WARNING_TRIPPOINT = 70
    ERROR_TRIPPOINT = 90

    def __init__(self, node):
        self.node = node
        resource = "/nodes/{}".format(node.node_id)
        super().__init__("temperature", "Node Temperature Check", "Hardware", resource)

    def run(self, container):
        out = self.execute_ipmi(container, "ipmitool sdr type 'Temp'")
        if out:
            if out:
                # SAMPLE:
                # root@du-conv-3-01:~# ipmitool sdr type "Temp"
                # Temp             | 0Eh | ok  |  3.1 | 37 degrees C
                # Temp             | 0Fh | ok  |  3.2 | 34 degrees C
                # Inlet Temp       | B1h | ok  | 64.96 | 28 degrees C
                # Exhaust Temp     | B2h | ns  | 144.96 | Disabled
                for line in out.splitlines():
                    if "|" in line:
                        parts = [part.strip() for part in line.split("|")]
                        id_, sensorstatus, message = parts[0], parts[2], parts[-1]

                        if sensorstatus == "ns" and "no reading" in message.lower():
                            continue

                        if sensorstatus != "ok" and "no reading" not in message.lower():
                            self.add_message(**self.get_message(sensor=id_, status="WARNING", message=message))
                            continue
                        temperature = int(message.split(" ", 1)[0])
                        self.add_message(
                            **self.get_message(
                                sensor=id_, status=sensorstatus, message=message, temperature=temperature
                            )
                        )
        else:
            self.add_message(**self.get_message(status="SKIPPED", message="NO temp information available"))

    def get_message(self, sensor="", status="OK", message="", temperature=0):
        result = {"status": status.upper(), "text": "%s: %s" % (sensor, message), "id": sensor}
        if status != "OK":
            return result

        if temperature >= self.WARNING_TRIPPOINT:
            result["status"] = "WARNING"
        elif temperature >= self.ERROR_TRIPPOINT:
            result["status"] = "ERROR"
        return result
