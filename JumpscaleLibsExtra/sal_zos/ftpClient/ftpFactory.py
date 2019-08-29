from Jumpscale import j

# import Jumpscale.baselib.remote

JSBASE = j.baseclasses.object

from .FtpClient import FtpClient


class FtpFactory(JSBASE):
    __jslocation__ = "j.sal_zos.ftpclient"

    def get(self, url):
        """
        Get sal for FtpClient
        
        Arguments:
            url
        
        Returns:
            the sal layer 
        """
        return FtpClient(url)
