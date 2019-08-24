# The style of key and value store :

 we suppose you have free domain is `cloudrobot.org`

## create client 
```
client = j.clients.etcd.get('test', data={'host':'10.102.242.128','password_': "password", 'user': "root"})
```
## coredns config

```
client.put("/hosts/org/cloudrobot", '{"host":"185.69.166.232","ttl":60}')

```
NOTE: if domain name is example.test.com
        key is `/hosts/com/test/example`

## traefik config
add your backend
```
In [142]: client.put("/traefik/backends/backend1/servers/server1/url", 'http://10.147.18.195')
```
point your frondend to the name of backend 
```
In [143]: client.put("/traefik/frontends/frontend1/backend", 'backend1')
```
add your frontend 
```
In [144]: client.put("/traefik/frontends/frontend1/routes/frontend1/rule", "Host:cloudrobot.org")
```
