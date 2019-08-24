import ipaddress


class OutOfIPs(Exception):
    pass


def _as_ip4(ipaddr):
    """[Converts ipv4 address string to ipaddress.IPv4Address.]
    
    Arguments:
        ipaddr {[str|ipaddress.IPAddress]} -- [IP address to normalize]
    
    Returns:
        [ipaddress.IPv4Address] -- [IPv4Address object]
    """
    _ip = ipaddr
    if isinstance(ipaddr, str):
        _ip = ipaddress.IPv4Address(ipaddr)
    return _ip


class IPPool:
    def __init__(self, id="", name="", network_address="", registered_ips=None):
        """[Creates an IPPool.]

        IPPool keeps track of all IPs and their state whether it's reserved or available

        Keyword Arguments:
            id {str} -- [pool id] (default: {""})
            name {str} -- [pool name] (default: {""})
            network_address {str} -- [network address e.g 192.168.20.0/24] (default: {""})

        Returns:
            [IPPool] -- [IP addresses pool] 
        """
        self.id = id
        self.name = name
        self.network_address = network_address
        self._network = ipaddress.IPv4Network(network_address)
        self._reserved = []
        self.registered_ips = registered_ips or list(self._network.hosts())

    @property
    def registered_ips(self):
        """
        [Gets the registered ips]
        
        Returns:
            [type] -- [description]
        """

        return self._ips

    @registered_ips.setter
    def registered_ips(self, registered_ips):
        self._ips = [self._validate_ip(ip) for ip in registered_ips]

    def _validate_ip(self, ipaddr):
        """[Checks if ipv4 address string is a valid IP and within the network.]
        
        Arguments:
            ipaddr {[str|ipaddress.IPv4Address]} -- [IP address to validate.]
        
        Raises:
            ValueError -- [Raised if the ipaddr not within the network hosts.]

        Returns:
            [ipaddress.IPv4Address] -- [Validated IP address as ipaddress.IPv4Address]

        """
        _ip = _as_ip4(ipaddr)
        if _ip not in self._network:
            raise j.exceptions.Value("{} not in network {}".format(ipaddr, self._network))

        return _ip

    def _validate_reservable_ip(self, ipaddr):
        """[Checks if IP ipaddr is reservable or not]
        
        Arguments:
            ipaddr {[str|ipaddress.IPv4Address]} -- [IP to reserve]
        
        Raises:
            ValueError -- [Raises value error if a IP ipaddr is loopback or network address or broadcast address]
        
        Returns:
            [ipaddress.IPv4Address] -- [Validated IP address as ipaddress.IPv4Address]
        """
        _ip = self._validate_ip(ipaddr)
        if _ip.is_loopback or _ip == self._network.network_address or _ip == self._network.broadcast_address:
            raise j.exceptions.Value(
                "{} can't be loopback or network_address {} or broadcast_address {}".format(
                    _ip, self._network.network_address, self._network.broadcast_address
                )
            )

        return _ip

    @property
    def subnetmask(self):
        """[Returns subnet mask of the network]
        
        Returns:
            [ipaddress.IPv4Address] -- [network netmask]
        """
        return self._network.netmask

    @property
    def ips(self):
        """[Returns all the host IP addresses in the network]
        
        Returns:
            [ List[ipaddress.IPv4Address] ] -- [List of all IPs in the network]
        """
        return self._ips

    hosts = ips

    @property
    def available_ips(self):
        """[Returns all the available IP addresses in the network.]
        
        Returns:
            [ List[ipaddress.IPv4Addresses] ] -- [List of all available IPs in the network]
        """
        return list(set(self._ips) - set(self._reserved))

    available_hosts = available_ips

    @property
    def reserved_ips(self):
        """[List of all reserved IP addresses in the network.]
        
        Returns:
            [ List[ipaddress.IPv4Addresses] ] -- [List of all reserved IPs in the network]
        """
        return self._reserved

    reserved_hosts = reserved_ips

    def reserve_ip(self, ipaddr):
        """[Reserve IP address on the network]
        
        Arguments:
            ipaddr {[string|ipaddress.IPv4Address]} -- [Reserve IP address on the network]
        """
        _ip = self._validate_reservable_ip(ipaddr)
        self._reserved.append(_ip)
        return _ip

    def release_ip(self, ipaddr):
        """[Release a reserved IP address back to the pool]
        
        Arguments:
            ipaddr {[str|ipaddress.IPv4Address]} -- [Reserve IP address on the network]
        """
        _ip = self._validate_ip(ipaddr)
        self._reserved.remove(_ip)

    def get_free_ip(self):
        """[Returns a free IP on the network, the very first available IP]
        
        Raises:
            OutOfIPs -- [Raised when no more IPs are available on the network]
        
        Returns:
            [ipaddress.IPv4Address] -- [Free ipaddress.IPv4Address]
        """
        available = self.available_ips
        if not available:
            raise OutOfIPs("Out of IPs.")
        return available[0]

    get_first_free_ip = get_free_ip

    def is_free_ip(self, ipaddr):
        """[Checks if IP ipaddr is free]
        
        Arguments:
            ipaddr {[str|ipaddress.IPv4Address]} -- [IP address to check if it's free or not.]
        
        Raises:
            ValueError -- [Raised for invalid IP ipaddr or if it's not in the network hosts]
        
        Returns:
            [bool] -- [returns if the IP ipaddr in the network hosts or not]
        """
        _ip = _as_ip4(ipaddr)
        if _ip not in self._network:
            raise j.exceptions.Value("{} not in network {}".format(ipaddr, self._network))
        return _ip not in self._reserved

    def __contains__(self, ipaddr):
        """[Checks if IP ipaddr with in the network host IP addresses]
        
        Arguments:
            ipaddr {[str|ipaddress.IPv4Address]} -- [IP address to check]
        
        Returns:
            [bool] -- [True if IP address within the network hosts IP addresses]
        """
        _ip = _as_ip4(ipaddr)
        return _ip in self._network

    hosts = ips


