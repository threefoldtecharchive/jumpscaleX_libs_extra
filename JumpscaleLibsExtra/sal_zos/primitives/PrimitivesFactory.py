from .Primitives import Primitives
from jumpscale import j

JSBASE = j.application.jsbase_get_class()


class PrimitivesFactory(JSBASE):
    __jslocation__ = "j.sal_zos.primitives"

    @staticmethod
    def get(node):
        """
        Get sal for zos primitives
        Returns:
            the sal layer 
        """
        return Primitives(node)
