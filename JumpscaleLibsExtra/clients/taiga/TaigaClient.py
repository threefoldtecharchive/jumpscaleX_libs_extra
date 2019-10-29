from Jumpscale import j
from taiga import TaigaAPI

JSConfigClient = j.baseclasses.object_config


class TaigaClient(JSConfigClient):
    _SCHEMATEXT = """
        @url = jumpscale.taiga.clients
        name** = "" (S)
        username = "" (S)
        password_ = "" (S)
        token_ = "" (S)
        host = "https://projects.threefold.me"
        """

    def _init(self, **kwargs):
        self.api = TaigaAPI(host=self.host)
        if self.token_:
            self.api.token = self.token_
        else:
            if not self.username or not self.password_:
                raise RuntimeError("username and password are required")
            self.api.auth(self.username, self.password_)
