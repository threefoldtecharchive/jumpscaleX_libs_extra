## BTC_ALPHA client
interacts with btc-alpha.com to provides trading operations and broadcasting of all trading events.

### requirments
you need a key and a secret for your account.
- make an account from: https://btc-alpha.com/en/accounts/api/settings/
- go to settings - api and create api key

### make a new client
```
> test_client = j.clients.btc_alpha.get("my_client", key_="*******", secret_="*****")
> test_client.save()
```

### use the client
- you can inquire, exchange, order.
* example: `test_client.get_currencies()` <br/>
also pprint for more readable response
```
from pprint import pprint
pprint(test_client.get_currencies())
```
see what other methods do at: https://btc-alpha.github.io/api-docs
