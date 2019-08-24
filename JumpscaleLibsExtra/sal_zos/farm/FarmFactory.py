from Jumpscale import j

JSBASE = j.baseclasses.object

from .Farm import Farm


class FarmFactory(JSBASE):

    __jslocation__ = "j.sal_zos.farm"

    def get(self, farmer_iyo_org):
        """
        Get sal for farm

        Arguments:
            farmer_iyo_org: the farmer iyo organisation

        Returns:
            the sal layer
        """
        return Farm(farmer_iyo_org)
