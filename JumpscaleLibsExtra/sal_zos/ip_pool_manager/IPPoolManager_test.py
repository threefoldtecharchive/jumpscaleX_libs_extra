import pytest
from unittest import TestCase
from .IPPoolManager import IPPool, IPPoolsManager, _as_ip4, OutOfIPs
import ipaddress


def test_as_ip4_of_string_returns_ip4address():
    ip = _as_ip4("192.168.20.3")
    assert isinstance(ip, ipaddress.IPv4Address)


def test_as_ip4_of_ip4address_returns_ip4address():
    ip = _as_ip4(ipaddress.IPv4Address("192.168.20.3"))
    assert isinstance(ip, ipaddress.IPv4Address)


def test_as_ip4_of_invalid_str_raises():
    with pytest.raises(ValueError):
        _as_ip4("123.2.31")


class TestIPPool(TestCase):
    def setUp(self):
        # For this pool 192.168.20.0 the available hosts IPs should be
        # ['192.168.20.1','192.168.20.2', '192.168.20.3', '192.168.20.4','192.168.20.5','192.168.20.6']
        # hosts are the full range - 192.168.20.3
        self._HOSTS = ["192.168.20.1", "192.168.20.2", "192.168.20.3", "192.168.20.5", "192.168.20.6"]
        self.p = IPPool(id="pool_1", name="poolname", network_address="192.168.20.0/29", registered_ips=self._HOSTS)
        self.pool_full_range_hosts = IPPool(id="pool_2", name="pool2name", network_address="192.168.20.0/29")

    def test_subnetmask(self):
        assert str(self.p.subnetmask) == "255.255.255.248"

    def test_len_ips_equals_len_hosts(self):
        assert len(self.p.ips) == len(self.p.hosts)

    def test_len_available_hosts_equals_len_available_ips(self):
        assert len(self.p.available_hosts) == len(self.p.available_ips)

    def test_ips_after_first_pool_creation_equal_available_ips(self):
        assert len(self.p.available_hosts) == len(self.p.available_ips) == len(self.p.ips) == len(self._HOSTS)

    def test_is_free_ip(self):
        for ip in self._HOSTS:
            assert self.p.is_free_ip(ip)

    def test_get_free_ip(self):
        ip = self.p.get_free_ip()
        assert str(ip) in self._HOSTS

    def test_pool_gets_network_range_if_no_registered_ips(self):
        assert len(self.pool_full_range_hosts.available_ips) == len(self._HOSTS) + 1

    def test_pool_doesnt_get_network_range_if_registered_ips(self):
        assert len(self.p.available_ips) == len(self._HOSTS)

    def test_cant_reserve_networkaddress(self):
        with pytest.raises(ValueError):
            self.p.reserve_ip(self.p._network.network_address)

    def test_cant_reserve_broadcastaddress(self):
        with pytest.raises(ValueError):
            self.p.reserve_ip(self.p._network.broadcast_address)

    def test_cant_reserve_loopback(self):
        with pytest.raises(ValueError):
            self.p.reserve_ip("127.0.0.1")

    def test_cant_reserve_ip_out_of_another_network(self):
        with pytest.raises(ValueError):
            self.p.reserve_ip("172.17.0.3")

    def test_cant_reserve_ip_out_of_network_hosts(self):
        with pytest.raises(ValueError):
            self.p.reserve_ip("192.168.20.19")

    def test_len_available_ips_after_reserving_two_ips(self):
        ip1 = self.p.get_first_free_ip()
        self.p.reserve_ip(ip1)
        assert len(self.p.reserved_ips) == 1
        assert len(self.p.available_ips) == len(self.p.registered_ips) - len(self.p.reserved_ips)
        ip2 = self.p.get_first_free_ip()
        self.p.reserve_ip(ip2)
        assert len(self.p.reserved_ips) == 2
        assert len(self.p.available_ips) == len(self.p.registered_ips) - len(self.p.reserved_ips)

    def test_len_reserved_ips_after_releasing_two_ips(self):
        ip1 = self.p.get_first_free_ip()
        self.p.reserve_ip(ip1)
        assert len(self.p.reserved_ips) == 1
        assert len(self.p.available_ips) == len(self.p.registered_ips) - len(self.p.reserved_ips)

        ip2 = self.p.get_first_free_ip()
        self.p.reserve_ip(ip2)
        assert len(self.p.reserved_ips) == 2
        assert len(self.p.available_ips) == len(self.p.registered_ips) - len(self.p.reserved_ips)

        self.p.release_ip(ip1)
        assert len(self.p.reserved_ips) == 1
        assert len(self.p.available_ips) == len(self.p.registered_ips) - len(self.p.reserved_ips)

        self.p.release_ip(ip2)
        assert len(self.p.reserved_ips) == 0
        assert len(self.p.available_ips) == len(self.p.registered_ips) - len(self.p.reserved_ips)

    def test_cant_reserve_more_than_allowed_hosts(self):
        with pytest.raises(OutOfIPs):
            for i in range(len(self._HOSTS) + 1):
                ip = self.p.get_first_free_ip()
                self.p.reserve_ip(ip)


