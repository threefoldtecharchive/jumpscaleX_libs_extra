from .Traefik import Traefik
from Jumpscale import j

JSBASE = j.baseclasses.object


class TraefikFactory(JSBASE):
    __jslocation__ = "j.sal_zos.traefik"

    def get(self, name, node, etcd_endpoint, etcd_password, etcd_watch=True, zt_identity=None, nics=None):
        """
        Get sal for traefik
        Returns:
            the sal layer
        """
        return Traefik(name, node, etcd_endpoint, etcd_password, etcd_watch, zt_identity, nics)
