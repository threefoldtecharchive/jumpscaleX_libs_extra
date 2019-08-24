from Jumpscale import j
import gevent

from DigitalMeLib.servers.digitalworld.BASE_CLASSES.ServiceBase import *


class ServiceVirtualBox(ServiceBase):

    _SCHEMA_TXT = """
    @url = world.hypervisor.virtualbox
    description = ""
    """

    # def __init__(self,id=None,name=None,servicepool=None):
    #     JSBASE.__init__(self,id,name,servicepool)

    @action
    def task1(self, descr):
        self._log_debug("TASK1:%s" % descr)
        return "RETURN:%s" % descr

    def task2(self, id):
        return "task2:%s" % id

    def monitor(self):
        print("monitor started")
        counter = 0
        while True:
            gevent.sleep(1)
            counter += 5
            print("monitor:%s:%s" % (self, counter))

    def ok(self):
        pass
