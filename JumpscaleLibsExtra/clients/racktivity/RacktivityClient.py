from Jumpscale import j
from .energyswitch.client import RackSal

JSConfigClient = j.baseclasses.object_config

TEMPLATE = """
username = ""
password_ = ""
hostname = "127.0.0.1"
port = 80
"""


class RacktivityClient(JSConfigClient, RackSal):
    _SCHEMATEXT = """
    @url = jumpscale.racktivity.client
    name* ="" (S)
    username = "" (S)
    password_ = "" (S)
    hostname = "127.0.0.1" (S)
    port = 80 (ipport)
    """

    def _init(self, **kwargs):
        RackSal.__init__(self, self.username, self.password_, self.hostname, self.port, rtf=None, moduleinfo=None)
