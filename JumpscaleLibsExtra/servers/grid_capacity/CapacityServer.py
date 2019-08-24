from Jumpscale import j
from .server import settings

TEMPLATE = """
host = "localhost"
port = 9900
debug = false
iyo_clientid = ""
iyo_secret = ""
iyo_callback = ""
"""
JSConfigBase = j.baseclasses.object


class CapacityServer(JSConfigBase):
    def __init__(self, instance, data={}, parent=None, interactive=False, template=None):
        JSConfigBase.__init__(
            self, instance=instance, data=data, parent=parent, template=TEMPLATE, interactive=interactive
        )
        settings.HOST = self.config.data["host"]
        settings.PORT = self.config.data["port"]
        settings.DEBUG = self.config.data["debug"]
        settings.IYO_CLIENTID = self.config.data["iyo_clientid"]
        settings.IYO_SECRET = self.config.data["iyo_secret"]
        settings.IYO_CALLBACK = self.config.data["iyo_callback"]
        from .server.app import app

        self.app = app

    def start(self):
        self.app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
