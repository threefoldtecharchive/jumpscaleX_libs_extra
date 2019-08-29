from Jumpscale import j

# import Jumpscale.baselib.remote

JSBASE = j.baseclasses.object

from .grafana import Grafana


class GrafanaFactory(JSBASE):
    __jslocation__ = "j.sal_zos.grafana"

    def get(self, container, ip, port, url):
        """
        Get sal for Grafana
        
        Returns:
            the sal layer 
        """
        return Grafana(container, ip, port, url)
