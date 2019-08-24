from Jumpscale import j
from .Request import Request
from .API import UserAPI, SpaceAPI, WikiAPI, CommentApi, LikeAPI, PostAPI
from .Country import Country

JSConfigClient = j.baseclasses.object_config


class FreeFlowClient(JSConfigClient):
    _SCHEMATEXT = """
        @url = jumpscale.freeflow.client
        name* = "" (S)
        base_url = "" (S)
        api_key = "" (S)
    """

    def test(self):
        return "PONG"

    @property
    def request(self):
        if not hasattr(self, "_request"):
            self._request = Request(self.base_url, self.api_key)
        return self._request

    @property
    def users(self):
        return UserAPI(self.request)

    @property
    def comments(self):
        return CommentApi(self.request)

    @property
    def users(self):
        return UserAPI(self.request)

    @property
    def spaces(self):
        return SpaceAPI(self.request)

    @property
    def likes(self):
        return LikeAPI(self.request)

    @property
    def posts(self):
        return PostAPI(self.request)

    @property
    def wikis(self):
        return WikiAPI(self.request)

    @property
    def countries(self):
        return Country.COUNTRIES.keys()
