import logging
import os
import time

from Jumpscale import j

from ..abstracts import Mountable
from ..disks.Disks import Disk
from ..disks.Partition import Partition

logging.basicConfig(level=logging.INFO)


def _prepare_device(node, devicename):
    j.tools.logger._log_debug("prepare device %s", devicename)
    ss = devicename.split("/")
    if len(ss) < 3:
        raise j.exceptions.Base("bad device name: {}".format(devicename))
    name = ss[2]

    disk = node.disks.get(name)
    if disk is None:
        raise j.exceptions.Value("device {} not found".format(name))

    node.client.system("parted -s /dev/{} mklabel gpt mkpart primary 1m 100%".format(name)).get()
    now = time.time()
    # check partitions is ready and writable
    while now + 60 > time.time():
        try:
            disk = node.disks.get(name)
            if len(disk.partitions) > 0:
                partition = disk.partitions[0]
                resp = node.client.bash(
                    "test -b {0} && dd if={0} of=/dev/null bs=4k count=1024".format(partition.devicename)
                ).get()
                if resp.state == "SUCCESS":
                    return partition
        except:
            time.sleep(1)
            continue
    else:
        raise j.exceptions.Base("Failed to create partition")


class StoragePools:
    def __init__(self, node):
        self.node = node

    @property
    def client(self):
        return self.node.client

    def list(self, fs_uuid=None):
        """
        list storage pools in a node
        :param fs_uuid: a filesystem uuid. If supplied the function only returns the storagepools that have this filesystem
        :return: list of StoragePool
        """
        storagepools = []
        btrfs_list = self.client.btrfs.list()
        for btrfs in btrfs_list:
            if btrfs["label"].startswith("sp_"):
                name = btrfs["label"].split("_", 1)[1]
                if not btrfs["devices"]:
                    continue
                device = btrfs["devices"][0]["path"]
                if (fs_uuid and btrfs["uuid"] == fs_uuid) or not fs_uuid:
                    storagepools.append(StoragePool(self.node, name, device))
        return storagepools

    def get(self, name):
        for pool in self.list():
            if pool.name == name:
                return pool
        raise j.exceptions.Value("Could not find StoragePool with name {}".format(name))

    def create(self, name, device, metadata_profile, data_profile, overwrite=False):
        if not isinstance(device, str):
            raise j.exceptions.Value("device must be a string not %s" % type(device))

        label = "sp_{}".format(name)
        j.tools.logger._log_debug("create storagepool %s", label)

        part = _prepare_device(self.node, device)

        self.client.btrfs.create(label, [part.devicename], metadata_profile, data_profile, overwrite=overwrite)
        pool = StoragePool(self.node, name, part.devicename)
        return pool


class StoragePool(Mountable):
    def __init__(self, node, name, device):
        self.node = node
        self.device = device
        self.name = name
        self._mountpoint = None

    @property
    def client(self):
        return self.node.client

    @property
    def type(self):
        medium = self.node.disks.get_device(self.device)
        if isinstance(medium, Disk):
            return medium.type
        elif isinstance(medium, Partition):
            return medium.disk.type

        raise j.exceptions.Base("unsupported device type")

    @property
    def devicename(self):
        return "UUID={}".format(self.uuid)

    def mount(self, target=None):
        if target is None:
            target = os.path.join("/mnt/storagepools/{}".format(self.name))
        return super().mount(target)

    def delete(self, zero=True):
        """
        Destroy storage pool
        param zero: write zeros (nulls) to the first 500MB of each disk in this storagepool
        """
        while self.mountpoint:
            self.umount()
        partition = None

        diskpath = os.path.basename(self.device)
        for disk in self.node.disks.list():
            for part in disk.partitions:
                if part.fs_uuid == self.uuid:
                    partition = part
                    break
            if partition:
                break

        if partition:
            disk = partition.disk
            self.client.disk.rmpart(disk.name, 1)
            if zero:
                self.client.bash(
                    "test -b /dev/{0} && dd if=/dev/zero bs=1M count=500 of=/dev/{0}".format(diskpath)
                ).get()
        return

    @property
    def mountpoint(self):
        mounts = self.node.list_mounts()
        for mount in mounts:
            if mount.device == self.device:
                options = mount.options.split(",")
                if "subvol=/" in options:
                    return mount.mountpoint

    @property
    def fsinfo(self):
        if self.mountpoint is None:
            raise j.exceptions.Value("can't get fsinfo if storagepool is not mounted")
        return self.client.btrfs.info(self.mountpoint)

    @mountpoint.setter
    def mountpoint(self, value):
        # do not do anything mountpoint is dynamic
        return

    def _get_mountpoint(self):
        mountpoint = self.mountpoint
        if not mountpoint:
            raise j.exceptions.Base("Can not perform action when filesystem is not mounted")
        return mountpoint

    @property
    def info(self):
        for fs in self.client.btrfs.list():
            if fs["label"] == "sp_{}".format(self.name):
                return fs
        return None

    def total_quota(self):
        return sum([subvol["Quota"] for subvol in self.raw_list()])

    def raw_list(self):
        mountpoint = self._get_mountpoint()
        return self.client.btrfs.subvol_list(mountpoint) or []

    def get_device_and_status(self):
        disks = self.client.disk.list()
        pool_status = "healthy"
        info = None
        for disk in disks:
            disk_name = "/dev/%s" % disk["kname"]
            for part in disk.get("children", []) or []:
                if self.uuid == part["uuid"]:
                    info = part
                    break
            if not info:
                continue

            status = "healthy"
            if info["subsystems"] != "block:virtio:pci":
                result = self.client.bash("smartctl -H %s > /dev/null ;echo $?" % disk_name).get()
                exit_status = int(result.stdout)

                if exit_status & 1 << 0:
                    status = "unknown"
                    pool_status = "degraded"
                if (exit_status & 1 << 2) or (exit_status & 1 << 3):
                    status = "degraded"
                    pool_status = "degraded"

            device = {"device": self.device, "partUUID": info["partuuid"] or "" if info else "", "status": status}

            return device, pool_status
        raise j.exceptions.Base("Failed to find device {}".format(self.device))

    def list(self):
        subvolumes = []
        for subvol in self.raw_list():
            path = subvol["Path"]
            type_, _, name = path.partition("/")
            if type_ == "filesystems":
                subvolumes.append(FileSystem(name, self))
        return subvolumes

    def get(self, name):
        """
        Get Filesystem
        """
        for filesystem in self.list():
            if filesystem.name == name:
                return filesystem
        raise j.exceptions.Value("Could not find filesystem with name {}".format(name))

    def exists(self, name):
        """
        Check if filesystem with name exists
        """
        for subvolume in self.list():
            if subvolume.name == name:
                return True
        return False

    def create(self, name, quota=None):
        """
        Create filesystem
        """
        j.tools.logger._log_debug("Create filesystem %s on %s", name, self)
        mountpoint = self._get_mountpoint()
        fspath = os.path.join(mountpoint, "filesystems")
        self.client.filesystem.mkdir(fspath)
        subvolpath = os.path.join(fspath, name)
        self.client.btrfs.subvol_create(subvolpath)
        if quota:
            self.client.btrfs.subvol_quota(subvolpath, str(quota))
        return FileSystem(name, self)

    @property
    def size(self):
        total = 0
        fs = self.info
        if fs:
            for device in fs["devices"]:
                total += device["size"]
        return total

    @property
    def uuid(self):
        fs = self.info
        if fs:
            return fs["uuid"]
        return None

    @property
    def used(self):
        total = 0
        fs = self.info
        if fs:
            for device in fs["devices"]:
                total += device["used"]
        return total

    def __repr__(self):
        return "StoragePool <{}>".format(self.name)


