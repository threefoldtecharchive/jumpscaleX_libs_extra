# EMail Forwarder
Email forwarder is a gevent bases SMTP server that accepts emails sent to a preconfigured list of 
domains and forward these emails to a configured destination email.
It helps us avoid configuring different aliases for each of our domains.


## Configurations
The API need to be configured to work correctly. The followig configurations are available:
- `listening_host`: the ip address for listening to incoming connections
- `listening_port`: the port to be used for listening to incoming connections
- `relay_host`: the host domain/ip address to use for sending the forwarded emails
- `relay_port`: the port to use for sending the forwarded emails
- `relay_user`: the user name (email address) to authenticate with
- `relay_password`: the password to authenticate with
- `relay_ssh`: use ssl for communication with the SMTP server
- `forward_config`: this is a list of forwarding configurations

### Forwarding Configurations
Forwarding configurations can be added by using the `add_forward_config` function:
```python
mf = j.servers.mail_forwarder.get(....)
mf.add_forward_config("codescalers.com", ["incubaide.com", "threefoldtech.com"])
```


## Handling incoming non-configured domain
Configuring an SMTP relay server can introduce the risk of having an open relay. To address this risk, the current implementation will drop all the recipients that do not match any of the source domains. i.e, if we have a recipient `husseina@mydomain.com` this recipient will not receive any emails.

## Known Issues
- The current implementation does not detect forwarding cycles
