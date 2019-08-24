from Jumpscale import j

import time
import datetime

# import jose.jwt
# from paramiko.ssh_exception import BadAuthenticationType
JSBASE = j.baseclasses.object


class Machine(j.baseclasses.object):
    def __init__(self, space, machine):
        JSBASE.__init__(self)

        self.space = space
        self.client = space.client
        self.id = machine["id"]
        self._ssh_enabled = None
        self.refresh()

    def refresh(self):
        self._model = None
        self._prefab = None
        self._prefab_private = None
        self._sshclient = None
        self._sshclient_private = None
        self.deleted = False

    @property
    def name(self):
        return self.model["name"]

    @property
    def sshkeyname(self):
        if self.model["description"] is None:
            raise j.exceptions.Base("Could not find sshkeyname, description is empty")
        for line in self.model["description"].split("\n"):
            if line.strip().startswith("sshkeyname:"):
                return line.split(":")[-1].strip()
        raise j.exceptions.Base("Could not find sshkeyname")

    @property
    def model(self):
        """gets image model if it is not already in the cache"""

        def do():
            timeout = j.data.time.epoch + 20
            model = self.client.api.cloudapi.machines.get(machineId=self.id)
            while len(model["interfaces"]) == 0 or model["interfaces"][0]["ipAddress"] == "Undefined":
                if j.data.time.epoch > timeout:
                    raise j.exceptions.RuntimeError("Could not get IP Address for machine %(name)s" % model)
                time.sleep(1)
                model = self.client.api.cloudapi.machines.get(machineId=self.id)
            return model

        self._model = self._cache.get(key="model", method=do, expire=120)

        return self._model

    def start(self):
        self.client.api.cloudapi.machines.start(machineId=self.id)

    def stop(self):
        self.client.api.cloudapi.machines.stop(machineId=self.id)

    def restart(self):
        self.client.api.cloudapi.machines.reboot(machineId=self.id)

    def pause(self):
        self.client.api.cloudapi.machines.pause(machineId=self.id)

    def resume(self):
        self.client.api.cloudapi.machines.resume(machineId=self.id)

    def reset(self):
        self.client.api.cloudapi.machines.reset(machineId=self.id)

    def delete(self):
        self._log_info("Machine delete:%s" % self)
        self.client.api.cloudapi.machines.delete(machineId=self.id)
        j.tools.nodemgr.delete(self.name)
        self.deleted = True
        self.refresh()

    def clone(self, name, cloudspaceId=None, snapshotTimestamp=None):
        """Will create a new machine that is a clone of this one.

        :param name: the name of the clone that will be created.
        :type name: str
        :param cloudspaceId: id of the cloud space in which the machine should be put., defaults to None
        :param cloudspaceId: int, optional
        :param snapshotTimestamp: snapshot to base the clone upon., defaults to None
        :param snapshotTimestamp: int, optional
        :return: the id of the created machine
        :rtype: int
        """

        return self.client.api.cloudapi.machines.clone(
            machineId=self.id, name=name, cloudspaceId=cloudspaceId, snapshotTimestamp=snapshotTimestamp
        )

    def snapshot_create(self, name=None):
        """Will create a snapshot of the machine.

        :param name: date time string representing name of the snapshot that will be created, if none will use current time, defaults to None
        :param name: str, optional
        """

        if name is None:
            name = str(datetime.datetime.now())
        self.client.api.cloudapi.machines.snapshot(machineId=self.id, name=name)

    @property
    def snapshots(self):
        """
        Will return a list of snapshots of the machine.
        :return: the list of snapshots
        """
        return self.client.api.cloudapi.machines.listSnapshots(machineId=self.id)

    def snapshot_delete(self, epoch):
        """
        Will delete a snapshot of the machine.
        :param epoch: the epoch of the snapshot to be deleted.
        """
        self.client.api.cloudapi.machines.deleteSnapshot(machineId=self.id, epoch=epoch)

    def snapshot_rollback(self, epoch):
        """
        Will rollback a snapshot of the machine.
        :param epoch: the epoch of the snapshot to be rollbacked.
        """
        self.client.api.cloudapi.machines.rollbackSnapshot(machineId=self.id, epoch=epoch)

    def history_get(self, size):
        """get machine history

        :param size: number of entries to return
        :type size: int
        :return: list of dict containing actions on the machine
        :rtype: list
        """

        return self.client.api.cloudapi.machines.getHistory(machineId=self.id, size=size)

    def externalnetwork_attach(self):
        self.client.api.cloudapi.machines.attachExternalNetwork(machineId=self.id)

    def externalnetwork_detach(self):
        self.client.api.cloudapi.machines.detachExternalNetwork(machineId=self.id)

    def disk_add(self, name, description, size=10, type="D", ssdSize=0):
        """attach disk to the machine

        :param name: name of the disk
        :type name: str
        :param description: description info of the disk
        :type description: str
        :param size: size of the disk in Gbytes, defaults to 10
        :param size: int, optional
        :param type: type of the disk: B for boot disk D for data disk and T for temp, defaults to 'D'
        :param type: str, optional
        :param ssdSize: not implemented, defaults to 0
        :param ssdSize: int, optional
        :return: id of the attached disk
        :rtype: int
        """

        disk_id = self.client.api.cloudapi.machines.addDisk(
            machineId=self.id, diskName=name, description=description, size=size, type=type, ssdSize=ssdSize
        )
        return disk_id

    @property
    def disks(self):
        """
        Wrapper to list all disks related to a machine
        : return: list of disks details
        """
        machine_data = self.client.api.cloudapi.machines.get(machineId=self.id)
        return [disk for disk in machine_data["disks"] if disk["type"] != "M"]

    def disk_detach(self, disk_id):
        """
        Detach disk from the machine
        """
        return self.client.api.cloudapi.machines.detachDisk(machineId=self.id, diskId=disk_id)

    def disk_attach(self, disk_id):
        """
        Attach disk to the machine
        """
        return self.client.api.cloudapi.machines.attachDisk(machineId=self.id, diskId=disk_id)

    def disk_limit_io(
        self,
        disk_id,
        total_bytes_sec,
        read_bytes_sec,
        write_bytes_sec,
        total_iops_sec,
        read_iops_sec,
        write_iops_sec,
        total_bytes_sec_max,
        read_bytes_sec_max,
        write_bytes_sec_max,
        total_iops_sec_max,
        read_iops_sec_max,
        write_iops_sec_max,
        size_iops_sec,
        iops=50,
    ):
        self.client.api.cloudapi.disks.limitIO(
            diskId=disk_id,
            iops=iops,
            total_bytes_sec=total_bytes_sec,
            read_bytes_sec=read_bytes_sec,
            write_bytes_sec=write_bytes_sec,
            total_iops_sec=total_iops_sec,
            read_iops_sec=read_iops_sec,
            write_iops_sec=write_iops_sec,
            total_bytes_sec_max=total_bytes_sec_max,
            read_bytes_sec_max=read_bytes_sec_max,
            write_bytes_sec_max=write_bytes_sec_max,
            total_iops_sec_max=total_iops_sec_max,
            read_iops_sec_max=read_iops_sec_max,
            write_iops_sec_max=write_iops_sec_max,
            size_iops_sec=size_iops_sec,
        )

    @property
    def portforwards(self):
        def do():
            return self.client.api.cloudapi.portforwarding.list(cloudspaceId=self.space.id, machineId=self.id)

        return self._cache.get("portforwards", do, expire=120)

    def portforwards_delete(self):
        """delete all portforwards
        """
        for item in self.portforwards:
            print("portforwards_delete")
            from IPython import embed

            embed(colors="Linux")
            s

    def portforward_exist(self, publicport):
        for item in self.portforwards:
            if int(item["publicPort"]) == int(publicport):
                return True
        return False

    def portforward_create(self, publicport, localport, protocol="tcp", overwrite=True):
        """create portforward exposing specified port of the machine

        :param publicport: The exposed public port if none will select first available port in the cloudspace beginning with 2200
        :type publicport: int
        :param localport: machine port to expose
        :type localport: int
        :param protocol: protocol to use(tcp, udp), defaults to 'tcp'
        :param protocol: str, optional
        :param overwrite: delete public port if exists, defaults to True
        :param overwrite: bool, optional
        :raises RuntimeError: if machine is deleted
        :raises j.exceptions.RuntimeError: if protocol not udp or tcp
        :raises j.exceptions.RuntimeError: if creating a portforward fails
        :return: public and localport
        :rtype: tuple
        """

        if self.deleted:
            raise j.exceptions.Base("machine deleted cannot create portforward")

        self.space.model  # will make sure space is deployed
        self.model  # will make sure machine is deployed
        if protocol not in ["tcp", "udp"]:
            raise j.exceptions.RuntimeError("Protocol for portforward should be tcp or udp not %s" % protocol)

        if overwrite and publicport:
            self.portforward_delete(publicport)

        # define real publicport, override it by a generated one if needed
        if publicport is None:
            unavailable_ports = [int(portinfo["publicPort"]) for portinfo in self.space.portforwards]
            candidate = 2200

            while candidate in unavailable_ports:
                candidate += 1

        try:
            self.client.api.cloudapi.portforwarding.create(
                cloudspaceId=self.space.id,
                protocol=protocol,
                localPort=localport,
                machineId=self.id,
                publicIp=self.ipaddr_public,
                publicPort=publicport if publicport is not None else candidate,
            )

        except Exception as e:
            # if we have a conflict response, let's check something:
            # - if it's an auto-generated port, we probably hit a concurrence issue
            #   let's try again with a new port
            if str(e).startswith("409 Conflict") and publicport is None:
                return self.portforward_create(None, localport, protocol)
            raise j.exceptions.RuntimeError("Error while creating portforwarding: %s" % e)

        self._cache.reset()

        publicport = publicport if publicport is not None else candidate
        return (publicport, localport)

    def portforward_delete(self, publicport):
        """delete portforward

        :param publicport: public port to be deleted
        :type publicport: int
        """

        if self.portforward_exist(publicport):
            self.client.api.cloudapi.portforwarding.deleteByPort(
                cloudspaceId=self.space.id,
                publicIp=self.space.model["publicipaddress"],
                publicPort=publicport,
                proto="tcp",
            )
        self._cache.reset()

    def portforward_delete_by_id(self, pfid):
        """delete portforward by its id

        :param pfid: id of public port to be deleted
        :type pfid: int
        """
        self._cache.reset()
        self.client.api.cloudapi.portforwarding.delete(cloudspaceid=self.space.id, id=pfid)

    @property
    def ipaddr_priv(self):
        return self.model["interfaces"][0]["ipAddress"]

    @property
    def ipaddr_public(self):
        return self.space.model["publicipaddress"]

    @property
    def sshclient(self):
        if self.deleted:
            raise j.exceptions.Base("machine deleted")

        if self._sshclient is None:
            addr, port = self._ssh_info()
            key = self._ssh_client_key(addr, port, "root")
            self._sshclient = j.clients.ssh.new(
                instance=key,
                addr=addr,
                port=port,
                login="root",
                passwd="",
                keyname=self.sshkeyname,
                allow_agent=True,
                timeout=300,
                addr_priv=self.ipaddr_priv,
            )
        return self._sshclient

    @property
    def sshclient_private(self):
        if self.deleted:
            raise j.exceptions.Base("machine deleted")

        if self._sshclient_private is None:
            addr, port = self.ipaddr_priv, 22
            key = self._ssh_client_key(addr, port, "root", True)
            self._sshclient_private = j.clients.ssh.new(
                instance=key,
                addr=self.ipaddr_priv,
                port=22,
                login="root",
                passwd="",
                keyname=self.sshkeyname,
                allow_agent=True,
                timeout=300,
                addr_priv=self.ipaddr_priv,
            )
        return self._sshclient_private

    def _ssh_info(self):
        sp_pfs = self.space.portforwards
        internal_ip = self.model["interfaces"][0]["ipAddress"]  # TODO harden
        port = None
        addr = None
        for pf in sp_pfs:
            if pf["localIp"] == internal_ip and pf["localPort"] == "22":
                addr = pf["publicIp"]
                port = pf["publicPort"]

        # error if port 22 is not found
        if not addr or not port:
            raise j.exceptions.Base("VM '%s' doesn't have ssh port 22 exposed" % self.name)

        return addr, port

    def _ssh_client_key(self, addr, port, login, private=False):
        return "%s-%s-%s-%s" % (addr.replace(".", "-"), port, login, ("private" if private else "public"))

    def authorizeSSH(self, sshkeyname):
        """authorize specified sshkey to the machine

        :param sshkeyname: public sshkey string
        :type sshkeyname: str
        """

        login = self.model["accounts"][0]["login"]
        addr, port = self._ssh_info()
        instance = self._ssh_client_key(addr, port, login)
        self._authorize(sshkeyname, instance, addr, port, None)

    def authorizeSSH_private(self, sshkeyname):
        """authorize specified sshkey to the machine over the private network

        :param sshkeyname: public sshkey string
        :type sshkeyname: str
        """
        login = self.model["accounts"][0]["login"]
        addr, port = self.ipaddr_priv, 22
        instance = self._ssh_client_key(addr, port, login, True)
        self._authorize(sshkeyname, instance, addr, port, None)

    def _authorize(self, sshkeyname, instance, addr, port, priv_addr):
        login = self.model["accounts"][0]["login"]
        password = self.model["accounts"][0]["password"]

        sshclient = j.clients.ssh.new(
            instance=instance,
            addr=addr,
            port=port,
            login=login,
            passwd=password,
            keyname="",
            allow_agent=False,
            timeout=300,
        )
        try:
            sshclient.connect()
            sshclient.ssh_authorize(key=sshkeyname, user="root")
        finally:
            sshclient.config.delete()  # remove this temp sshconnection
            sshclient.close()
            # remove bad key from local known hosts file
            j.clients.sshkey.knownhosts_remove(addr)

        instance = self._ssh_client_key(addr, port, "root", priv_addr)
        self._sshclient = j.clients.ssh.new(
            instance=instance,
            addr=addr,
            port=port,
            login="root",
            passwd="",
            keyname=self.sshkeyname,
            allow_agent=True,
            timeout=300,
            addr_priv=self.ipaddr_priv,
        )

        j.tools.executor.reset()

    @property
    def ssh_ipaddr_public(self):
        """returns (addr,port)
        """

        def do():
            pubip = None
            sshport = None
            for portforward in self.space.portforwards:
                if portforward["localIp"] == self.ipaddr_priv and int(portforward["localPort"]) == 22:
                    pubip = portforward["publicIp"]
                    sshport = int(portforward["publicPort"])
                    break

            if not pubip:
                pubip = self.ipaddr_public

            if sshport is None:
                self._log_debug("did not find ssh portforward: will create")
                if not self._ssh_enabled:
                    self.portforward_create(None, 22)
                    self._ssh_enabled = True
                else:
                    raise j.exceptions.Base(
                        "Cannot find sshport at public side to access this machine, even after creation"
                    )

            return (pubip, sshport)

        return self._cache.get("ssh_ipaddr_public", do, expire=120)

    @property
    def executor(self):
        """gets an executor object

        :raises RuntimeError: in case the machine is deleted
        :return: executor object
        :rtype: object
        """

        if self.deleted:
            raise j.exceptions.Base("machine deleted")
        return j.tools.executor.ssh_get(self.sshclient)

    @property
    def executor_private(self):
        """gets an executor object to the private network

        :raises RuntimeError: in case the machine is deleted
        :return: executor object
        :rtype: object
        """
        if self.deleted:
            raise j.exceptions.Base("machine deleted")
        return j.tools.executor.ssh_get(self.sshclient_private)

    @property
    def prefab(self):
        """
        Will get a prefab executor for the machine.
        Will attempt to create a portforwarding

        the sshkeyname needs to be loaded in local ssh-agent (this is the only supported method!)

        login/passwd has been made obsolete, its too dangerous

        """
        if self.deleted:
            raise j.exceptions.Base("machine deleted")

        if self._prefab is None:
            self._prefab = j.tools.prefab.get(self.executor, usecache=False)
        return self._prefab

    @property
    def prefab_private(self):
        """
        Will get a prefab executor for the machine.
        Will attempt to create a portforwarding

        the sshkeyname needs to be loaded in local ssh-agent (this is the only supported method!)

        login/passwd has been made obsolete, its too dangerous

        """
        if self.deleted:
            raise j.exceptions.Base("machine deleted")

        if self._prefab_private is None:
            self._prefab_private = j.tools.prefab.get(self.executor_private, usecache=False)
        return self._prefab_private

    @property
    def node(self):
        if self.deleted:
            raise j.exceptions.Base("machine deleted")
        node = j.tools.nodemgr.get(self.name, create=False)
        return node

    @property
    def node_private(self):
        if self.deleted:
            raise j.exceptions.Base("machine deleted")
        node = j.tools.nodemgr.get(self.name + "_private", create=False)
        return node

    def __repr__(self):
        return "machine: %s (%s)\n%s" % (self.name, self.id, self.model)
        # return "machine: %s (%s)" % (self.name, self.id)

    __str__ = __repr__
