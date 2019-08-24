from Jumpscale import j

# import Jumpscale.baselib.remote

JSBASE = j.baseclasses.object

from .influxdb import InfluxDB


class InfluxDBFactory(JSBASE):
    __jslocation__ = "j.sal_zos.influx"

    def get(self, container, ip, port, rpcport):
        """
        Get sal for InfluxDB
        
        Arguments:
            container, ip, port, rpcport
        
        Returns:
            the sal layer 
        """
        return InfluxDB(container, ip, port, rpcport)
