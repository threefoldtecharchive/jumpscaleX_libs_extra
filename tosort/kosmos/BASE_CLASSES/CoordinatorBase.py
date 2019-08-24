from Jumpscale import j


class CoordinatorBase(j.application.JSFactoryConfigsBaseClass):
    def __init__(self):
        j.application.JSFactoryConfigsBaseClass.__init__(self)
        self.services = {}
        self._name = self.__jslocation__.replace("j.world.", "")

    # def _service_action_ask(self,instance,name):
    #     cmd = [name,arg]
    #     self.q_in.put(cmd)
    #     rc,res = self.q_out.get()
    #     return rc,res

    # @property
    # def name(self):
    #     return self.data.name
    #
    # @property
    # def key(self):
    #     if self._key == None:
    #         self._key = "%s"%(j.core.text.strip_to_ascii_dense(self.name))
    #     return self._key

    def __str__(self):
        return "coordinator:%s" % self._name
