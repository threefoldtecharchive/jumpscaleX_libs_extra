from .BootstrapBot import BootstrapBot, LAPIS_PORT
from Jumpscale import j

JSBASE = j.baseclasses.object


class BootstrapBotFactory(JSBASE):
    __jslocation__ = "j.sal_zos.bootstrapbot"

    @staticmethod
    def get(node, name, sendgrid_key, lapis_port=LAPIS_PORT):
        """
        Get sal for Bootstrap Bot
        Returns:
            the sal layer
        """
        return BootstrapBot(node=node, name=name, sendgrid_key=sendgrid_key, lapis_port=lapis_port)
