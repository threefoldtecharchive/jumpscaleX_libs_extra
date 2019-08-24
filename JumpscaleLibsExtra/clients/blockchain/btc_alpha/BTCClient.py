from Jumpscale import j

import hmac
import requests
from time import time
from urllib.parse import urlencode


# TODO:*1 FROM CLIENT import .... and put in client property
# TODO:*1 regenerate using proper goraml new file & newest generation tools ! (had to fix manually quite some issues?)

JSConfigBase = j.baseclasses.object_config


class BTCClient(JSConfigBase):

    _SCHEMATEXT = """
    @url = jumpscale.btc.client
    name* = "" (S)
    service_url = "https://btc-alpha.com/api/" (S)
    key_ = "" (S)
    secret_ = "" (S)
    """

    def _init(self, **kwargs):
        if not self.key_ or not self.secret_:
            raise j.exceptions.Input("Need to specify both key and secret to use the client")

    def get_currencies(self):
        """ Returns all active currencies
        :return: array of currencies
        Example: [{'sign': 'Ƀ', 'short_name': 'BTC'}, {'sign': 'Ξ', 'short_name': 'ETH'}, ...]
        """
        return self._query("get", "v1/currencies/")

    def get_pairs(self, **kwargs):
        """ Returns all active pairs
        :param kwargs: Filters (Optional): currency1, currency2
        :return: pairs array
        Example: [{'currency2': 'USD', 'maximum_order_size': '100000000.00000000', 'minimum_order_size': '0.00000001',
                'currency1': 'BTC', 'name': 'BTC_USD', 'price_precision': 3}, ... ]
        """
        return self._query("get", "v1/pairs/", params=kwargs)

    def get_wallets(self, **kwargs):
        """ Returns own wallets
        :param kwargs: Filters (Optional): currency_id
        :return: wallets array
        Example: [{'currency': 'BTC', 'balance': '0.00000000', 'reserve': '0.00000000'}, ...]
        """
        return self._query("get", "v1/wallets/", params=kwargs, auth=True)

    def get_own_sell_orders(self, **kwargs):
        """ Returns own sell orders """
        kwargs["type"] = "sell"
        return self._query("get", "v1/orders/own/", params=kwargs, auth=True)

    def get_own_buy_orders(self, **kwargs):
        """ Returns own buy orders """
        kwargs["type"] = "buy"
        return self._query("get", "v1/orders/own/", params=kwargs, auth=True)

    def create_sell_order(self, pair, amount, price):
        """ Create sell order
        :param pair: Pair (BTC_USD,)
        :param amount: Amount of order - string
        :param price: Price of order - string
        :return: order info
        Example: {
        'type': 'buy', 'date': 1483721079.51632, 'oid': '11268', 'price': '870.69000000', 'amount': '0.00000000',
        'trades': [{'type': 'sell', 'price': '870.69000000', 'o_id': '11266', 'amount': '0.00010000', 'tid': '6049'}]
        }
        """
        data = {"pair": pair, "amount": amount, "price": price, "type": "sell"}
        return self._query("post", "v1/order/", data=data, auth=True)

    def create_buy_order(self, pair, amount, price):
        """ Create buy order """
        data = {"pair": pair, "amount": amount, "price": price, "type": "buy"}
        return self._query("post", "v1/order/", data=data, auth=True)

    def cancel_order(self, oid):
        """ Cancel order
        :param oid: id of order
        Example: {
            order: 63568
        }
        """
        data = {"order": oid}
        return self._query("post", "v1/order-cancel/", data=data, auth=True)

    def get_exchanges(self, **kwargs):
        """ Returns last exchanges
        :param kwargs: Filters (Optional): pair, limit
        :return: exchanges array
        Example: [{'id': 6030, 'price': '839.36000000', 'pair': 'BTC_USD', 'type': 1, 'timestamp': 1483705817.735508,
                'amount': '0.00281167'}, ....]
        """
        return self._query("get", "v1/exchanges/", params=kwargs)

    def get_own_exchanges(self, **kwargs):
        """ Returns only own exchanges
        :param kwargs: see get_exchanges()
        :return: see get_exchanges()
        """
        return self._query("get", "v1/exchanges/own/", params=kwargs, auth=True)

    def get_own_sell_exchanges(self, **kwargs):
        kwargs["type"] = "sell"
        return self._query("get", "v1/exchanges/own/", params=kwargs, auth=True)

    def get_own_buy_exchanges(self, **kwargs):
        kwargs["type"] = "buy"
        return self._query("get", "v1/exchanges/own/", params=kwargs, auth=True)

    def get_deposits(self):
        """ Returns all made deposits
        :return: deposits array
        Example [{'timestamp': 1485363039.18359, 'id': 317, 'currency': 'BTC', 'amount': '530.00000000'}, ... ]
        """
        return self._query("get", "v1/deposits/", auth=True)

    def get_withdraws(self, **kwargs):
        """ Returns all made withdraws
        :param kwargs: currency_id, status
        :return: withdraws array
        Example: [{'id': 403, 'timestamp': 1485363466.868539, 'currency': 'BTC', 'amount': '0.53000000', 'status': 20} ...]
        """

        return self._query("get", "v1/withdraws/", params=kwargs, auth=True)

    def get_orderbook(self, pair, **kwargs):
        """ Return sell and buy orders for specified pair
        :param kwargs: limit_bids, limit_asks, group
        :return: object {'bids': Array, 'asks': Array}
        Example: {
            'bids': [{'price': 911.519, 'id': 44667, 'amount': 0.000446, 'timestamp': 1485777324.410015}],
            'asks': [{'price': 911.122, 'id': 44647, 'amount': 0.001233, 'timestamp': 1485777124.415542}]
        }
        """

        return self._query("get", "v1/orderbook/{}/".format(pair), params=kwargs)

    def get_charts(self, pair, type, **kwargs):
        """ Return data for chart candles
        :param pair: Pair name
        :param type: Type of candles ('1','5','15','30','60','240','D')
        :param kwargs: since, until, limit
        :return: array of bars
        Example [
            {'volume': 0.262929, 'high': 912.236, 'low': 910.086, 'close': 911.915, 'time': 1485777600, 'open': 910.424},
            {'volume': 2.16483814, 'high': 911.519, 'low': 909.432, 'close': 910.424, 'time': 1485774000, 'open': 909.433}
        ]
        """
        return self._query("get", "charts/{}/{}/chart".format(pair, type), params=kwargs)

    def _query(self, method, base_url, params=None, data=None, auth=False):
        request_conf = {"method": method, "url": self.service_url + base_url, "allow_redirects": True}

        if params:
            request_conf["url"] += "?" + urlencode(params)

        if data:
            request_conf["data"] = data

        if auth:
            request_conf["headers"] = self._get_headers(data or {})

        response = requests.request(**request_conf)

        if 300 > response.status_code >= 200:
            return response.json()
        else:
            raise j.exceptions.Value("Http status {} - {}".format(response.status_code, response.content))

    def _get_headers(self, data):
        msg = self.key_ + urlencode(sorted(data.items(), key=lambda val: val[0]))

        sign = hmac.new(self.secret_.encode(), msg.encode(), digestmod="sha256").hexdigest()

        return {"X-KEY": self.key_, "X-SIGN": sign, "X-NONCE": str(int(time() * 1000))}
