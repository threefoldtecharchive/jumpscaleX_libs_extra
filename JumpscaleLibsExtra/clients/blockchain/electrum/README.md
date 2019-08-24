# Electrum Wallet Client

This is a jumpscale wrapper to integrate [Electrum wallet](https://github.com/spesmilo/electrum), the client uses the standard jumpscale configuration management strategy.


## Client Configuration
The client can be configured via the following attributes:
- server: Electrum rpc daemon address in the form of host:port:protocol
- rpc_user: User name of the rpc user to use for connecting to the daemon
- rpc_pass: Password of the rpc user to use for connecting to the daemon
- electrum_path: Path to the electrum directory
- seed: The main seed of the wallet
- fee: Transaction fee
- testnet: if set to 1 then the client will connect to daemon connecting to testnet


## How to create a client instance
### Use an existing seed or generate a new one
If you already have a seed, you can use it to recover the your wallet addresses
```python
SEED = 'net shield travel gather west quote afraid salad spawn casino smile smoke boil flower rescue image antenna soda silent bounce husband tail square phrase'
```
If you want to create a new seed, you can do the following:
```python
from electrum.mnemonic import Mnemonic
SEED = Mnemonic('n').make_seed(num_bits=256)
```

To create a client instance you can run the following commands in a kosmos shell
```python
ELECTRUM_DIR = '/opt/var/data/electrum'
RPC_USER = 'user'
RPC_PASS = 'pass'
RPC_PORT = 7777
RPC_HOST = 'localhost'
WALLET_NAME = 'testwallet'

client_data = {
      'server': "{}:{}:s".format(RPC_HOST, RPC_PORT),
      'rpc_user': RPC_USER,
      'rpc_pass_': RPC_PASS,
      'seed_': SEED,
      'password_': "",
      "passphrase_": "",
      "electrum_path": ELECTRUM_DIR,
      "testnet": 1
  }

  electrum_cl = j.clients.btc_electrum.get(instance=WALLET_NAME,
                                                  data=client_data)
  electrum_cl.config.save()

```

## How to use the client
Once you have configured the client you can start using the wallet, the client supports all the commands the can be run by the Electrum commands from the console.

```python
WALLET_NAME = 'testwallet'
electrum_cl = j.clients.btc_electrum.get(WALLET_NAME)
electrum_cl.wallet.[TAP]

# list addresses
electrum_cl.wallet.listaddresses()

# check balance
electrum_cl.wallet.getbalance()
```


## Atomicwap Support
Atomicswap support is supported via the electrum client. The automicswap support depends on the Golang implementation of electrum atomicswap provided by [Rivine](https://github.com/rivine/atomicswap)

To perform atomicswap operations you will need to execute the following commands:
```python
WALLET_NAME = 'testwallet'
electrum_cl = j.clients.btc_electrum.get(WALLET_NAME)

electrum_cl.wallet.getbalance()

electrum_cl.atomicswap.[TAP]

```
Supported APIs are:
- Initiate
- Participate
- Auditcontract
- Redeem
- Refund
- Extractsecret

