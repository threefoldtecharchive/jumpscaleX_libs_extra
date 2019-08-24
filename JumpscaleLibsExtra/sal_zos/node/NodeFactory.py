from .Node import Node
from Jumpscale import j

JSBASE = j.baseclasses.object


class PrimitivesFactory(JSBASE):
    __jslocation__ = "j.sal_zos.node"

    @staticmethod
    def get(client):
        """
        Get sal for zos node
        Returns:
            the sal layer
        """
        return Node(client)
