from Jumpscale import j
from .SanicServer import SanicServer

JSConfigs = j.baseclasses.object_config_collection


class SanicFactory(JSConfigs):

    __jslocation__ = "j.servers.sanic"
    _CHILDCLASS = SanicServer

    def __init__(self):
        JSConfigs.__init__(self)
        self._default = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get("default")
        return self._default
