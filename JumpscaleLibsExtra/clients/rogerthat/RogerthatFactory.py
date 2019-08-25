from Jumpscale import j
from .Rogerthat import Rogerthat

JSConfigs = j.baseclasses.object_config_collection


class RogerthatFactory(JSConfigs):
    __jslocation__ = "j.clients.rogerthat"
    _CHILDCLASS = Rogerthat
