from Jumpscale import j

# import time
# import datetime
# import jose.jwt
# from paramiko.ssh_exception import BadAuthenticationType

from .Machine import Machine
from .Space import Space
from .Authorizables import Authorizables

JSBASE = j.baseclasses.object


class Account(Authorizables):
    def __init__(self, client, model):
        Authorizables.__init__(self)
        self.client = client
        self.model = model
        self.id = model["id"]

    @property
    def spaces(self):
        """returns all cloudspaces in the account"""
        ovc_spaces = self.client.api.cloudapi.cloudspaces.list()
        spaces = list()
        for space in ovc_spaces:
            if space["accountId"] == self.model["id"]:
                spaces.append(Space(self, space))
        return spaces

    @property
    def disks(self):
        """
        Wrapper to list all disks related to an account
        : return: list of disks details
        """
        return self.client.api.cloudapi.disks.list(accountId=self.id)

    def disk_delete(self, disk_id, detach=True):
        """delete disk by its id. I think there should be a class for disks to list all its wrappers

        :param disk_id: The disk id that needs to be removed
        :type disk_id: int
        :param detach: detach the disk from the machine first, defaults to True
        :param detach: bool, optional
        :return: true if deleted
        :rtype: bool
        """

        return self.client.api.cloudapi.disks.delete(diskId=disk_id, detach=detach)

    def space_get(
        self,
        name,
        location="",
        create=True,
        maxMemoryCapacity=-1,
        maxVDiskCapacity=-1,
        maxCPUCapacity=-1,
        maxNASCapacity=-1,
        maxNetworkOptTransfer=-1,
        maxNetworkPeerTransfer=-1,
        maxNumPublicIP=-1,
        externalnetworkId=None,
    ):
        """Returns the cloud space with the given name, and in case it doesn't exist yet the account will be created.

        :param name: name of the cloud space to lookup or create if it doesn't exist yet, e.g. "myvdc"
        :type name: [type]
        :param location: location when the cloud space needs to be created, defaults to ""
        :param location: str, optional only required when cloud space needs to be created
        :param create: if set to True the cloudspace is created in case it doesn't exist yet, defaults to True
        :param create: bool, optional 
        :param maxMemoryCapacity: available memory in GB for all virtual machines in the cloud space, defaults to -1
        :param maxMemoryCapacity: int, optional
        :param maxVDiskCapacity: available disk capacity in GiB for all virtual disks in the cloud space, defaults to -1(unlimited)
        :param maxVDiskCapacity: int, optional
        :param maxCPUCapacity: total number of available virtual CPU core that can be used by the virtual machines in the cloud space, defaults to -1(unlimited)
        :param maxCPUCapacity: int, optional
        :param maxNASCapacity: not implemented, defaults to -1(unlimited)
        :param maxNASCapacity: int, optional
        :param maxNetworkOptTransfer: not implemented, defaults to -1(unlimited)
        :param maxNetworkOptTransfer: int, optional
        :param maxNetworkPeerTransfer: maximum sent/received network transfer peer, defaults to -1(unlimited)
        :param maxNetworkPeerTransfer: int, optional
        :param maxNumPublicIP: number of external IP addresses that can be used in the cloud space, defaults to -1(unlimited)
        :param maxNumPublicIP: int, optional
        :param externalnetworkId: id of external network to connect to, defaults to None
        :param externalnetworkId: int, optional
        :raises j.exceptions.RuntimeError: if cloud space doesn't exist, and create argument was set to False
        :return: space object
        :rtype: object
        """

        if not location:
            location = self.client.config.data["location"]
        if location == "":
            self.client.config.data = {"location": self.client.locations[0]["name"]}
            self.client.config.save()
            location = self.client.config.data["location"]

        for space in self.spaces:
            if space.model["name"] == name and space.model["location"] == location:
                return space
        else:
            if create:
                self.client.api.cloudapi.cloudspaces.create(
                    access=self.client.login,
                    name=name,
                    accountId=self.id,
                    location=location,
                    maxMemoryCapacity=maxMemoryCapacity,
                    maxVDiskCapacity=maxVDiskCapacity,
                    maxCPUCapacity=maxCPUCapacity,
                    maxNASCapacity=maxNASCapacity,
                    maxNetworkOptTransfer=maxNetworkOptTransfer,
                    maxNetworkPeerTransfer=maxNetworkPeerTransfer,
                    maxNumPublicIP=maxNumPublicIP,
                    externalnetworkId=externalnetworkId,
                )
                return self.space_get(name, location, False)
            else:
                raise j.exceptions.RuntimeError("Could not find space with name %s" % name)

    def disk_create(self, name, gid, description, size=0, type="B", ssd_size=0):
        """create a new disk in the account

        :param name: name of the disk
        :type name: str
        :param gid: grid id to create the disk on
        :type gid: int
        :param description: description info of the disk
        :type description: str
        :param size: size of the disk in Gbytes, defaults to 0
        :param size: int, optional
        :param type: type of the disk: B for boot disk D for data disk and T for temp, defaults to "B"
        :param type: str, optional
        :param ssd_size: not implemented, defaults to 0
        :param ssd_size: int, optional
        :return: created disk id
        :rtype: int
        """

        res = self.client.api.cloudapi.disks.create(
            accountId=self.id, name=name, gid=gid, description=description, size=size, type=type, ssdSize=ssd_size
        )
        return res

    def _addUser(self, username, right):
        self.client.api.cloudapi.accounts.addUser(accountId=self.id, userId=username, accesstype=right)

    def _updateUser(self, username, right):
        self.client.api.cloudapi.accounts.updateUser(accountId=self.id, userId=username, accesstype=right)

    def _deleteUser(self, username):
        self.client.api.cloudapi.accounts.deleteUser(accountId=self.id, userId=username, recursivedelete=True)

    def get_consumption(self, start, end):
        """download the resources traking files for an account within a given period

        :param start: epoch representing the start time
        :type start: int
        :param end: epoch representing the end time
        :type end: int
        :return: consumption data
        :rtype: str
        """

        return self.client.api.cloudapi.accounts.getConsumption(accountId=self.id, start=start, end=end)

    def save(self):
        """Update account on env with current account object data"""
        self.client.api.cloudapi.accounts.update(
            accountId=self.model["id"],
            name=self.model["name"],
            maxMemoryCapacity=self.model.get("maxMemoryCapacity"),
            maxVDiskCapacity=self.model.get("maxVDiskCapacity"),
            maxCPUCapacity=self.model.get("maxCPUCapacity"),
            maxNASCapacity=self.model.get("maxNASCapacity"),
            maxNetworkOptTransfer=self.model.get("maxNetworkOptTransfer"),
            maxNetworkPeerTransfer=self.model.get("maxNetworkPeerTransfer"),
            maxNumPublicIP=self.model.get("maxNumPublicIP"),
        )

    def refresh(self):
        """refresh current account object"""
        accounts = self.client.api.cloudapi.accounts.list()
        found = False
        for account in accounts:
            if account["id"] == self.id:
                self.model = account
                found = True
                break
        if not found:
            raise j.exceptions.RuntimeError(
                "No account found with name %s. The user doesn't have access to the account or it is been deleted."
                % self.model["name"]
            )

    def delete(self):
        """Delete current account"""
        self.client.api.cloudbroker.account.delete(accountId=self.id, reason="API request")

    def get_available_images(self, cloudspaceId=None):
        """lists all available images for a cloud space

        :param cloudspaceId: if specified will list images only for specified cloudspace, defaults to None
        :param cloudspaceId: int, optional
        :return: list of dict representing image info
        :rtype: list
        """

        return self.client.api.cloudapi.images.list(cloudspaceId=cloudspaceId, accountId=self.id)

    def __str__(self):
        return "OpenvCloud client account: %(name)s" % (self.model)

    __repr__ = __str__
