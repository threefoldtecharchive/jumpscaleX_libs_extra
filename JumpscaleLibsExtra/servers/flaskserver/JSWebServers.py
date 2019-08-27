from Jumpscale import j
from .JSWebServer import JSWebServer

JSConfigBase = j.baseclasses.object_config_collection


class JSWebServers(JSConfigBase):
    __jslocation__ = "j.servers.flask"

    def _init(self, **kwargs):
        self.latest = None

    def get(self, port):
        """
        will return server which can be attached in a gevent_servers_rack
        """
        return JSWebServer(port=port)

    def install(self):
        """
        kosmos 'j.servers.web.install()'

        """
        pips = """
        flask
        flask_login
        flask_migrate
        # flask_wtf
        # flask_sqlalchemy
        # gunicorn
        gevent
        """
        p = j.tools.prefab.local
        p.runtimes.pip.install(pips)

        # will make sure we have the lobs here for web
        j.clients.git.getContentPathFromURLorPath("https://github.com/threefoldtech/jumpscale_weblibs")

    def start(self, instance="main", background=False, debug=False):

        # start redis
        print("make sure core redis running")
        j.clients.redis.core_check()

        s = self.get(instance)

        if not background:
            s.start(debug=debug)
        else:
            # start
            cmd = """
            export LC_ALL=de_DE.utf-8
            export LANG=de_DE.utf-8
            export FLASK_DEBUG=1
            export APP_SETTINGS=project.server.config.DevelopmentConfig
            js_web start -i $instance -d
            """
            cmd = cmd.replace("$instance", instance)
            j.servers.tmux.execute(
                cmd, session="main", window=instance, pane="main", session_reset=False, window_reset=True
            )

            host = s.config.data["host"]
            port = s.config.data["port"]
            print("webserver running on http://%s:%s/" % (host, port))

    def test(self, name="", start=True):
        """
        following will run all tests

        kosmos 'j.servers.web.test()'

        """

        self._test_run(name=name)
