from .ZOS_VM import ZOS_VM


class ZOS_VMFactory(JSBASE):
    __jslocation__ = "j.sal_zos.vm"

    @staticmethod
    def get(node, name, flist=None, vcpus=2, memory=2048):
        """
        Get sal for VM management in ZOS

        Returns:
            the sal layer
        """
        return ZOS_VM(node, name, flist, vcpus, memory)
