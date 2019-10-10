from Jumpscale import j

JSBASE = j.baseclasses.object

"""
This module assume having tcprouter and coredns installed.
tfgateway = j.tools.tf_gateway.get(j.core.db) # or another redisclient
tfgateway.tcpservice_register("bing", "www.bing.com", "122.124.214.21")
tfgateway.domain_register_a("ahmed", "bots.grid.tf.", "123.3.23.54")
"""


class TFGateway(j.baseclasses.object):
    """
    tool to register tcpservices in tcprouter and coredns records
    """

    def __init__(self, redisclient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redisclient = redisclient

    def _validate_ip(self, ip):
        if not j.data.types.ipaddr.check(ip):
            raise j.exceptions.Value("invalid ip {}".format(ip))

    def _records_get(self, record_ip):
        records = []
        if isinstance(record_ip, str):
            self._validate_ip(record_ip)
            records = [{"ip": record_ip}]

        elif isinstance(record_ip, list):
            for ip in record_ip:
                self._validate_ip(ip)
                records.append({"ip": ip})
        return records

    def install(self):
        j.builders.network.tcprouter.install()
        j.builders.network.tcprouter.start()
        j.builders.network.coredns.install()
        j.builders.network.coredns.start()

    def tcpservice_register(self, service_name, domain, service_endpoint):
        """
        register a tcpservice to be used by tcprouter in j.core.db

        :param service_name: service name to register in tcprouter
        :type service_name: str
        :param domain: (Server Name Indicator SNI) (e.g www.facebook.com)
        :type domain: str
        :param service_endpoint: TLS endpoint 102.142.96.34:443 "ip:port"
        :type service_endpoint: string 
        """
        service = {}
        service["Key"] = "/tcprouter/service/{}".format(service_name)
        record = {"addr": service_endpoint, "sni": domain, "name": service_name}
        json_dumped_record_bytes = j.data.serializers.json.dumps(record).encode()
        b64_record = j.data.serializers.base64.encode(json_dumped_record_bytes).decode()
        service["Value"] = b64_record
        self.redisclient.set(service["Key"], j.data.serializers.json.dumps(service))

    def domain_register(self, name, domain="bots.grid.tf.", record_type="a", records=None):
        """registers domain in coredns (needs to be authoritative)
        
        e.g: ahmed.bots.grid.tf

        requires nameserver on bots.grid.tf (authoritative)
        - ahmed is name
        - domain is bots.grid.tf
        
        :param name: name 
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param record_type: valid dns record (a, aaaa, txt, srv..), defaults to "a"
        :type record_type: str, optional
        :param records: records list, defaults to None
        :type records: [type], optional is [ {"ip":machine ip}] in case of a/aaaa records
        """
        if not domain.endswith("."):
            domain += "."
        data = {}
        records = records or []
        if self.redisclient.hexists(domain, name):
            data = j.data.serializers.json.loads(self.redisclient.hget(domain, name))

        if record_type in data:
            for record in data[record_type]:
                if record not in records:
                    records.append(record)
        data[record_type] = records
        self.redisclient.hset(domain, name, j.data.serializers.json.dumps(data))

    def domain_list(self):
        return self.redisclient.keys("*.")

    def domain_exists(self, domain):
        if not domain.endswith("."):
            domain += "."
        if self.redisclient.exists(domain):
            return True
        subdomain, domain = domain.split(".", 1)
        return self.redisclient.hexist(domain, subdomain)

    def domain_dump(self, domain):
        if not domain.endswith("."):
            domain += "."
        resulset = {}
        for key, value in self.redisclient.hgetall(domain).items():
            resulset[key.decode()] = j.data.serializers.json.loads(value)
        return resulset

    def subdomain_get(self, domain, subdomain):
        if not domain.endswith("."):
            domain += "."
        subdomain_info = self.redisclient.hget(domain, subdomain)
        return j.data.serializers.json.loads(subdomain_info)

    def domain_register_a(self, name, domain, record_ip):
        """registers A domain in coredns (needs to be authoritative)
        
        e.g: ahmed.bots.grid.tf

        requires nameserver on bots.grid.tf (authoritative)
        - ahmed is name
        - domain is bots.grid.tf
        
        :param name: myhost
        :type name: str
        :param domain: str, defaults to "grid.tf."
        :type domain: str, optional
        :param record_ip: machine ip in ipv4 format
        :type record_ip: str or list of str
        """
        records = self._records_get(record_ip)
        return self.domain_register(name, domain, record_type="a", records=records)

    def domain_register_aaaa(self, name, domain, record_ip):
        """registers A domain in coredns (needs to be authoritative)
        
        e.g: ahmed.bots.grid.tf

        requires nameserver on bots.grid.tf (authoritative)
        - ahmed is name
        - domain is bots.grid.tf
        
        :param name: name 
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param record_ip: machine ips in ipv6 format
        :type record_ip: list of str
        """
        records = self._records_get(record_ip)
        return self.domain_register(name, domain, record_type="aaaa", records=records)

    def domain_register_cname(self, name, domain, host):
        """Register CNAME record
        
        :param name: name 
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: cname
        :type host: str
        """
        self.domain_register(name, domain, "cname", records=[{"host": host}])

    def domain_register_ns(self, name, domain, host):
        """register NS record

        :param name: name 
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: host
        :type host: str

        """
        self.domain_register(name, domain, "ns", records=[{"host": host}])

    def domain_register_txt(self, name, domain, text):
        """register TXT record

        :param name: name 
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param text: text
        :type text: text
        """

        self.domain_register(name, domain, "txt", records=[{"text": text}])

    def domain_register_mx(self, name, domain, host, priority=10):
        """register MX record

        :param name: name 
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: host for mx e.g mx1.example.com
        :type host: str
        :param priority: priority defaults to 10
        :type priority: int

        """

        self.domain_register(name, domain, "mx", records=[{"host": host, "priority": priority}])

    def domain_register_srv(self, name, domain, host, port, priority=10, weight=100):
        """register SRV record

        :param name: name 
        :type name: str
        :param domain: str, defaults to "bots.grid.tf."
        :type domain: str, optional
        :param host: host for mx e.g mx1.example.com
        :type host: str
        :param port: port for srv record
        :type port: int
        :param priority: priority defaults to 10
        :type priority: int
        :param weight: weight defaults to 100
        :type weight: int

        """
        self.domain_register(
            name, domain, "srv", records=[{"host": host, "port": port, "priority": priority, "weight": weight}]
        )

    def test(self):
        """
        kosmos 'j.tools.tf_gateway.test()'

        :return:
        """
        self.domain_register_a("ns", "3bot.me", "134.209.90.92")
        self.domain_register_a("a", "3bot.me", "134.209.90.92")

        # to test
        # dig @ns1.name.com a.test.3bot.me
