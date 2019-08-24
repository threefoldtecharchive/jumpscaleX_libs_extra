from Jumpscale import j
import krakenex
from pykrakenapi import KrakenAPI

JSConfigClient = j.baseclasses.object_config


class KrakenClient(JSConfigClient):
    _SCHEMATEXT = """
        @url = jumpscale.kraken.clients
        name* = "" (S)
        api_key_ = "" (S)
        private_key_ = "" (S)
        """

    def _init(self, **kwargs):
        kraken_api = krakenex.API()
        kraken_api.key = self.api_key_
        kraken_api.secret = self.private_key_
        self.api = KrakenAPI(kraken_api)

    def test(self):

        k = self.api
        self._log_debug("open orders")
        self._log_debug(k.get_open_orders())

        self._log_debug("get account balance")
        self._log_debug(k.get_account_balance())
