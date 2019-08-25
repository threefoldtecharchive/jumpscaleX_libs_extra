from Jumpscale import j
from .PortalClient import PortalClient

JSConfigs = j.baseclasses.object_config_collection


class PortalClientFactory(JSConfigs):
    __jslocation__ = "j.clients.portal"
    _CHILDCLASS = PortalClient

    def _init(self, **kwargs):
        self._portalClients = {}
