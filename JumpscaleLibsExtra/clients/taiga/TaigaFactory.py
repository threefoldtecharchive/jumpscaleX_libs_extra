from Jumpscale import j
from .TaigaClient import TaigaClient

JSConfigs = j.baseclasses.object_config_collection


class TaigaFactory(JSConfigs):
    # check https://github.com/threefoldtech/jumpscaleX_libs_extra/issues/7
    _CHILDCLASS = TaigaClient

    def install(self, reset=False):
        j.builders.runtimes.pip.install("python-taiga", reset=reset)
