from .zerodb import Zerodb
from ..abstracts import DynamicCollection
from ..disks.Disks import StorageType

from Jumpscale import j


class Zerodbs(DynamicCollection):
    def __init__(self, node):
        self.node = node

    def get(self, name):
        """
        Get zerodb object and load data from reality

        :param name: Name of the zerodb
        :type name: str

        :return: Zerodb object
        :rtype: Zerodb object
        """
        zdb = Zerodb(self.node, name, node_port=None)
        zdb.load_from_reality()
        return zdb

    def list(self):
        """
        list zerodb objects

        :return: list of Zerodb object
        :rtype: list
        """
        zdbs = []
        for container in self.node.containers.list():
            if container.name.startswith("zerodb_"):
                zdb = Zerodb(node=self.node, name=container.name.lstrip("zerodb_"), node_port=None)
                zdb.load_from_reality(container)
                zdbs.append(zdb)
        return zdbs

    def create(self, name, node_port, path=None, mode="user", sync=False, admin=""):
        """
        Create zerodb object

        To deploy zerodb invoke .deploy method

        :param name: Name of the zerodb
        :type name: str
        :param node_port: public port on the node that is forwarded to the zerodb listening port in the container
        :type node_port: int
        :param path: path zerodb stores data on
        :type path: str
        :param mode: zerodb running mode
        :type mode: str
        :param sync: zerodb sync
        :type sync: bool
        :param admin: zerodb admin password
        :type admin: str

        :return: Zerodb object
        :rtype: Zerodb object
        """
        return Zerodb(node=self.node, name=name, node_port=node_port, path=path, mode=mode, sync=sync, admin=admin)

    def prepare(self):
        """
        prepare all the disk of the node to be usable by 0-db

        creates a storage pool on each disk, then a filesystem on each storage pool

        :return: list of filesystem path created
        :rtype: [str]
        """

        mounts = []

        # list of all disk devices name used by the storage pool existing on the nodes
        storagepools = self.node.storagepools.list()
        devices_used = [sp.device for sp in storagepools]
        # list of all disk device name on the nodes
        disks = self.node.disks.list()
        all_disks = [d.devicename for d in filter(_zdb_friendly, disks)]

        # search for disk with no storage pool on it yet
        for sp_device in devices_used:
            for disk_device in all_disks:
                if sp_device.find(disk_device) != -1:
                    all_disks.remove(disk_device)
                    break

        # create a storage pool on all the disk which doesn't any storage pool yet
        for device in all_disks:
            name = j.data.idgenerator.generateGUID()
            j.tools.logger._log_info("create storage pool %s on %s", name, device)
            sp = self.node.storagepools.create(
                name, device=device, metadata_profile="single", data_profile="single", overwrite=True
            )
            storagepools.append(sp)

        # make sure we don't use storage pool reserved for something else
        storagepools = filter(reserved_storagepool, storagepools)

        # at this point we have a storage pool on each eligible disk
        for sp in storagepools:
            if not sp.mountpoint:
                logger.info("mount storagepool %s", sp.name)
                sp.mount()
            if not sp.exists("zdb"):
                logger.info("create filesystem on storage pool %s", sp.name)
                fs = sp.create("zdb")
            else:
                fs = sp.get("zdb")
            mounts.append(fs.path)

        return mounts

    def create_and_mount_subvolume(self, zdb_name, size, disktypes):
        GiB = 1024 ** 3
        # filter storagepools that have the correct disk type and whose (total size - reserved subvolume quota) >= size

        def usable_storagepool(sp):
            if sp.type.value not in disktypes:
                return False
            if (sp.size - sp.total_quota() / GiB) <= size:
                return False
            return True

        storagepools = list(filter(usable_storagepool, self.node.storagepools.list()))
        # sort less used pool firt
        storagepools.sort(key=lambda sp: sp.size - sp.total_quota(), reverse=True)
        if not storagepools:
            return ""

        storagepool = storagepools[0]
        fs = storagepool.create("zdb_{}".format(zdb_name), size * GiB)
        return fs.path


def reserved_storagepool(storagepool):
    """
    function used to filter out storage pool that should not be used for zdb installation
    """
    from ..node.Node import ZOS_CACHE

    if storagepool.name == ZOS_CACHE:
        return False
    return True


def _zdb_friendly(disk):
    """
    filter function to remove disk not suitable for zerodb usage
    """
    if disk.type not in [StorageType.HDD, StorageType.SSD, StorageType.NVME, StorageType.ARCHIVE]:
        j.tools.logger._log_info("skipping unsupported disk type %s" % disk.type)
        return False
    # this check is there to be able to test with a qemu setup. Not needed if you start qemu with --nodefaults
    if disk.model in ["QEMU HARDDISK   ", "QEMU DVD-ROM    "] or disk.transport == "usb":
        return False
    return True
