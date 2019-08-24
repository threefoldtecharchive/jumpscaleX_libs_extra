import netaddr


def authorize_zerotiers(identify, nics):
    from JumpscaleLibsExtra.sal_zos.abstracts import ZTNic

    for nic in nics:
        if isinstance(nic, ZTNic):
            nic.authorize(identify)


def get_ip_from_nic(addrs):
    for ip in addrs:
        network = netaddr.IPNetwork(ip["addr"])
        if network.version == 4:
            return network.ip.format()


def get_zt_ip(nics, network=False, network_range=""):
    """[summary]
    Returns zerotier ip from a list of nics
    :param nics: a list of nic dicts
    :type nics: list
    :param network: a variable indicating if the ip should or should not be in network range <network_range>, defaults to False
    :param network: bool, optional
    :param network_range: the network range the ip should or should not be in, defaults to ''
    :param network_range: str, optional
    :return: [description]
    :rtype: [type]
    """
    if network and not network_range:
        raise j.exceptions.Base("Invalid network range")

    for nic in nics:
        if nic["name"].startswith("zt"):
            ipAdress = get_ip_from_nic(nic["addrs"])
            if not ipAdress:
                continue
            ip = netaddr.IPAddress(ipAdress)
            ip_network = netaddr.IPNetwork(network_range) if network_range else ""
            if network and network_range and ip not in ip_network:
                # required network range is not satisfied
                continue
            if not network and network_range and ip in ip_network:
                # network range should be avoided
                continue
            return ipAdress
