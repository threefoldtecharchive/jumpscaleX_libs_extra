from .Disks import Disks
from Jumpscale import j

JSBASE = j.baseclasses.object


class DisksFactory(JSBASE):
    __jslocation__ = "j.sal_zos.disks"

    @staticmethod
    def get(node):
        """
        Get sal for Disks
        Returns:
            the sal layer 
        """
        return Disks(node)
