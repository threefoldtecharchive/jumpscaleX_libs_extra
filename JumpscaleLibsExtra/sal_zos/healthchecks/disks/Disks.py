from enum import Enum

from ..abstracts import Mountable
from .Partition import Partition
from Jumpscale import j


class StorageType(Enum):
    SSD = "SSD"
    HDD = "HDD"
    NVME = "NVME"
    ARCHIVE = "ARCHIVE"
    CDROM = "CDROM"


class Disks:

    """Subobject to list disks"""

    def __init__(self, node):
        self.node = node

    @property
    def client(self):
        return self.node.client

    def list(self):
        """
        List of disks on the node
        """
        disks = []
        for disk_info in self.client.disk.list():
            disks.append(Disk(node=self.node, disk_info=disk_info))
        return disks

    def get(self, name):
        """
        return the disk called `name`
        @param name: name of the disk
        """
        for disk in self.list():
            if disk.name == name:
                return disk
        return None

    def get_device(self, name):
        """
        Get device can be either disk or partition

        @param name: partition or disk name
        @type name: str
        @return: Disk or Partition
        @rtype: Disk Partition
        """
        for disk in self.list():
            if disk.devicename == name:
                return disk
            for partition in disk.partitions:
                if partition.devicename == name:
                    return partition
        raise j.exceptions.NotFound("Could not find device with name {}".format(name))


class Disk(Mountable):
    """Disk in a Zero-OS"""

    def __init__(self, node, disk_info):
        """
        disk_info: dict returned by client.disk.list()
        """
        # g8os client to talk to the node
        Mountable.__init__(self)
        self.node = node
        self.name = None
        self.size = None
        self.blocksize = None
        self.partition_table = None
        self.mountpoint = None
        self.model = None
        self._filesystems = []
        self._type = None
        self.partitions = []
        self.transport = None
        self._disk_info = disk_info

        self._load(disk_info)

    @property
    def client(self):
        return self.node.client

    @property
    def devicename(self):
        return "/dev/{}".format(self.name)

    @property
    def filesystems(self):
        self._populate_filesystems()
        return self._filesystems

    @property
    def type(self):
        """
        return the type of the disk
        """
        if self._type is None:
            if self._disk_info["type"] == "rom":
                self._type = StorageType.CDROM
            else:
                res = self.node.client.disk.seektime(self.devicename)

                # assume that if a disk is more than 7TB it's a SMR disk
                if res["type"] == "HDD":
                    if int(self._disk_info["size"]) > (1024 * 1024 * 1024 * 1024 * 7):
                        self._type = StorageType.ARCHIVE
                    else:
                        self._type = StorageType.HDD
                elif res["type"] in ["SSD", "SDD"]:
                    if "nvme" in self._disk_info["name"]:
                        self._type = StorageType.NVME
                    else:
                        self._type = StorageType.SSD
        return self._type

    def _load(self, disk_info):
        self.name = disk_info["name"]
        self.size = int(disk_info["size"])
        self.blocksize = disk_info["blocksize"] if "blocksize" in disk_info else None
        if "table" in disk_info and disk_info["table"] != "unknown":
            self.partition_table = disk_info["table"]
        self.mountpoint = disk_info["mountpoint"]
        self.model = disk_info["model"]
        self.transport = disk_info["tran"]
        for partition_info in disk_info.get("children", []) or []:
            self.partitions.append(Partition(disk=self, part_info=partition_info))

    def _populate_filesystems(self):
        """
        look into all the btrfs filesystem and populate
        the filesystems attribute of the class with the detail of
        all the filesystem present on the disk
        """
        disk_devices_names = [self.devicename]
        disk_devices_names.extend([part.devicename for part in self.partitions])

        self._filesystems = []
        for fs in self.client.btrfs.list() or []:
            for device in fs["devices"]:
                if device["path"] in disk_devices_names:
                    self._filesystems.append(fs)

    def mktable(self, table_type="gpt", overwrite=False):
        """
        create a partition table on the disk
        @param table_type: Partition table type as accepted by parted
        @param overwrite: erase any existing partition table
        """
        if self.partition_table is not None and overwrite is False:
            return

        self.client.disk.mktable(disk=self.name, table_type=table_type)

    def mkpart(self, start, end, part_type="primary"):
        """
        @param start: partition start as accepted by parted mkpart
        @param end: partition end as accepted by parted mkpart
        @param part_type: partition type as accepted by parted mkpart
        """
        before = {p.name for p in self.partitions}

        self.client.disk.mkpart(self.name, start=start, end=end, part_type=part_type)
        after = {}
        for disk in self.client.disk.list():
            if disk["name"] != self.name:
                continue
            for part in disk.get("children", []):
                after[part["name"]] = part
        name = set(after.keys()) - before

        part_info = after[list(name)[0]]
        partition = Partition(disk=self, part_info=part_info)
        self.partitions.append(partition)

        return partition

    def __str__(self):
        return "Disk <{}>".format(self.name)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.devicename == other.devicename
