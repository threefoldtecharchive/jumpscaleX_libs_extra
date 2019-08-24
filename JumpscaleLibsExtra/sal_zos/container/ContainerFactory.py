from Jumpscale import j

JSBASE = j.baseclasses.object

from .Container import Containers


class ContainerFactory(JSBASE):

    __jslocation__ = "j.sal_zos.containers"

    def get(self, node):
        """
        Get sal for VM management in ZOS
        
        Arguments:
            node
        
        Returns:
            the sal layer 
        """
        return Containers(node)
