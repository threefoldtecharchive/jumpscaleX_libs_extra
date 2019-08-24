from Jumpscale import j

# import Jumpscale.baselib.remote

JSBASE = j.baseclasses.object

from ..gateway.gateway import Gateway


class GatewayFactory(JSBASE):
    __jslocation__ = "j.sal_zos.gateway"

    def get(self, node, name):
        """
        Get sal for Gateway
        
        Arguments:
            node
            name
        
        Returns:
            the sal layer 
        """
        return Gateway(node, name)
