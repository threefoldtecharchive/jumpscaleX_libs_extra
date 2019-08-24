from Jumpscale import j

# import gevent


class CoordinatorHypervisor(j.world.system._CoordinatorBase):

    __jslocation__ = "j.world.hypervisor"

    def __init__(self):

        j.world.system._CoordinatorBase.__init__(self)

        from .ServiceVirtualBox import ServiceVirtualBox

        self.load(ServiceVirtualBox)
