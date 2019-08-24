from Jumpscale import j
from .Farmers import *
from .Nodes import *


class ThreeFoldDirectory(j.application.JSFactoryConfigsBaseClass):

    __jslocation__ = "j.tools.threefold_directory"
    _CHILDCLASSES = [Farmers, Nodes]

    def _init(self, **kwargs):
        self._zerotier_client = None
        self._zerotier_net_sysadmin = None
        # self.zerotier_net_tfgrid = self.zerotier_client.network_get("") #TODO:*1
        self._iyo = None
        self._jwt = None

    @property
    def zerotier_client(self):
        if not self._zerotier_client:
            if not j.clients.zerotier.exists("sysadmin"):
                raise j.exceptions.Base(
                    "Please configure your zerotier sysadmin client: j.clients.zerotier.get(name='sysadmin', token_=TOKEN)"
                )
            self._zerotier_client = j.clients.zerotier.get("sysadmin")
        return self._zerotier_client

    @property
    def zerotier_net_sysadmin(self):
        if not self._zerotier_net_sysadmin:
            self._zerotier_net_sysadmin = self.zerotier_client.network_get(
                "1d71939404587f3c"
            )  # don't change the nr is fixed
        return self._zerotier_net_sysadmin

    @property
    def iyo(self):
        if not self._iyo:
            self._iyo = j.clients.itsyouonline.get()
        return self._iyo

    @property
    def jwt(self):
        if not self._jwt:
            self._jwt = self.iyo.jwt_get(refreshable=True, scope="user:memberof:threefold.sysadmin")
        return self._jwt

    def farmer_get(self, name):
        if self.farmers.exists(name=name):
            return self.farmers.get(name=name)
        else:
            return self.farmers.new(name=name)

    def farmers_load(self):
        """
        will get all farmers from tf directory & load in BCDB
        """
        farmers = j.clients.threefold_directory.farmers
        for farmer in farmers:
            if not farmer.get("name"):
                continue
            obj = self.farmers.get(name=farmer["name"])
            for wallet_addr in farmer["wallet_addresses"]:
                if wallet_addr not in obj.wallets:
                    obj.wallets.append(wallet_addr)
            obj.iyo_org = farmer["iyo_organization"]
            obj.save()

    def node_get(self, zerotier_addr=None, die=False):
        res = self.node_find(zerotier_addr=zerotier_addr)
        if len(res) == 0:
            if die:
                raise j.exceptions.Base("could not find node: zerotier_addr=%s" % (zerotier_addr))
            return None
        elif len(res) > 1:
            raise j.exceptions.Base("found too many nodes, should only be 1: zerotier_addr=%s" % (zerotier_addr))
        else:
            return res[0]

    def node_find(self, zerotier_addr=None):  # TODO: needs to be extended by more arguments
        # am doing rather brute force because think sqlite indexing is broken
        res = []
        for node in self.nodes.find():
            found = True
            if zerotier_addr:
                if node.node_zerotier_id != zerotier_addr:
                    found = False
            if found:
                res.append(node)
        return res

    def zerotier_scan(self, reset=False):
        """
        will do a scan of the full zerotier sysadmin network, this can take a long time
        :return:

        kosmos 'j.tools.threefold_directory.zerotier_scan()'

        """
        for node in self.zerotier_net_sysadmin.members_list():
            online = node.data["online"]  # online from zerotier
            # online_past_sec = int(j.data.time.epoch - node.data["lastOnline"] / 1000)
            ipaddr = node.data["config"]["ipAssignments"][0]
            if online:
                o = self.node_get(zerotier_addr=node.address, die=False)
                if not o:
                    o = self.nodes.new(name="zt_%s" % node.address)
                    o.sysadmin_ipaddr = ipaddr
                    o.node_zerotier_id = node.address
                    o.save()
                o.check(jwt=o.jwt, reset=reset)

    def tfdir_scan(self, reset=False):
        for node in j.clients.threefold_directory.capacity:
            o = self.nodes.get(name="tf_{}".format(node["node_id"]))
            o.from_dir(node)
            o.save()

    def get_farmer_nodes(self, farmer_id):
        if not self.farmers.find(iyo_org=farmer_id):
            return []
        else:
            return [node for node in self.nodes.find() if node.farmer_id == farmer_id]

    def scan(self):
        """
        kosmos 'j.tools.threefold_directory.scan()'
        """
        self.farmers_load()
        self.tfdir_scan()
        # self.zerotier_scan()
