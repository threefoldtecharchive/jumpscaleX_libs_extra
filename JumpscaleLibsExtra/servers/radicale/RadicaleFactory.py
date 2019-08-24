from Jumpscale import j
from .RadicaleServer import RadicaleServer

JSConfigs = j.baseclasses.objects_config_bcdb


class RadicaleFactory(JSConfigs):
    __jslocation__ = "j.servers.radicale"
    _CHILDCLASS = RadicaleServer

    def __init__(self):
        JSConfigs.__init__(self)
        self._default = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get("default")
        return self._default
