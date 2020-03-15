from Jumpscale import j
from .karkenClient import KrakenClient

JSConfigs = j.baseclasses.object_config_collection


class KrakenFactory(JSConfigs):
    _CHILDCLASS = KrakenClient
    # check https://github.com/threefoldtech/jumpscaleX_libs_extra/issues/7

    def install(self, reset=False):
        j.builders.runtimes.pip.install("pykrakenapi", reset=reset)
        j.builders.runtimes.pip.install("krakenex", reset=reset)
