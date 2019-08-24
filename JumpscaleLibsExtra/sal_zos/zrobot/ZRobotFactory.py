from .ZRobot import ZeroRobot
from Jumpscale import j

JSBASE = j.baseclasses.object


class ZeroRobotFactory(JSBASE):
    __jslocation__ = "j.sal_zos.zrobot"

    def get(
        self,
        container,
        port=6600,
        telegram_bot_token=None,
        telegram_chat_id=0,
        template_repos=None,
        data_repo=None,
        config_repo=None,
        config_key=None,
        organization=None,
        auto_push=None,
        auto_push_interval=None,
    ):
        """
        Get sal for ZeroRobot in ZOS
        Returns:
            the sal layer
        """
        return ZeroRobot(
            container,
            port=port,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            template_repos=template_repos,
            data_repo=data_repo,
            config_repo=config_repo,
            config_key=config_key,
            organization=organization,
            auto_push=auto_push,
            auto_push_interval=auto_push_interval,
        )
