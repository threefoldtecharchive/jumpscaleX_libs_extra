class ZOS(j.baseclasses.object_config):

    _SCHEMATEXT = """
    @url = zos.config
    date_start = 0 (D)
    description = ""
    progress = (LS)
    address_private = ""
    sshport_last = 4010    
    """

    def __init__(self, zosclient):
        j.baseclasses.object_config.__init__(self)
        self.zosclient = zosclient
        if zosclient.client._Client__redis is None:
            zosclient.ping()  # otherwise the redis client does not work
        self._zostype = "zerotier"

    def container_get(self, name="builder", flist=""):
        from .ZOSContainer import ZOSContainer

        zc = ZOSContainer(zos=self, name=name)
        if flist is not "":
            zc.flist = flist
        zc.start()
        return zc

    def __repr__(self):
        return "zos:%s" % self.name

    __str__ = __repr__


# rsync -e "ssh -p1027"  -rav --delete ~/code/github/threefoldtech/ root@192.168.56.101:/root/code/github/threefoldtech/
# rsync -e "ssh"  -rav --delete ~/code/github/threefoldtech/ root@10.244.172.242:/root/code/github/threefoldtech/