class FileSystem:
    def __init__(self, name, pool):

        self.name = name
        self.pool = pool
        self.subvolume = "filesystems/{}".format(name)
        self.path = os.path.join(self.pool.mountpoint, self.subvolume)
        self.snapshotspath = os.path.join(self.pool.mountpoint, "snapshots", self.name)

    @property
    def client(self):
        return self.pool.node.client

    def delete(self, includesnapshots=True):
        """
        Delete filesystem
        """
        paths = [fs["Path"] for fs in self.client.btrfs.subvol_list(self.path)]
        paths.sort(reverse=True)
        for path in paths:
            rpath = os.path.join(self.path, os.path.relpath(path, self.subvolume))
            self.client.btrfs.subvol_delete(rpath)
        self.client.btrfs.subvol_delete(self.path)
        if includesnapshots:
            for snapshot in self.list():
                snapshot.delete()
            self.client.filesystem.remove(self.snapshotspath)

    def get(self, name):
        """
        Get snapshot
        """
        for snap in self.list():
            if snap.name == name:
                return snap
        raise j.exceptions.Value("Could not find snapshot {}".format(name))

    def list(self):
        """
        List snapshots
        """
        snapshots = []
        if self.client.filesystem.exists(self.snapshotspath):
            for fileentry in self.client.filesystem.list(self.snapshotspath):
                if fileentry["is_dir"]:
                    snapshots.append(Snapshot(fileentry["name"], self))
        return snapshots

    def exists(self, name):
        """
        Check if a snapshot exists
        """
        return name in self.list()

    def create(self, name):
        """
        Create snapshot
        """
        j.tools.logger._log_debug("create snapshot %s on %s", name, self.pool)
        snapshot = Snapshot(name, self)
        if self.exists(name):
            raise j.exceptions.Base("Snapshot path {} exists.")
        self.client.filesystem.mkdir(self.snapshotspath)
        self.client.btrfs.subvol_snapshot(self.path, snapshot.path)
        return snapshot

    def __repr__(self):
        return "FileSystem <{}: {!r}>".format(self.name, self.pool)


class Snapshot:
    def __init__(self, name, filesystem):

        self.filesystem = filesystem
        self.name = name
        self.path = os.path.join(self.filesystem.snapshotspath, name)
        self.subvolume = "snapshots/{}/{}".format(self.filesystem.name, name)

    @property
    def client(self):
        return self.filesystem.pool.node.client

    def rollback(self):
        self.filesystem.delete(False)
        self.client.btrfs.subvol_snapshot(self.path, self.filesystem.path)

    def delete(self):
        self.client.btrfs.subvol_delete(self.path)

    def __repr__(self):
        return "Snapshot <{}: {!r}>".format(self.name, self.filesystem)
