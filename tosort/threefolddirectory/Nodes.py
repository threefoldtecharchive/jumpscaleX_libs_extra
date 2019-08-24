from Jumpscale import j


class Node(j.baseclasses.object_config):
    """
    one farmer instance
    """

    _SCHEMATEXT = """
        @url = threefold.grid.node
        
        name* = ""
        
        node_zos_id* = ""               #zero os id of the host
        node_zerotier_id* = ""          #zerotier id
        node_public_ip* = ""            #node public ip address
        
        description = ""
        
        macaddresses = [] (LS)          #list of macaddresses found of this node
        
        noderobot = (B)                #could access the node robot (did answer)
        noderobot_up_last = (D)        #last time that the noderobot was up (last check)
        noderobot_ipaddr = ""          #ipaddress where to contact the noderobot
        
        sysadmin = (B)                 #is accessible over sysadmin network for support?
        sysadmin_up_ping = (B)         #ping worked over sysadmin zerotier
        sysadmin_up_zos = (B)          #zeroos was reachable (over redis for support = sysadmin
        sysadmin_up_last = (D)         #last time that this node was up on sysadmin network
        sysadmin_ipaddr = ""           #ipaddress on sysadmin network
        
        tfdir_found = (B)              #have found the reservation in the threefold dir
        tfdir_up_last = (D)            #date of last time the node was updated in the threefold dir
        
        tfgrid_up_ping = (B)           #ping worked on zerotier public network for the TF Grid
        tfgrid_up_last = 0 (D)         #last date that we saw this node to be up (accessible over ping on pub zerotier net)
        
        state = ""                     #OK, ERROR, INIT
        
        error = ""                      #there is an error on this node
        
        farmer_id* = (S)
        farmer = false (B)
        update = (D)
        
        capacity_reserved = (O) !threefold.grid.capacity.reserved
        capacity_used = (O) !threefold.grid.capacity.used
        capacity_total = (O) !threefold.grid.capacity.total
        location = (O) !threefold.grid.capacity.location
        
        
        @url = threefold.grid.capacity.reserved
        mru = 0 (F)            #nr of units reserved
        cru = 0 (F)
        hru = 0 (F)
        sru = 0 (F)
        
        @url = threefold.grid.capacity.used
        mru = 0 (F)            #nr of units used in the box
        cru = 0 (F)
        hru = 0 (F)
        sru = 0 (F)
        
        @url = threefold.grid.capacity.total
        mru = 0 (F)            #nr of units total in the box
        cru = 0 (F)
        hru = 0 (F)
        sru = 0 (F)
        
        
        @url = threefold.grid.capacity.location
        country = ""
        city = ""
        continent = ""
        latitude = (F)
        longitude = (F)

        """

    def _init(self, **kwargs):
        pass

    @staticmethod
    def _ping(ipaddr):
        """

        :param ipaddr:
        :return: empty string if ping was ok
        """
        active = False
        counter = 0
        error = ""
        while not active and counter < 4:
            try:
                active = j.sal.nettools.pingMachine(ipaddr)
            except Exception as e:
                if "packet loss" in str(e):
                    print("ping fail for:%s" % ipaddr)
                    counter += 1
                    error = "packet loss"
                else:
                    error = str(e)
        return error

    def check(self, dir_item=None, jwt=None, reset=False):
        """
        will do ping test, zero-os test, ...

        :param reset: reset saved node info
        """

        raise NotImplemented()
        if self.update > j.data.time.epoch - 3600 and not reset:
            print("NOT NEEDED TO UPDATE:")
            print(self.node_zos_id)
            return

        self.sysadmin = False
        self.error = ""
        self.noderobot = False
        self.sysadmin_up_ping = False
        self.sysadmin_up_zos = False
        self.tfdir_found = False
        self.tfgrid_up_ping = False

        ipaddr = self.sysadmin_ipaddr

        # PING TEST on sysadmin network
        error = self._ping(ipaddr)
        sysadmin_ping = error == ""

        # ZOSCLIENT
        zos = None
        try:
            zos = j.clients.zos.get(data={"password_": jwt, "host": ipaddr}, instance="sysadmin_%s" % ipaddr)
        except Exception as e:
            if "Connection refused" in str(e):
                error = "connection refused zosclient"
            else:
                error = str(e)

        zos_ping = False
        if zos:
            try:
                zos_ping = "PONG" in zos.client.ping()
                self.sysadmin_up_last = j.data.time.epoch
                self.sysadmin_up_zos = j.data.time.epoch
            except Exception as e:
                if "Connection refused" in str(e):
                    zos_ping = False
                    error = "connection refused ping"
                else:
                    error = str(e)

        if sysadmin_ping and zos_ping:
            self.sysadmin = True
            self.node_zos_id = zos.name  # zos.client.infself.os()['hostid']

        dir_item = self._tf_dir_node_find(ipaddr, self.node_zos_id)
        dir_item = None
        self.sysadmin_up_ping = sysadmin_ping
        self.sysadmin_up_zos = zos_ping
        if self.error is not "zerotier lost the connection to the node":
            self.error = error

        robot = self.robot_get(o)
        if False and robot:
            if len(robot.templates.uids.keys()) > 0:
                self.noderobot = True
                self.noderobot_up_last = j.data.time.epoch
                self.state = "OK"

        self.tfdir_up_last = ""
        self.tf_dir_found = bool(dir_item)

        self.update = j.data.time.epoch  # last time this check was done

        self.save()
        print(self)

    def from_dir(self, dir_item):
        if dir_item is not None:
            self.farmer_id = dir_item["farmer_id"]
            self.node_zos_id = dir_item["node_id"]
            self.node_robot = dir_item["robot_address"]
            if dir_item["reserved_resources"]:
                self.capacity_reserved.cru = dir_item["reserved_resources"]["cru"]
                self.capacity_reserved.hru = dir_item["reserved_resources"]["hru"]
                self.capacity_reserved.mru = dir_item["reserved_resources"]["mru"]
                self.capacity_reserved.sru = dir_item["reserved_resources"]["sru"]

            if dir_item["total_resources"]:
                self.capacity_total.cru = dir_item["total_resources"]["cru"]
                self.capacity_total.hru = dir_item["total_resources"]["hru"]
                self.capacity_total.mru = dir_item["total_resources"]["mru"]
                self.capacity_total.sru = dir_item["total_resources"]["sru"]

            if dir_item["used_resources"]:
                self.capacity_used.cru = dir_item["used_resources"]["cru"]
                self.capacity_used.hru = dir_item["used_resources"]["hru"]
                self.capacity_used.mru = dir_item["used_resources"]["mru"]
                self.capacity_used.sru = dir_item["used_resources"]["sru"]

            self.tfdir_found = True

            self.tfdir_up_last = dir_item["updated"]

            self.noderobot_ipaddr = dir_item["robot_address"]

            if dir_item.get("location"):
                self.location.city = dir_item["location"]["city"]
                self.location.continent = dir_item["location"]["continent"]
                self.location.country = dir_item["location"]["country"]
                self.location.latitude = dir_item["location"]["latitude"]
                self.location.longitude = dir_item["location"]["longitude"]

            self.tfdir_found = True
            self.tfdir_up_last = dir_item["updated"]
            self.save()


class Nodes(j.baseclasses.objects_config_bcdb):
    """
    ...
    """

    _CHILDCLASS = Node
