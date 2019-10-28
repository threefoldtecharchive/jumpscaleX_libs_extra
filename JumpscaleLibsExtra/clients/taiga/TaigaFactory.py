from Jumpscale import j
from .TaigaClient import TaigaClient

JSConfigs = j.baseclasses.object_config_collection


class TaigaFactory(JSConfigs):
    __jslocation__ = "j.clients.taiga"
    _CHILDCLASS = TaigaClient

    def install(self, reset=False):
        j.builders.runtimes.pip.install("python-taiga", reset=reset)
