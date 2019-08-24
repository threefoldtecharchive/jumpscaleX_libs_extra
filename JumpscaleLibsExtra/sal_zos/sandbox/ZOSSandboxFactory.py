from Jumpscale import j

# import Jumpscale.baselib.remote

JSBASE = j.baseclasses.object


class ZOSSandboxFactory(JSBASE):
    __jslocation__ = "j.sal_zos.sandbox"

    def get(self, data={}):
        """
        Get sal for influxdb
        
        Arguments:
            object using jumpscale schema
        
        Returns:
            the sal layer 
        """
        return data
