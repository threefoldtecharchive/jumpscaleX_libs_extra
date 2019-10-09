from Jumpscale import j
from .TFGateway import TFGateway

JSBASE = j.baseclasses.object


class TFGatewayFactory(JSBASE):
    __jslocation__ = "j.tools.tf_gateway"

    def get(self, redisclient):
        if not redisclient:
            raise j.exceptions.Input("Require redis client")
        return TFGateway(redisclient)
