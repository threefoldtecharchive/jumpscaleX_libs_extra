from Jumpscale import j
from .webgateway import WebGateway


class WebGatewayFactory(j.baseclasses.factory):
    __jslocation__ = "j.clients.webgateway"
    _CHILDCLASS = WebGateway
