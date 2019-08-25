from Jumpscale import j
from .webgateway import WebGateway


class WebGatewayFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.clients.webgateway"
    _CHILDCLASS = WebGateway
