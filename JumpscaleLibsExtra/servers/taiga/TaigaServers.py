from Jumpscale import j
from .TaigaServer import TaigaServer


class TaigaServers(j.baseclasses.object_config_collection_testtools):
    """
    Taiga Server factory
    """

    __jslocation__ = "j.servers.taiga"
    _CHILDCLASS = TaigaServer

    def _init(self, **kwargs):
        self._default = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get(name="default")
        return self._default
