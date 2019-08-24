from .UserBot import UserBot, GEDIS_PORT, LAPIS_PORT
from Jumpscale import j

JSBASE = j.baseclasses.object


class UserBotFactory(JSBASE):
    __jslocation__ = "j.sal_zos.userbot"

    @staticmethod
    def get(node, name, bootstrap_token, gedis_port=GEDIS_PORT, lapis_port=LAPIS_PORT):
        """
        Get sal for UserBot
        Returns:
            the sal layer
        """
        return UserBot(
            node=node, name=name, bootstrap_token=bootstrap_token, gedis_port=gedis_port, lapis_port=lapis_port
        )