class IPPoolsManager:
    def __init__(self, pools=None):
        """[IPPoolManager manages getting/releasing free IPs]
        
        Arguments:
            pools {[List[IPPool]]} -- []
        """
        self._pools_dict = {p.id: p for p in pools}
        self._reserved_ips = {}

    @property
    def pools_ids(self):
        return list(self._pools_dict.keys())

    def manages_pool(self, pool_id):
        return pool_id in self._pools_dict

    def get_free_ip(self, pool_id):
        """[Get free IP address from a certain pool with id pool_id]
        
        Arguments:
            pool_id {[str]} -- [pool id]
        
        Returns:
            [Tuple[str, ipaddress.IPv4Address]] -- [tuple of pool id and reserved ip]
        """
        pool = self._pools_dict[pool_id]
        freeip = pool.get_free_ip()

        self._reserved_ips[freeip] = pool_id
        return (pool_id, pool.reserve_ip(freeip))

    def get_any_free_ip(self):
        """[Get a free IP]

        Returns:
            [Tuple[str, ipaddress.IPv4Address]] -- [tuple of pool id and reserved ip]
        """
        for pool_id, pool in self._pools_dict.items():
            try:
                pool_id, ip = self.get_free_ip(pool_id)
            except OutOfIPs as e:
                pass
            else:
                return (pool_id, ip)
        else:
            raise OutOfIPs("No IPs available on all pools.")

    def is_reserved_ip(self, ipaddr):
        """[Check if IP is reserved already]

        Arguments:
            ipaddr {[str|ipaddress.IPv4Address]} -- [IP address to check if reserved by any pool]


        Returns:
            [bool] -- [True if IP ipaddr is already reserved ]
        """
        _ip = _as_ip4(ipaddr)
        return _ip in self.reserved_ips

    def is_free_ip(self, ipaddr):
        """[Check if IP ipaddr is free]
        
        Arguments:
            ipaddr {[str|ipaddress.IPv4Address]} -- [IP address to check if free by any pool]

        
        Returns:
            [bool] -- [True if IP ipaddr is free and False otherwise]
        """
        return not self.is_reserved_ip(ipaddr)

    def release_ip(self, pool_id, ipaddr):
        """[Releases IP ipaddr from Pool identified by pool_id]
        
        Arguments:
            pool_id {[str]} -- [Pool id]
            ipaddr {[str|ipaddress.IPv4Address]} -- [IPv4 address]
        
        Raises:
            ValueError -- [If no pool is registered with id pool_id or ipaddr is invalid ip address or not within network hosts too]
        """
        pool = self._pools_dict.get(pool_id, None)
        if pool is None:
            raise j.exceptions.Value("No pool registered with id: {}".format(pool_id))
        _ip = _as_ip4(ipaddr)
        pool.release_ip(ipaddr)

    @property
    def available_ips(self):
        ips = []
        for p in self._pools_dict.values():
            ips.extend(p.available_ips)
        return ips

    available_hosts = available_ips

    @property
    def ips(self):
        ips = []
        for p in self._pools_dict.values():
            ips.extend(p.ips)
        return ips

    hosts = ips

    @property
    def reserved_ips(self):
        ips = []
        for p in self._pools_dict.values():
            ips.extend(p.reserved_ips)
        return ips

    reserved_hosts = reserved_ips
