import netaddr
from zerotier.client import Client


class ZTBootstrap:
    def __init__(self, zt_token, bootstap_id, grid_id, cidr):

        self.bootstap_nwid = bootstap_id
        self.grid_nwid = grid_id
        self._cidr = cidr  # TODO validate format
        # create client and set the authentication header
        self._zt = Client()
        self._zt.set_auth_header("Bearer " + zt_token)

    def configure_routes(self):
        for nwid in [self.bootstap_nwid, self.grid_nwid]:
            resp = self._zt.network.getNetwork(nwid)
            resp.raise_for_status()
            nw = resp.json()
            nw["config"]["routes"] = [{"target": self._cidr, "via": None}]
            self._zt.network.updateNetwork(nw, nwid).raise_for_status()

    def list_join_request(self):
        """
        return a list of member that try to access the bootstap network
        """
        resp = self._zt.network.listMembers(id=self.bootstap_nwid)
        resp.raise_for_status()

        requests = []
        for member in resp.json():
            if not member["online"] or member["config"]["authorized"]:
                continue
            requests.append(member)

        return requests

    def assign_ip(self, nwid, member, ip=None):
        """
        Assign an Ip address to a member in a certain network
        @nwid : id of the network
        @member : member object
        @ip: ip address to assing to the member, if None take the next free IP in the range
        """
        if ip is None:
            ip = self._find_free_ip(nwid)
        member["config"]["authorized"] = True
        member["config"]["ipAssignments"] = [ip]
        resp = self._zt.network.updateMember(member, member["nodeId"], nwid)
        resp.raise_for_status()
        return ip

    def unauthorize_member(self, nwid, member):
        member["config"]["authorized"] = False
        member["config"]["ipAssignments"] = []
        resp = self._zt.network.updateMember(member, member["nodeId"], nwid)
        resp.raise_for_status()

    def _find_free_ip(self, nwid):

        resp = self._zt.network.listMembers(nwid)
        resp.raise_for_status()

        all_ips = list(netaddr.IPNetwork(self._cidr))
        for member in resp.json():
            for addr in member["config"]["ipAssignments"]:
                all_ips.remove(netaddr.IPAddress(addr))
        if len(all_ips) <= 0:
            raise j.exceptions.Base("No more free ip in the range %s" % self._cidr)
        return str(all_ips[0])


if __name__ == "__main__":
    token = "4gE9Cfqw2vFFzCPC1BYaj2mbSpNScxJx"
    bootstap_nwid = "17d709436c993670"
    grid_nwid = "a09acf02336ce8b5"

    zt = ZTBootstrap(token, bootstap_nwid, grid_nwid, "192.168.10.0/24")
    from IPython import embed

    embed()
