from Jumpscale import j
from .Rogerthat import Rogerthat

JSConfigs = j.baseclasses.objects_config_bcdb


class RogerthatFactory(JSConfigs):
    __jslocation__ = "j.clients.rogerthat"
    _CHILDCLASS = Rogerthat
