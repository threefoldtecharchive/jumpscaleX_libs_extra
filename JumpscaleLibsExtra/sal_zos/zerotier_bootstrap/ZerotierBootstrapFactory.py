from Jumpscale import j

JSBASE = j.baseclasses.object

from .ZerotierBootstrap import ZTBootstrap


class ZerotierBootstrapFactory(JSBASE):
    __jslocation__ = "j.sal_zos.zt_bootstrap"

    def get(self, zt_token, bootstap_id, grid_id, cidr):
        """
        Get sal for zerotier bootstrap in ZOS
        Returns:
            the sal layer
        """
        return ZTBootstrap(zt_token, bootstap_id, grid_id, cidr)
