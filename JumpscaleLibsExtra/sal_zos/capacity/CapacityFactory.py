from Jumpscale import j

# import Jumpscale.baselib.remote

JSBASE = j.baseclasses.object

from .Capacity import Capacity


class CapacityFactory(JSBASE):

    __jslocation__ = "j.sal_zos.capacity"

    def get(self, node):
        """
        Get sal for Capacity
        
        Arguments:
            node
        
        Returns:
            the sal layer 
        """
        return Capacity(node)
