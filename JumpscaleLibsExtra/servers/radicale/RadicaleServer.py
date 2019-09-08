from gevent.monkey import patch_all

patch_all()
from Jumpscale import j
from gevent.pywsgi import WSGIServer

from radicale import application

JSConfigClient = j.baseclasses.object_config


class RadicaleServer(JSConfigClient):
    _SCHEMATEXT = """
       @url =  jumpscale.servers.radicale
       name** = "default" (S)
       port = 11000 (I)
               """

    def install(self):
        """
        kosmos 'j.servers.gundb.install()'

        :return:
        """
        # j.builders.runtimes.python3.pip_package_install("radicale")
        pass

    def start(self, name="radicale", background=False):
        """
        kosmos 'j.servers.webdav.start()'

        :param manual means the server is run manually using e.g. kosmos 'j.servers.rack.start(background=True)'

        """
        if not background:
            self.install()

            rack = j.servers.rack.get()
            server = WSGIServer(("0.0.0.0", self.port), application)
            rack.add(name=name, server=server)
            rack.start()

    def test(self):
        self.install(reset=reset)
        self.default.start()
        self.default.stop()
