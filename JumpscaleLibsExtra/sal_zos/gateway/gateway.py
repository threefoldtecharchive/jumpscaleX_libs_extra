import time

import yaml
from Jumpscale import j

from ..abstracts import Collection
from .cloudinit import CloudInit
from .dhcp import DHCP
from .firewall import Firewall
from .http import HTTPServer
from .network import Networks

PUBLIC_THREEFOLD_NETWORK = "9bee8941b5717835"


class DestBind:
    def __init__(self, ipaddress, port):
        """
        Portforward target bind instance
        :param ipaddress: ip to forward to
        :type ipaddress: str
        :param port: port to forward to
        :type port: int
        """
        self.ipaddress = ipaddress
        self.port = port

    def __str__(self):
        return "Bind <{}:{}>".format(self.ipaddress, self.port)

    __repr__ = __str__


class SourceBind:
    def __init__(self, parent, network_name, port):
        """
        Portforward source bind instance

        :param parent: the parent of the forward
        :type parent: Gateway
        :param network_name: the network name to get the source ip from
        :type network_name: str
        :param port: the source port to forward from
        :type port
        """
        self.network_name = network_name
        self.port = port
        self.parent = parent

    @property
    def ipaddress(self):
        return self.parent.networks[self.network_name].ip.address

    @ipaddress.setter
    def ipaddress(self):
        raise j.exceptions.Base("ipaddress can't be set")

    def __str__(self):
        return "Source Bind <{}:{}>".format(self.network_name, self.port)

    __repr__ = __str__


class Forward:
    def __init__(self, parent, name, source=None, target=None, protocols=None):
        """
        Initialize forward

        :param parent: the parent of the forward
        :type parent: Gateway
        :param name: Logical name to give to the portforward
        :type name: str
        :param source: Source Network/Port for the portforwards
        :type source: tuple(str, int) or instance of SourceBind
        :param target: Target IP/Port for the portforwards
        :type target: tuple(str, int) or instance of DestBind
        :param protocols: Protocols to forward tcp or udp
        :type protocols: list(str)
        """
        self.name = name
        if protocols:
            for protocol in protocols:
                if protocol not in ["tcp", "udp"]:
                    raise j.exceptions.Value("Invalid protocol {} for portforward".format(protocol))
        if protocols is None:
            protocols = ["tcp"]
        self.protocols = protocols
        if isinstance(source, tuple):
            self.source = SourceBind(parent, *source)
        elif isinstance(source, SourceBind):
            self.source = source
        if self.source.network_name not in parent.networks:
            raise j.exceptions.NotFound("Network with name {} doesn't exist".format(self.source.network_name))

        if isinstance(target, tuple):
            self.target = DestBind(*target)
        elif isinstance(target, DestBind):
            self.target = target

    def __str__(self):
        return "Forward <{}:{}>".format(self.source, self.target)

    __repr__ = __str__


class PortForwards(Collection):
    def add(self, name, source, target, protocols=None):
        """
        Add portforward to the gateway

        :param name: Logical name to give to the portforward
        :type name: str
        :param source: Source Network/Port for the portforwards
        :type source: tuple(str, int) or instance of SourceBind
        :param target: Target IP/Port for the portforwards
        :type target: tuple(str, int) or instance of DestBind
        :param protocols: Protocols to forward tcp or udp
        :type protocols: list(str)
        """
        super().add(name)
        forward = Forward(self._parent, name, source, target, protocols)
        self._items.append(forward)
        return forward


class HTTPProxy:
    def __init__(self, name, host, destinations, types=None):
        """
         Httproxy instance
        :param name: logical name of the http proxy
        :type name: str
        :param host: Host to forward for typical a dns like eg: example.org
        :type host: str
        :param destinations: One or more destination to forward to:
                                eg: ['http://192.168.103.2:8080']
        :type destinations: list(str)
        :param types: Type of proxy http or https
        :type types: list(str)
        """
        self.name = name
        self.host = host
        if types:
            for proxy_type in types:
                if proxy_type not in ["http", "https", "shttps"]:
                    raise j.exceptions.Value("Invalid type {} for http proxy".format(proxy_type))
        if types is None:
            types = ["http", "https"]
        self.types = types
        self.destinations = destinations

    def __str__(self):
        return "Proxy <{}:{}>".format(self.host, self.destinations)

    __repr__ = __str__


