from Jumpscale import j
from .RacktivityClient import RacktivityClient

JSConfigs = j.baseclasses.objects_config_bcdb


class RacktivityFactory(JSConfigs):
    __jslocation__ = "j.clients.racktivity"
    _CHILDCLASS = RacktivityClient
