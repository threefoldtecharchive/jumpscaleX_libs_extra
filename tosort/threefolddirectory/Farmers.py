from Jumpscale import j


class Farmer(j.baseclasses.object_config):
    """
    one farmer instance
    """

    _SCHEMATEXT = """
        @url = threefold.grid.farmer
        name* = ""
        description = ""
        error = ""
        iyo_org* = ""
        wallets = (LS)
        emailaddr = (LS)
        mobile = (LS)
        """

    def _init(self, **kwargs):
        pass


class Farmers(j.baseclasses.objects_config_bcdb):
    """
    ...
    """

    _CHILDCLASS = Farmer