class HTTPProxies(Collection):
    def add(self, name, host, destinations, types=None):
        """
        Add http proxy to the gateway
        :param name: logical name of the http proxy
        :type name: str
        :param host: Host to forward for typical a dns like eg: example.org
        :type host: str
        :param destinations: One or more destination to forward to:
                                eg: ['http://192.168.103.2:8080']
        :type destinations: list(str)
        :param types: Type of proxy http or https
        :type types: list(str)
        """
        super().add(name)
        proxy = HTTPProxy(name, host, destinations, types)
        self._items.append(proxy)
        return proxy


class Route:
    def __init__(self, name, dev, dest, gateway=None):
        """
        Route instance


        :param name: logcal name of the route
        :type name: str
        :param dev: device name
        :type dev: str
        :param dest: destination network
        :type dest: str
        :param gateway: optional gateway, defaults to None
        :param gateway: str, optional
        """

        self.name = name
        self.dev = dev
        self.dest = dest
        self.gateway = gateway

    def __str__(self):
        return "Route <{} via {} dev {}>".format(self.dest, self.gateway, self.dev)

    __repr__ = __str__


class Routes(Collection):
    def add(self, name, dev, dest, gateway=None):
        """
        Add a route to the gateway


        :param name: logical name of the route
        :type name: str
        :param dev: device name
        :type dev: str
        :param dest: destination network
        :type dest: str
        :param gateway: optional gateway, defaults to None
        :param gateway: str, optional
        """

        super().add(name)
        route = Route(name, dev, dest, gateway)
        self._items.append(route)
        return route


