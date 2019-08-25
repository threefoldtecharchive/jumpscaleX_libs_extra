from Jumpscale import j
from .Rogerthat import Rogerthat

JSConfigs = j.baseclasses.factory


class RogerthatFactory(JSConfigs):
    __jslocation__ = "j.clients.rogerthat"
    _CHILDCLASS = Rogerthat
