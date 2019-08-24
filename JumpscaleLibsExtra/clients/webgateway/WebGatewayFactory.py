from Jumpscale import j
from .webgateway import WebGateway


class WebGatewayFactory(j.baseclasses.objects_config_bcdb):
    __jslocation__ = "j.clients.webgateway"
    _CHILDCLASS = WebGateway
