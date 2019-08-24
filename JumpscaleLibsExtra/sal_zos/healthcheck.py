import hashlib
import json
import os
import traceback
from Jumpscale import j


class HealthCheckObject:
    def __init__(self, id, name, category, resource):

        self.id = id
        self.name = name
        self.category = category
        self._messages = []
        self.resource = resource
        self.stacktrace = ""

    def add_message(self, id, status, text):
        self._messages.append({"id": id, "text": text, "status": status})

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "resource": self.resource,
            "stacktrace": self.stacktrace or "",
            "messages": self._messages,
        }


class HealthCheckRun(HealthCheckObject):
    def start(self, *args, **kwargs):
        try:
            self.run(*args, **kwargs)
        except Exception as e:
            self.stacktrace = traceback.format_exc()

        return self.to_dict()


class IPMIHealthCheck(HealthCheckRun):
    def execute_ipmi(self, container, cmd):
        if self.node.client.filesystem.exists("/dev/ipmi") or self.node.client.filesystem.exists("/dev/ipmi0"):
            return container.client.system(cmd).get().stdout
        return ""


class ContainerContext:
    def __init__(self, node, flist):
        self.node = node
        self.flist = flist
        self.container = None
        self._name = "healthcheck_{}".format(hashlib.md5(flist.encode()).hexdigest())

    def __enter__(self):
        try:
            self.container = self.node.containers.get(self._name)
        except LookupError:
            self.container = self.node.containers.create(self._name, self.flist, host_network=True, privileged=True)
        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        return


class HealthCheck:
    def __init__(self, node):
        self.node = node
        self.healtcheckfolder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "healthchecks")

    def with_container(self, flist):
        return ContainerContext(self.node, flist)

    def run(self, container, name, timeout=None):
        try:
            healthcheckfile = os.path.join(self.healtcheckfolder, name + ".py")
            if not os.path.exists(healthcheckfile):
                raise j.exceptions.Base("Healtcheck with name {} not found".format(name))
            container.client.filesystem.upload_file("/tmp/{}.py".format(name), healthcheckfile)
            try:
                job = container.client.bash("python3 /tmp/{}.py".format(name))
                response = job.get(timeout)
            except TimeoutError:
                container.client.job.kill(job.id, 9)
                raise j.exceptions.Base("Failed to execute {} on time".format(name))
            if response.state == "ERROR":
                raise j.exceptions.Base("Failed to execute {} {}".format(name, response.stdout))
            try:
                return json.loads(response.stdout)
            except Exception:
                raise j.exceptions.Base("Failed to parse response of {}".format(name))
        except Exception as e:
            healtcheck = {"id": name, "status": "ERROR", "message": str(e)}
            return healtcheck

    def cpu_mem(self):
        from .healthchecks.cpu_mem_core import CPU, Memory

        cpu = CPU(self.node)
        memory = Memory(self.node)
        return [cpu.start(), memory.start()]

    def disk_usage(self):
        from .healthchecks.diskusage import DiskUsage

        usage = DiskUsage(self.node)
        return usage.start()

    def network_bond(self):
        from .healthchecks.networkbond import NetworkBond

        bond = NetworkBond(self.node)
        return bond.start()

    def node_temperature(self, container):
        from .healthchecks.temperature import Temperature

        temperature = Temperature(self.node)
        result = temperature.start(container)
        return result

    def network_stability(self, nodes):
        from .healthchecks.networkstability import NetworkStability

        stability = NetworkStability(self.node)
        return stability.start(nodes)

    def qemu_vm_logs(self):
        from .healthchecks.qemu_vm_logs import QemuVMLogs

        vmCheck = QemuVMLogs(self.node)
        return vmCheck.start()

    def rotate_logs(self):
        from .healthchecks.log_rotator import RotateLogs

        rotator = RotateLogs(self.node)
        return rotator.start()

    def openfiledescriptors(self):
        from .healthchecks.openfiledescriptors import OpenFileDescriptor

        ofd = OpenFileDescriptor(self.node)
        return ofd.start()

    def interrupts(self):
        from .healthchecks.interrupts import Interrupts

        inter = Interrupts(self.node)
        return inter.start()

    def threads(self):
        from .healthchecks.threads import Threads

        thread = Threads(self.node)
        return thread.start()

    def ssh_cleanup(self, job):
        from .healthchecks.ssh_cleanup import SSHCleanup

        cleaner = SSHCleanup(self.node, job)
        return cleaner.start()

    def powersupply(self, container):
        from .healthchecks.powersupply import PowerSupply

        powersupply = PowerSupply(self.node)
        return powersupply.start(container)

    def fan(self, container):
        from .healthchecks.fan import Fan

        fan = Fan(self.node)
        return fan.start(container)

    def context_switch(self):
        from .healthchecks.context_switch import ContextSwitch

        return ContextSwitch(self.node).start()

    def network_load(self):
        from .healthchecks.networkload import NetworkLoad

        load = NetworkLoad(self.node)
        return load.start()
