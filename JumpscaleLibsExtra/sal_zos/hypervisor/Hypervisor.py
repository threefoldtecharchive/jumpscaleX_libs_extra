from Jumpscale import j
from ..vm.ZOS_VM import ZOS_VM


class Hypervisor:
    def __init__(self, node):
        self.node = node

    def create(self, name, flist=None, vcpus=2, memory=2048):
        j.tools.logger._log_info("Creating kvm %s" % name)
        return ZOS_VM(self.node, name, flist, vcpus, memory)

    def list(self):
        for vm in self.node.client.kvm.list():
            vm = ZOS_VM(self.node, vm["name"])
            vm.load_from_reality()
            yield vm

    def get(self, name):
        vm = ZOS_VM(self.node, name)
        vm.load_from_reality()
        return vm
