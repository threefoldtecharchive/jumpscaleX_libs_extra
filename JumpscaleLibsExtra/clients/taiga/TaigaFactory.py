from Jumpscale import j

try:
    from taiga import TaigaAPI
except ImportError:
    j.builders.runtimes.python3.pip_package_install("python-taiga")
from .TaigaClient import TaigaClient

JSConfigs = j.baseclasses.object_config_collection


class TaigaFactory(JSConfigs):
    # check https://github.com/threefoldtech/jumpscaleX_libs_extra/issues/7
    _CHILDCLASS = TaigaClient
    __jslocation__ = "j.clients.taiga"

    def install(self):
        j.builders.runtimes.python3.pip_package_install("python-taiga")
