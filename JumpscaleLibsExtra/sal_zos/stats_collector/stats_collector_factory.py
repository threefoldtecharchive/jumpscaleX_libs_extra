from .stats_collector import StatsCollector
from Jumpscale import j

JSBASE = j.baseclasses.object


class StatsCollectorFactory(JSBASE):
    __jslocation__ = "j.sal_zos.stats_collector"

    @staticmethod
    def get(container, ip, port, db, retention, jwt):
        """
        Get sal for Disks
        Returns:
            the sal layer
        """
        return StatsCollector(container, ip, port, db, retention, jwt)
