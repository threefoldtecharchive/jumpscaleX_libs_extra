from Jumpscale import j

JSBASE = j.baseclasses.object


class ErrBotFactory(j.baseclasses.object):
    __jslocation__ = "j.servers.errbot"

    def start(self, reset=False):
        """
        kosmos 'j.servers.errbot.start(reset=True)'
        :return:
        """
        # if reset:
        #     self.cmd.stop()

        import logging

        logger = logging.Logger("installer")

        import sys

        sys.path.append("~/opt/var/build/python3/lib/python3.6/site-packages")

        import errbot
        from importlib import util

        path = "%s/config.py" % self._dirpath
        spec = util.spec_from_file_location("IT", path)
        config = spec.loader.load_module()

        from errbot import BotPlugin, botcmd

        class MyPlugin(BotPlugin):
            def activate(self):
                super().activate()  # <-- needs to be *before* get_plugin
                self.other = self.get_plugin("OtherPlugin1")

            @botcmd
            def hello(self, msg, args):
                return self.other.my_variable

        from errbot.bootstrap import bootstrap

        backend = config.BACKEND
        from errbot.logs import root_logger
        from errbot.plugin_wizard import new_plugin_wizard

        bootstrap(backend, root_logger, config)

        j.shell()
