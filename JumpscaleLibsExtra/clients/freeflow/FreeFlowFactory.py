from Jumpscale import j
from .FreeFlowClient import FreeFlowClient

JSConfigs = j.baseclasses.objects_config_bcdb


class FreeFlowFactory(JSConfigs):
    __jslocation__ = "j.clients.freeflowpages"
    _CHILDCLASS = FreeFlowClient
