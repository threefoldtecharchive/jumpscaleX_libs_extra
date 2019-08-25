from Jumpscale import j
from .RacktivityClient import RacktivityClient

JSConfigs = j.baseclasses.object_config_collection


class RacktivityFactory(JSConfigs):
    __jslocation__ = "j.clients.racktivity"
    _CHILDCLASS = RacktivityClient
