"""
Electrum module to implement atomicswap support
"""
from Jumpscale import j
import json


class ElectrumAtomicswap:
    """
    ElectrumAtomicswap class
    This class wraps the binaries provided by https://github.com/rivine/atomicswap/releases
    """

    def __init__(self, wallet_name, data_dir, rpcuser, rpcpass, rpchost="localhost", rpcport=7777, testnet=False):
        """
        Initialize ElectrumAtomicswap object
        """
        self._prefab = j.tools.prefab.local
        self._wallet_name = wallet_name
        self._data_dir = data_dir
        self._rpcuser = rpcuser
        self._rpcpass = rpcpass
        self._host = "{}:{}".format(rpchost, rpcport)
        self._testnet = testnet
        self._wallet_path = j.sal.fs.joinPaths(data_dir, "testnet" if testnet else "mainnet", "wallets", wallet_name)
        self._load_wallet()

    def _load_wallet(self):
        """
        Loads the wallet
        """
        cmd = "electrum{} -D {} -w {} daemon load_wallet".format(
            " --testnet" if self._testnet else "", self._data_dir, self._wallet_path
        )

        self._log_info("Loading wallet {} using command: {}".format(self._wallet_name, cmd))
        self._prefab.core.run(cmd)

    def initiate(self, participant_address, amount):
        """
        Initialize a new atomicswap contract

        @param participant_address: Address of the participant of the contract
        @param amount: Amount in BTC to send to participant

        @returns:
            a dict with the contract details
        """
        cmd = 'btcatomicswap{} -automated --rpcuser={} --rpcpass={} -s "{}" initiate {} {}'.format(
            " -testnet" if self._testnet else "", self._rpcuser, self._rpcpass, self._host, participant_address, amount
        )
        self._log_info("Initiating a new atomicswap contract using command: {}".format(cmd))
        _, out, _ = self._prefab.core.run(cmd)
        return json.loads(out)

    def participate(self, initiator_address, amount, secret_hash):
        """
        Participate in an existing atomicswap contract

        @param initiator_address: Address of initiator
        @param amount: The amount of BTC to participate in this contract
        @param secret_hash: The secret hash of the atomicswap contract
        """
        cmd = 'btcatomicswap{} -automated --rpcuser={} --rpcpass={} -s "{}" participate {} {} {}'.format(
            " -testnet" if self._testnet else "",
            self._rpcuser,
            self._rpcpass,
            self._host,
            initiator_address,
            amount,
            secret_hash,
        )
        self._log_info("Participating in an atomicswap contract using command: {}".format(cmd))
        _, out, _ = self._prefab.core.run(cmd)
        return json.loads(out)

    def auditcontract(self, contract, contract_transaction):
        """
        Audit an existing atomicswap contract

        @param contract: Atomciswap contract script hash to audit
        @param contract_transaction: Atomicswap contract transaction address
        """
        cmd = 'btcatomicswap{} -automated --rpcuser={} --rpcpass={} -s "{}" auditcontract {} {}'.format(
            " -testnet" if self._testnet else "",
            self._rpcuser,
            self._rpcpass,
            self._host,
            contract,
            contract_transaction,
        )
        self._log_info("Auditing an atomicswap contract using command: {}".format(cmd))
        _, out, _ = self._prefab.core.run(cmd)
        return json.loads(out)

    def refund(self, contract, contract_transaction):
        """
        Refund an atomicswap contract

        @param contract: Atomciswap contract script hash to audit
        @param contract_transaction: Atomicswap contract transaction address
        """
        cmd = 'btcatomicswap{} -automated --rpcuser={} --rpcpass={} -s "{}" refund {} {}'.format(
            " -testnet" if self._testnet else "",
            self._rpcuser,
            self._rpcpass,
            self._host,
            contract,
            contract_transaction,
        )
        self._log_info("Refunding an atomicswap contract using command: {}".format(cmd))
        _, out, _ = self._prefab.core.run(cmd)
        return json.loads(out)

    def redeem(self, contract, contract_transaction, secret):
        """
        Complete the atomicswap contract by spending a the output as the receiver of the atomicswap

        @param contract: Atomciswap contract script hash to audit
        @param contract_transaction: Atomicswap contract transaction address
        @param secret: The atomicswap contract secret
        """
        cmd = 'btcatomicswap{} -automated --rpcuser={} --rpcpass={} -s "{}" redeem {} {} {}'.format(
            " -testnet" if self._testnet else "",
            self._rpcuser,
            self._rpcpass,
            self._host,
            contract,
            contract_transaction,
            secret,
        )
        self._log_info("Redeeming the atomicswap contract using command: {}".format(cmd))
        _, out, _ = self._prefab.core.run(cmd)
        return json.loads(out)

    def extract_secret(self, redemption_transaction, secret_hash):
        """
        Extract secret from atomicswap contract

        @param redemption_transaction: Atomciswap redemption transaction
        @param secret_hash: Atomicswap contract secret hash
        """
        cmd = 'btcatomicswap{} -automated --rpcuser={} --rpcpass={} -s "{}" extractsecret {} {}'.format(
            " -testnet" if self._testnet else "",
            self._rpcuser,
            self._rpcpass,
            self._host,
            redemption_transaction,
            secret_hash,
        )
        self._log_info("Extracting secret from an atomicswap contract using command: {}".format(cmd))
        _, out, _ = self._prefab.core.run(cmd)
        return json.loads(out)
