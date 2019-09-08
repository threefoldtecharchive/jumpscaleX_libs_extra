"""
Jumpscale client module that define a client for electrum wallet
"""

from Jumpscale import j

from clients.blockchain.electrum.ElectrumWallet import ElectrumWallet
from clients.blockchain.electrum.ElectrumAtomicswap import ElectrumAtomicswap


JSConfigBase = j.baseclasses.object_config


class ElectrumClient(JSConfigBase):
    """
    Electrum client object
    """

    _SCHEMATEXT = """
        @url = jumpscale.electrum.client
        name** = "" (S)
        server = "localhost:7777" (S)
        rpc_user = "user" (S)
        rpc_pass_ = "pass" (S)
        seed_ = "" (S)
        fee = 10000 (I)
        password_ = "" (S)
        passphrase_ = "" (S)
        electrum_path = "" (S)
        testnet = 0 (I)
        """

    def _init(self, **kwargs):
        """
        Initializes new Rivine Client
        """
        self._wallet = None
        self._atomicswap = None

    @property
    def wallet(self):
        # access atomicswap to make sure the wallet is loaded
        # need to figure out a better wayt to do this using a call to the library
        self.atomicswap
        if self._wallet is None:
            config_data = {}
            for key, value in self.config.data.items():
                config_data[key.strip("_")] = value
            self._wallet = ElectrumWallet(name=self.instance, config=config_data)
        return self._wallet

    @property
    def atomicswap(self):
        """
        Atomicswap support for BTC electrum
        """
        if self._atomicswap is None:
            self._atomicswap = ElectrumAtomicswap(
                wallet_name=self.instance,
                data_dir=self.config.data["electrum_path"],
                rpcuser=self.config.data["rpc_user"],
                rpcpass=self.config.data["rpc_pass_"],
                rpchost=self.config.data["server"].split(":")[0],
                rpcport=self.config.data["server"].split(":")[1],
                testnet=self.config.data["testnet"],
            )
        return self._atomicswap
