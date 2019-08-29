from ..abstracts import Mountable


class Partition(Mountable):
    """Partition of a disk in a Zero-OS"""

    def __init__(self, disk, part_info):
        """
        part_info: dict returned by client.disk.list()
        """
        # g8os client to talk to the node
        self.disk = disk
        self.name = None
        self.size = None
        self.blocksize = None
        self.mountpoint = None
        self.uuid = None
        self.fs_uuid = None

        self._load(part_info)
        Mountable.__init__(self)

    @property
    def client(self):
        return self.disk.node.client

    @property
    def filesystem(self):
        for fs in self.client.btrfs.list() or []:
            if fs["uuid"] == self.fs_uuid:
                return fs

    @property
    def devicename(self):
        return "/dev/{}".format(self.name)

    def _load(self, part_info):
        self.name = part_info["name"]
        self.size = int(part_info["size"])
        self.blocksize = self.disk.blocksize
        self.mountpoint = part_info["mountpoint"]
        self.uuid = part_info["partuuid"]
        self.fs_uuid = part_info["uuid"]

    def __str__(self):
        return "Partition <{}>".format(self.name)

    def __repr__(self):
        return str(self)
