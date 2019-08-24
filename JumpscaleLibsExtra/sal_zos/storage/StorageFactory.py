from Jumpscale import j

JSBASE = j.baseclasses.object

from .StoragePool import StoragePools


class ContainerFactory(JSBASE):
    __jslocation__ = "j.sal_zos.storagepools"

    def get(self, node):
        """
        Get sal for storage pools

        Arguments:
            node

        Returns:
            the sal layer
        """
        return StoragePools(node)
