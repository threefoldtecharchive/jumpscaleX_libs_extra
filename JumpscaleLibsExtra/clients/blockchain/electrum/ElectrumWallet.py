"""
Jumpscale module provides an electrum wallet functionalities
"""

import os
import inspect
from electrum import daemon
from electrum import keystore
from electrum import constants
from electrum.wallet import Wallet
from electrum.network import Network
from electrum.commands import Commands
from electrum.storage import WalletStorage
from electrum.simple_config import SimpleConfig

EXECLUDED_COMMANDS = ["create", "commands", "restore", "dumpprivkeys"]


class ElectrumWallet:
    """
    An Electrum wallet wrapper
    """

    def __init__(self, name, config):
        """
        Initializes new electrum wallet instance

        @param name: Name of the wallet
        @param config: Configuration dictionary e.g {
            'server': 'localhost:7777:s',
            'rpc_user': 'user',
            'rpc_pass_': 'pass',
            'electrum_path': '/opt/var/data/electrum',
            'seed': '....',
            'fee': 10000,
            'testnet': 1
        }
        """
        self._name = name
        self._config = config
        self._config["testnet"] = bool(self._config["testnet"])
        if self._config["testnet"] is True:
            constants.set_testnet()

        self._config["verbos"] = False
        self._electrum_config = SimpleConfig(self._config)
        self._wallet_path = os.path.join(self._electrum_config.path, "wallets", self._name)
        self._storage = WalletStorage(path=self._wallet_path)
        if not self._storage.file_exists():
            self._electrum_config.set_key("default_wallet_path", self._wallet_path)
            k = keystore.from_seed(self._config["seed"], self._config["passphrase"], False)
            k.update_password(None, self._config["password"])
            self._storage.put("keystore", k.dump())
            self._storage.put("wallet_type", "standard")
            self._storage.put("use_encryption", bool(self._config["password"]))
            self._storage.write()
            self._wallet = Wallet(self._storage)
            # self._server = daemon.get_server(self._electrum_config)
            self._network = Network(self._electrum_config)
            self._network.start()
            self._wallet.start_threads(self._network)
            self._wallet.synchronize()
            self._wallet.wait_until_synchronized()
            self._wallet.stop_threads()
            self._wallet.storage.write()
        else:
            self._network = None
            self._wallet = self._wallet = Wallet(self._storage)

        self._commands = Commands(config=self._electrum_config, wallet=self._wallet, network=self._network)

        self._init_commands()

    def _init_commands(self):
        """
        Scans the electrum commands class and binds all its methods to this class
        """
        execlude_cmd = lambda item: (not item[0].startswith("_")) and item[0] not in EXECLUDED_COMMANDS
        for name, func in filter(execlude_cmd, inspect.getmembers(self._commands, inspect.ismethod)):
            setattr(self, name, func)