class Gateway:
    def __init__(self, node, name):
        """
        Gateway Sal
        :param node: node sal object
        :type node: class Node
        :param name: gateway logical name
        :type name: str
        """
        self.name = name
        self.node = node
        self.domain = "lan"
        self._container = None
        self.networks = Networks(self)
        self.routes = Routes(self)
        self.flist = "https://hub.grid.tf/tf-official-apps/zero-os-gw-master.flist"
        self.portforwards = PortForwards(self)
        self.httpproxies = HTTPProxies(self)
        self.certificates = []
        self.zt_identity = None
        self._default_nic = ""  # the name of the default network if there is one

    def from_dict(self, data):
        """
        Initialize networks, portforwards, httpproxies and certificates from data.

        :param data: data to use for initialization
        :type data: dict following the schema of the gateway template https://github.com/zero-os/0-templates/tree/master/templates/gateway/schema.capnp
        """
        self.networks = Networks(self)
        self.routes = Routes(self)
        self.portforwards = PortForwards(self)
        self.httpproxies = HTTPProxies(self)
        self.zt_identity = data.get("ztIdentity")
        self.domain = data.get("domain") or "lan"
        self.certificates = data.get("certificates", [])
        for nic in data.get("networks", []):
            network = self.networks.add(nic["name"], nic["type"], nic.get("id"))
            if nic.get("config"):
                network.ip.cidr = nic["config"].get("cidr", None)
                network.ip.gateway = nic["config"].get("gateway", None)
            if network.type == "zerotier":
                network.client_name = nic.get("ztClient")
            if nic.get("hwaddr"):
                network.hwaddr = nic["hwaddr"]
            network.public = nic.get("public")
            dhcpserver = nic.get("dhcpserver")
            if not dhcpserver:
                continue
            network.hosts.nameservers = dhcpserver.get("nameservers", [])
            network.hosts.pool_size = dhcpserver.get("poolSize", network.hosts.pool_size)
            network.hosts.pool_start = dhcpserver.get("poolStart", network.hosts.pool_start)
            for host in dhcpserver["hosts"]:
                dhcphost = network.hosts.add(host["hostname"], host["ipaddress"], host["macaddress"])
                if host.get("cloudinit", {}).get("userdata"):
                    dhcphost.cloudinit.userdata = yaml.load(host["cloudinit"]["userdata"])
                if host.get("cloudinit", {}).get("metadata"):
                    dhcphost.cloudinit.metadata = yaml.load(host["cloudinit"]["metadata"])
        for forward in data["portforwards"]:
            self.portforwards.add(
                forward["name"],
                (forward["srcnetwork"], forward["srcport"]),
                (forward["dstip"], forward["dstport"]),
                forward.get("protocols"),
            )
        for proxy in data["httpproxies"]:
            self.httpproxies.add(proxy["name"], proxy["host"], proxy["destinations"], proxy["types"])
        for route in data["routes"]:
            self.routes.add(route["name"], route["dev"], route["dest"], route["gateway"])

    def deploy(self):
        """
        Deploy gateway in reality
        """
        publicnetworks = list(filter(lambda net: net.public, self.networks))
        if len(publicnetworks) != 1:
            raise j.exceptions.Base("Need exactly one public network")
        if publicnetworks[0].type == "zerotier" and not self._default_nic:
            defnet = self.networks.add("nat0", "default")
            defnet.public = False
        if self.container is None:
            self.create_container()
        elif not self.container.is_running():
            self.container.start()
        self.container.upload_content("/etc/resolv.conf", "nameserver 127.0.0.1\n")
        self.setup_zerotier()

        # setup cloud-init magical ip
        ip = self.container.client.ip
        loaddresses = ip.addr.list("lo")
        magicip = "169.254.169.254/32"
        if magicip not in loaddresses:
            ip.addr.add("lo", magicip)
        if "cloudinit" not in self.httpproxies:
            self.httpproxies.add("cloudinit", "169.254.169.254", ["http://127.0.0.1:8080"], ["http"])

        self.update_nics()
        self.restore_certificates()
        self.configure_fw()
        self.configure_dhcp()
        self.configure_cloudinit()
        self.configure_http()
        self.save_certificates()
        self.configure_routes()

    def stop(self):
        """
        Stop a gateway by stopping the container
        """
        if self.container:
            self.container.stop()
            self._container = None

    def update_nics(self):
        """
        Apply gateway's networks to gateway container's nics
        """
        if self.container is None:
            raise j.exceptions.Base("Can not update nics when gateway is not deployed")
        toremove = []
        wantednetworks = list(self.networks)
        for nic in self.container.nics:
            try:
                network = self.networks[nic["name"]]
                wantednetworks.remove(network)
            except KeyError:
                toremove.append(nic)
        for removeme in toremove:
            if removeme["type"] == "default":
                self._remove_container_portforwards()
            self.container.remove_nic(removeme["name"])

        for network in wantednetworks:
            self.container.add_nic(network.to_dict(forcontainer=True))
            if network.type == "default":
                self._update_container_portforwards()

    def _container_name(self):
        """
        Return the name used for gateway's container
        :return: container name
        :rtype: str
        """
        return "gw_{}".format(self.name)

    @property
    def container(self):
        """
        Get container to run gateway services on

        :return: Container object or None
        :rtype: Container
        """
        if self._container is None:
            try:
                self._container = self.node.containers.get(self._container_name())
            except LookupError:
                return None
        return self._container

    def is_running(self):
        if self.container:
            return self.container.is_running()
        return False

    def create_container(self):
        """
        Create the gateway container
        """
        public_threefold_nic = False
        nics = []
        if not self.zt_identity:
            self.zt_identity = self.node.client.system("zerotier-idtool generate").get().stdout.strip()
        ztpublic = self.node.client.system("zerotier-idtool getpublic {}".format(self.zt_identity)).get().stdout.strip()

        for network in self.networks:
            if network.type == "zerotier":
                if not network.networkid:
                    if not network.client:
                        raise j.exceptions.Base("Zerotier network should either have client or networkid assigned")
                    cidr = network.ip.subnet or "172.20.0.0/16"
                    ztnetwork = network.client.network_create(False, cidr, name=network.name)
                    network.networkid = ztnetwork.id
                if network.networkid == PUBLIC_THREEFOLD_NETWORK:
                    public_threefold_nic = True
                if network.client:
                    ztnetwork = network.client.network_get(network.networkid)
                    privateip = None
                    if network.ip.cidr:
                        privateip = str(network.ip.cidr)
                    ztnetwork.member_add(ztpublic, self.name, private_ip=privateip)
            nics.append(network.to_dict(forcontainer=True))
        if not public_threefold_nic:
            network = self.networks.add(name="threefold", type_="zerotier", networkid=PUBLIC_THREEFOLD_NETWORK)
            nics.append(network.to_dict(forcontainer=True))
            # zerotierbridge = nic.pop('zerotierbridge', None)
            # if zerotierbridge:
            #    contnics.append(
            #        {
            #            'id': zerotierbridge['id'], 'type': 'zerotier',
            #            'name': 'z-{}'.format(nic['name']), 'token': zerotierbridge.get('token', '')
            #        })
        self._container = self.node.containers.create(
            self._container_name(),
            self.flist,
            hostname=self.name,
            nics=nics,
            privileged=True,
            identity=self.zt_identity,
        )
        return self._container

    def to_dict(self, live=False):
        """
        Convert the gateway object to a dict.
        :return: a dict representation of the gateway matching the schema of the gateway template
                 https://github.com/zero-os/0-templates/tree/master/templates/gateway/schema.capnp
        :rtype: dict
        """
        data = {
            "networks": [],
            "routes": [],
            "hostname": self.name,
            "portforwards": [],
            "httpproxies": [],
            "domain": self.domain,
            "certificates": self.certificates,
            "ztIdentity": self.zt_identity,
        }
        for network in self.networks:
            nic = network.to_dict(live=live)
            if network.hosts.list():
                hosts = []
                dhcp = {
                    "nameservers": network.hosts.nameservers,
                    "hosts": hosts,
                    "poolStart": network.hosts.pool_start,
                    "poolSize": network.hosts.pool_size,
                }
                for networkhost in network.hosts:
                    host = {
                        "macaddress": networkhost.macaddress,
                        "ipaddress": networkhost.ipaddress,
                        "hostname": networkhost.name,
                        "cloudinit": {
                            "userdata": yaml.dump(networkhost.cloudinit.userdata),
                            "metadata": yaml.dump(networkhost.cloudinit.userdata),
                        },
                    }
                    hosts.append(host)
                nic["dhcpserver"] = dhcp
            data["networks"].append(nic)
        for proxy in self.httpproxies:
            data["httpproxies"].append(
                {"host": proxy.host, "destinations": proxy.destinations, "types": proxy.types, "name": proxy.name}
            )
        for forward in self.portforwards:
            data["portforwards"].append(
                {
                    "srcport": forward.source.port,
                    "srcnetwork": forward.source.network_name,
                    "dstport": forward.target.port,
                    "dstip": forward.target.ipaddress,
                    "protocols": forward.protocols,
                    "name": forward.name,
                }
            )
        for route in self.routes:
            data["routes"].append({"name": route.name, "dev": route.dev, "dest": route.dest, "gateway": route.gateway})
        return data

    def to_json(self):
        """
        Create a json string of the result of to_dict function
        """
        return j.data.serializers.json.dumps(self.to_dict())

    def configure_dhcp(self):
        """
        Configure dhcp server based on the hosts added to the networks
        """
        if self.container is None:
            raise j.exceptions.Base("Can not configure dhcp when gateway is not deployed")
        dhcp = DHCP(self.container, self.domain, self.networks)
        dhcp.apply_config()

    def configure_cloudinit(self):
        """
        Configure cloudinit
        """
        if self.container is None:
            raise j.exceptions.Base("Can not configure cloudinit when gateway is not deployed")
        cloudinit = CloudInit(self.container, self.networks)
        cloudinit.apply_config()

    def configure_http(self):
        """
        Configure http server based on the httpproxies
        """
        if self.container is None:
            raise j.exceptions.Base("Can not configure http when gateway is not deployed")
        httpserver = HTTPServer(self.container, self.httpproxies)
        httpserver.apply_rules()

    def configure_fw(self):
        """
        Configure nftables based on the networks and portforwards
        """
        if self.container is None:
            raise j.exceptions.Base("Can not configure fw when gateway is not deployed")

        if self._default_nic and self.networks[self._default_nic].public:
            self._update_container_portforwards()

        firewall = Firewall(self.container, self.networks, self.portforwards, self.routes)
        firewall.apply_rules()

    def configure_routes(self):
        """
        Configure routing table
        """
        if self.container is None:
            raise j.exceptions.Base("Can not configure fw when gateway is not deployed")
        existing_routes = self.container.client.ip.route.list()

        def exists(route):
            for r in existing_routes:
                if r["dev"] == route.dev and r["dst"] == route.dest:
                    return True
            return False

        for route in self.routes:
            if not exists(route):
                self.container.client.ip.route.add(dev=route.dev, dst=route.dest, gw=route.gateway)

    def _remove_container_portforwards(self):
        """
        Remove all portforwards on the gateway container
        """
        for host_port, container_port in self.container.info["container"]["arguments"]["port"].items():
            self.container.node.client.container.remove_portforward(self.container.id, host_port, int(container_port))

    def _update_container_portforwards(self):
        """
        Update the gateway container portforwards
        """
        publicip = self.node.get_nic_hwaddr_and_ip()[1]
        container_forwards = set(
            [v for k, v in self.container.info["container"]["arguments"]["port"].items() if v == int(k.split(":")[-1])]
        )
        wanted_forwards = {80, 443}
        container_ip = str(self.container.default_ip(self._default_nic).ip)
        for forward in self.portforwards:
            source = forward.source
            if str(source.ipaddress) == container_ip:
                wanted_forwards.add(source.port)
        for port in container_forwards - wanted_forwards:
            self.container.node.client.container.remove_portforward(
                self.container.id, "{}:{}".format(publicip, port), port
            )
        for port in wanted_forwards - container_forwards:
            self.container.node.client.container.add_portforward(
                self.container.id, "{}:{}".format(publicip, port), port
            )

    def save_certificates(self, caddy_dir="/.caddy"):
        """
        Store https certificates in self.certificates
        """
        if self.container.client.filesystem.exists(caddy_dir):
            self.certificates = []
            for cert_authority in self.container.client.filesystem.list("{}/acme/".format(caddy_dir)):
                if cert_authority["is_dir"]:
                    users = []
                    sites = []
                    if self.container.client.filesystem.exists(
                        "{}/acme/{}/users".format(caddy_dir, cert_authority["name"])
                    ):
                        users = self.container.client.filesystem.list(
                            "{}/acme/{}/users".format(caddy_dir, cert_authority["name"])
                        )
                    if self.container.client.filesystem.exists(
                        "{}/acme/{}/sites".format(caddy_dir, cert_authority["name"])
                    ):
                        sites = self.container.client.filesystem.list(
                            "{}/acme/{}/sites".format(caddy_dir, cert_authority["name"])
                        )
                    for user in users:
                        if user["is_dir"]:
                            cert_path = "{}/acme/{}/users/{}".format(caddy_dir, cert_authority["name"], user["name"])
                            metadata = key = cert = ""
                            if self.container.client.filesystem.exists("{}/{}.json".format(cert_path, user["name"])):
                                metadata = self.container.download_content("{}/{}.json".format(cert_path, user["name"]))
                            if self.container.client.filesystem.exists("{}/{}.key".format(cert_path, user["name"])):
                                key = self.container.download_content("{}/{}.key".format(cert_path, user["name"]))
                            self.certificates.append({"path": cert_path, "key": key, "metadata": metadata})

                    for site in sites:
                        if site["is_dir"]:
                            cert_path = "{}/acme/{}/sites/{}".format(caddy_dir, cert_authority["name"], site["name"])
                            metadata = key = cert = ""
                            if self.container.client.filesystem.exists("{}/{}.json".format(cert_path, site["name"])):
                                metadata = self.container.download_content("{}/{}.json".format(cert_path, site["name"]))
                            if self.container.client.filesystem.exists("{}/{}.key".format(cert_path, site["name"])):
                                key = self.container.download_content("{}/{}.key".format(cert_path, site["name"]))
                            if self.container.client.filesystem.exists("{}/{}.crt".format(cert_path, site["name"])):
                                cert = self.container.download_content("{}/{}.crt".format(cert_path, site["name"]))
                            self.certificates.append(
                                {"path": cert_path, "key": key, "metadata": metadata, "cert": cert}
                            )

    def restore_certificates(self):
        """
        Restore https certifcates if loaded into self.certificates
        """
        for cert in self.certificates:
            self.container.client.filesystem.mkdir(cert["path"])
            self.container.upload_content(
                "{}/{}.json".format(cert["path"], cert["path"].split("/")[-1]), cert["metadata"]
            )
            self.container.upload_content("{}/{}.key".format(cert["path"], cert["path"].split("/")[-1]), cert["key"])
            if cert.get("cert"):
                self.container.upload_content(
                    "{}/{}.crt".format(cert["path"], cert["path"].split("/")[-1]), cert["cert"]
                )

    def get_zerotier_nic(self, zerotierid):
        """
        Get the zerotier network device
        :param zerotierid: id of the zerotier
        :type zerotierid: str
        :return: zerotier network device name
        :rtype: str
        """
        for zt in self.container.client.zerotier.list():
            if zt["id"] == zerotierid:
                return zt["portDeviceName"]
        else:
            raise j.exceptions.RuntimeError("Failed to get zerotier network device")

    def cleanup_zerotierbridge(self, nic):
        zerotierbridge = nic.pop("zerotierbridge", None)
        ip = self.container.client.ip
        if zerotierbridge:
            nicname = nic["name"]
            linkname = "l-{}".format(nicname)[:15]
            zerotiername = self.get_zerotier_nic(zerotierbridge["id"])

            # bring related interfaces down
            ip.link.down(nicname)
            ip.link.down(linkname)
            ip.link.down(zerotiername)

            # remove IPs
            ipaddresses = ip.addr.list(nicname)
            for ipaddr in ipaddresses:
                ip.addr.delete(nicname, ipaddr)

            # delete interfaces/bridge
            ip.bridge.delif(nicname, zerotiername)
            ip.bridge.delif(nicname, linkname)
            ip.bridge.delete(nicname)

            # rename interface and readd IPs
            ip.link.name(linkname, nicname)
            for ipaddr in ipaddresses:
                ip.addr.add(nicname, ipaddr)

            # bring interfaces up
            ip.link.up(nicname)
            ip.link.up(zerotiername)

    def setup_zerotier(self):
        # TODO: Implement zerotierbridge
        def wait_for_interface():
            start = time.time()
            while start + 60 > time.time():
                for link in self.container.client.ip.link.list():
                    if link["type"] == "tun":
                        return
                time.sleep(0.5)
            raise j.exceptions.RuntimeError("Could not find zerotier network interface")

        ip = self.container.client.ip
        for network in self.networks:
            continue
            # zerotierbridge = nic.pop('zerotierbridge', None)
            # if zerotierbridge:
            #     nicname = nic['name']
            #     linkname = 'l-{}'.format(nicname)[:15]
            #     wait_for_interface()
            #     zerotiername = self.get_zerotier_nic(zerotierbridge['id'])
            #     token = zerotierbridge.get('token')
            #     if token:
            #         zerotier = client.Client()
            #         zerotier.set_auth_header('bearer {}'.format(token))

            #         resp = zerotier.network.getMember(self.container.model.data.zerotiernodeid, zerotierbridge['id'])
            #         member = resp.json()

            #         j.tools.logger._log_info("Enable bridge in member {} on network {}".format(member['nodeId'], zerotierbridge['id']))
            #         member['config']['activeBridge'] = True
            #         zerotier.network.updateMember(member, member['nodeId'], zerotierbridge['id'])

            #     # check if configuration is already done
            #     linkmap = {link['name']: link for link in ip.link.list()}

            #     if linkmap[nicname]['type'] == 'bridge':
            #         continue

            #     # bring related interfaces down
            #     ip.link.down(nicname)
            #     ip.link.down(zerotiername)

            #     # remove IP and rename
            #     ipaddresses = ip.addr.list(nicname)
            #     for ipaddr in ipaddresses:
            #         ip.addr.delete(nicname, ipaddr)
            #     ip.link.name(nicname, linkname)

            #     # create bridge and add interface and IP
            #     ip.bridge.add(nicname)
            #     ip.bridge.addif(nicname, linkname)
            #     ip.bridge.addif(nicname, zerotiername)

            #     # readd IP and bring interfaces up
            #     for ipaddr in ipaddresses:
            #         ip.addr.add(nicname, ipaddr)
            #     ip.link.up(nicname)
            #     ip.link.up(linkname)
            #     ip.link.up(zerotiername)
