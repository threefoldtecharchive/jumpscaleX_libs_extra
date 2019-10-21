# Threebot wikis deploy

## How to deploy threebot wikis

- You can create/use a machine for DNS hosting to control the subdomains using [CoreDNS](https://github.com/coredns/coredns) and [TCPRouter](https://github.com/xmonader/tcprouter) (TFGateway) if you don't have a machine with domain.
- Then create another machine to deploy the wikis on.

## Deploy DNS Hoster

- **create a new instance of threebot deploy tool for dnshoster.**

```python
kosmos
```

```python
dns_machine = j.tools.threebot_deploy.get("dns", do_machine_name="dogateway", do_token="YOUR DIGITAL OCEAN TOKEN", do_project_name="codescalers", ssh_key="YOUR SSH KEY")
```

**Note**: YOUR SSH KEY is the one which you will use to access the machine with. It should be saved on digital ocean's account, if not you can use your docker's ssh key

- **Get/Create the machine**

If you have a machine already you just make sure by

```python
dns_machine.do_machine
```

else create a new one:

```python
# optional change your machine specs. default(size_slug="s-1vcpu-1gb")
dns_machine.create_new_do_machine()
```

- **install jumpscale**

```python
# optional: you can pass the branch you want to install from
dns_machine.jsx_install(branch="development")
```

- **Deploy DNS Hoster**

```python
dns_machine.install_tcprouter_coredns()
```

Now we have the DNS machine up and ready

## Deploy 3bot wikis

- **create a new instance of threebot deploy tool.**

```python
kosmos
```

```python
wikis_machine = j.tools.threebot_deploy.get("wikis", do_machine_name="wikis", do_token="YOUR DIGITAL OCEAN TOKEN", ssh_key="YOUR SSH KEY")
```

**Note**: YOUR SSH KEY is the one which you will use to access the machine with. It should be saved on digital ocean's account, if not you can use your docker's ssh key

- **Get/Create the machine**

If you have a machine already you just get it

```python
wikis_machine.do_machine
```

else create a new one:

```python
# optional change your machine specs. default(size_slug="s-1vcpu-1gb")
wikis_machine.create_new_do_machine()
```

- **install jumpscale**

```python
wikis_machine.jsx_install()
```

- **Deploy wikis**

```python
wikis_machine.deploy_wikis()
```

- **Add dns record to the dns hoster**

```python
dns_machine.add_dns_record(subdomain="wikis", domain="web.grid.tf", wikis_machine_ip="WIKIS MACHINE IP", wikis_machine_port="443"):
```

Site should be live now, Congrats!

- **add macro tests**

```python
wikis_machine.test_macros()
```

will be at: domain/wiki/testwikis

- **reset_env**

To clear sonic and bcdb

```python
wikis_machine.reset_env()
```
