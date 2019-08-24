from Jumpscale import j
from .karkenClient import KrakenClient

JSConfigs = j.baseclasses.objects_config_bcdb


class KrakenFactory(JSConfigs):
    __jslocation__ = "j.clients.kraken"
    _CHILDCLASS = KrakenClient

    def install(self, reset=False):
        j.builders.runtimes.pip.install("pykrakenapi", reset=reset)
        j.builders.runtimes.pip.install("krakenex", reset=reset)
