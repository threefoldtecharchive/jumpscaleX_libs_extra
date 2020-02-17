"""
Client factory for electrum wallet
"""

from Jumpscale import j

from electrum.commands import Commands
from .ElectrumClient import ElectrumClient

JSConfigBaseFactory = j.baseclasses.object_config_collection


class ElectrumClientFactory(JSConfigBaseFactory):
    """
    Factroy class to get a electrum client object
    """

    # check https://github.com/threefoldtech/jumpscaleX_libs_extra/issues/8
    _CHILDCLASS = ElectrumClient

    def _init(self, **kwargs):
        self.__imports__ = "electrum"

    def generate_seed(self, nbits=132):
        """
        Creates a new seed

        @param nbits: Number of bits for creating the seed default is 132 which will generate a 12 words seed
        """
        cmd = Commands(None, None, None)
        return cmd.make_seed(nbits=nbits)

    def create_wallet(self, name, network, seed, data_path, rpc_server, rpc_user, rpc_pass, password="", passphrase=""):
        """
        Creates a new BTC electrum wallet
        If a wallet with the same name exit, an excveption is raised
        """
        if name in self.list():
            raise j.exceptions.Value(
                "A wallet with name {} already exist. Please use open_wallet to open an existing wallet".format(name)
            )
        data = {
            "testnet": network == "TESTNET",
            "seed_": seed,
            "electrum_path": data_path,
            "server": "{}:s".format(rpc_server.replace(":s", "")),
            "rpc_user": rpc_user,
            "rpc_pass_": rpc_pass,
            "password_": password,
            "passphrase_": passphrase,
        }
        electrum_cl = self.get(instance=name, data=data)
        electrum_cl.config.save()
        self._load_wallet(electrum_cl.wallet)
        return electrum_cl.wallet

    def open_wallet(self, name):
        """
        Open an existing wallet
        Will raise an exception if wallet doesnt exist
        """
        if name not in self.list():
            raise j.exceptions.Value(
                "A wallet with name {} doesn not exist. Please use create_wallet to create new wallet".format(name)
            )
        wallet = self.get(name, create=False, interactive=False).wallet
        self._load_wallet(wallet)
        return wallet

    def _load_wallet(self, wallet):
        """
        Loads an existing wallet into electrum daemon
        """
        cmd = "electrum{} -D {} -w {} daemon load_wallet".format(
            " --testnet" if wallet._config["testnet"] else "", wallet._config["electrum_path"], wallet._wallet_path
        )

        self._log_info("Loading wallet {} using command: {}".format(wallet._name, cmd))
        j.tools.prefab.local.core.run(cmd)
