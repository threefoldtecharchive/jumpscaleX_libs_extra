from Jumpscale import j

JSConfigs = j.baseclasses.object_config_collection

from .BTCClient import BTCClient


class GitHubFactory(JSConfigs):

    __jslocation__ = "j.clients.btc_alpha"
    _CHILDCLASS = BTCClient

    def test(self):
        # will be manual. for security reasons.
        # connect to btc api
        # do some operations and stuff
        # make sure connection is working
        pass
