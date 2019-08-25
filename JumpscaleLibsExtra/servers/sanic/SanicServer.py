from Jumpscale import j
import os

JSConfigClient = j.baseclasses.object_config


class SanicServer(JSConfigClient):
    _SCHEMATEXT = """
           @url =  jumpscale.sanic.server.1
           name* = "default" (S)
           host = "127.0.0.1" (S)
           port = 8001 (I)
           default_path = "" (S)
           """

    def _init(self, **kwargs):
        self._default_client = None
        self.path = os.path.dirname(os.path.abspath(__file__))
        print(self.path)

    @property
    def startupcmd(self):
        if not self.default_path:
            self.default_path = "{}/server_app.py".format(self.path)
        cmd = "python3 {}".format(self.default_path)
        raise RuntimeError("need to load from other location")
        cmd_gedis = """kosmos '\
        server = j.servers.gedis.configure(host="0.0.0.0", port=8888);\
        server.actor_add("/sandbox/code/github/threefoldtech/digitalmeX/DigitalMe/tools/graphql_tutorial/graphql_actor.py");\
        server.save();\
        server.start();'
        """
        return [
            j.servers.startupcmd.get(name="gedis", cmd_start=cmd_gedis),
            j.servers.startupcmd.get(name="Sanic", cmd_start=cmd),
        ]

    def start(self):
        """
        Starts sanic server in tmux
        """
        for cmd in self.startupcmd:
            cmd.start()

    def stop(self):
        """
        Stops sanic server in tmux
        """
        for cmd in self.startupcmd:
            cmd.stop()

    def install(self, reset=True):
        """
        kosmos 'j.servers.sanic.install()'
        """
        j.builders.apps.sanic.install(reset=reset)
