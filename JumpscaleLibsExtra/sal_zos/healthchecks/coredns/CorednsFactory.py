from .CoreDns import Coredns
from Jumpscale import j

JSBASE = j.baseclasses.object


class CorednsFactory(JSBASE):
    __jslocation__ = "j.sal_zos.coredns"

    def get(
        self, name, node, etcd_endpoint, etcd_password, zt_identity=None, nics=None, backplane="backplane", domain=None
    ):
        """
        Get sal for coredns
        Returns:
            the sal layer
        """
        return Coredns(name, node, etcd_endpoint, etcd_password, zt_identity, nics, backplane, domain)