class TestIPPoolManager(TestCase):
    def setUp(self):
        self.p1 = IPPool(id="pool_1", name="devnet", network_address="192.168.20.0/29")
        self.p2 = IPPool(id="pool_2", name="opsnet", network_address="192.128.23.0/30")
        self.mgr = IPPoolsManager(pools=[self.p1, self.p2])

    def test_manager_manages_pools(self):
        assert self.mgr.manages_pool(self.p1.id) is True
        assert self.mgr.manages_pool(self.p2.id) is True
        assert self.mgr.manages_pool("unknownpool") is False

    def test_get_free_ip_belongs_to_one_of_the_managed_pools(self):
        pool_id, ip = self.mgr.get_free_ip("pool_1")
        assert pool_id in self.mgr.pools_ids

    def test_get_any_free_ip_belongs_to_one_of_the_managed_pools(self):
        pool_id, ip = self.mgr.get_any_free_ip()
        assert pool_id in self.mgr.pools_ids

    def test_reserving_ip_doesnt_make_it_available(self):
        pool_id, ip = self.mgr.get_any_free_ip()
        assert ip not in self.mgr.available_ips

    def test_reserving_ip_makes_it_reserved(self):
        pool_id, ip = self.mgr.get_any_free_ip()
        assert self.mgr.is_reserved_ip(ip) is True

    def test_is_free_ip(self):
        pool_id, ip = self.mgr.get_any_free_ip()
        assert self.mgr.is_reserved_ip(ip) is True
        self.mgr.release_ip(pool_id, ip)
        assert self.mgr.is_reserved_ip(ip) is False
        assert self.mgr.is_free_ip(ip) is True

    def test_all_available_ips_equals_sum_of_ips_in_registered_pools(self):
        assert len(self.mgr.available_ips) == 8 == sum(len(p.available_ips) for p in [self.p1, self.p2])

    def test_reserving_two_ips_decreases_available_ips_by_two(self):
        pool_id1, ip1 = self.mgr.get_any_free_ip()
        pool_id2, ip2 = self.mgr.get_any_free_ip()
        assert len(self.mgr.ips) > len(self.mgr.available_ips) and (
            len(self.mgr.ips) - len(self.mgr.available_ips) == 2
        )
        assert len(self.mgr.ips) == len(self.mgr.available_ips) + len(self.mgr.reserved_ips)

    def test_releasing_two_ips_increases_available_ips(self):

        pool_id1, ip1 = self.mgr.get_any_free_ip()
        pool_id2, ip2 = self.mgr.get_any_free_ip()
        assert len(self.mgr.ips) > len(self.mgr.available_ips) and (
            len(self.mgr.ips) - len(self.mgr.available_ips) == 2
        )
        assert len(self.mgr.ips) == len(self.mgr.available_ips) + len(self.mgr.reserved_ips)

        self.mgr.release_ip(pool_id1, ip1)
        self.mgr.release_ip(pool_id2, ip2)
        assert len(self.mgr.ips) == 8
        assert len(self.mgr.reserved_ips) == 0

    def test_manager_raises_outofip(self):
        with pytest.raises(OutOfIPs):
            for i in range(9):
                pool_id, ip = self.mgr.get_any_free_ip()
