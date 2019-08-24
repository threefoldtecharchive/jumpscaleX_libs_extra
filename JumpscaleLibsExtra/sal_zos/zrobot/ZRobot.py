import time


class ZeroRobot:
    """
    Zero robot
    """

    def __init__(
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
        self.id = "zbot.{}".format(container.name)
        self.container = container
        self.port = port
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.template_repos = template_repos if template_repos else list()
        self.data_repo = data_repo or "/sandbox/code/zrobot"
        self.config_repo = config_repo or "/sandbox/code/zrobot/config"
        self.organization = organization
        self.config_key = config_key
        self.auto_push = auto_push
        self.auto_push_interval = auto_push_interval

    def start(self, timeout=120):
        if self.is_running():
            return

        container_client = self.container.client

        kwargs = {"port": self.port, "data": self.data_repo, "config": self.config_repo}
        cmd_line = "/usr/local/bin/zrobot server start --listen :{port} --data-repo {data} --config-repo {config}".format(
            **kwargs
        )

        if self.config_key:
            cmd_line += " --config-key %s" % self.config_key

        for template_repo in self.template_repos:
            cmd_line += " --template-repo %s" % template_repo

        if self.telegram_bot_token:
            cmd_line += " --telegram-bot-token %s" % self.telegram_bot_token

        if self.telegram_chat_id:
            cmd_line += " --telegram-chat-id %s" % self.telegram_chat_id

        if self.organization:
            cmd_line += " --organization %s" % self.organization

        if self.auto_push:
            cmd_line += " --auto-push"

        if self.auto_push_interval:
            cmd_line += " --auto-push-interval %s" % str(self.auto_push_interval)

        cmd = container_client.system(cmd_line, id=self.id)

        start = time.time()
        # need a long timeout cause it can take a long time to download all the file from the hub
        # this is python, lot's of small files
        while not self.container.is_port_listening(self.port, 300):
            if not self.is_running():
                result = cmd.get()
                raise j.exceptions.Base(
                    "Could not start 0-robot.\nstdout: %s\nstderr: %s" % (result.stdout, result.stderr)
                )
            if time.time() > start + timeout:
                container_client.job.kill(self.id, signal=9)
                result = cmd.get()
                raise j.exceptions.Base(
                    "Zero robot failed to start within %s seconds!\nstdout: %s\nstderr: %s",
                    (timeout, result.stdout, result.stdout),
                )

        self.container.node.client.nft.open_port(self.port)

    def is_running(self):
        return self.container.is_job_running(self.id)

    def stop(self, timeout=60):
        if not self.is_running():
            return

        self.container.client.job.kill(self.id)
        for _ in range(timeout):
            if not self.is_running():
                return
            time.sleep(1)
        self.container.client.job.kill(self.id, signal=9)

        self.container.node.client.nft.drop_port(self.port)
