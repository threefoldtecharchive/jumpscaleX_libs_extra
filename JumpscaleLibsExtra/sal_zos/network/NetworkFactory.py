from .Network import Network
from jumpscale import j

JSBASE = j.application.jsbase_get_class()


class NetworkFactory(JSBASE):
    __jslocation__ = "j.sal_zos.network"

    @staticmethod
    def get(node):
        """
        Get sal for Network
        Returns:
            the sal layer 
        """
        return Network(node)
