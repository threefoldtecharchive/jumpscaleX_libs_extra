from Jumpscale import j

# import Jumpscale.baselib.remote

JSBASE = j.baseclasses.object

from ..zerodb.zerodb import Zerodb


class ZerodbFactory(JSBASE):
    __jslocation__ = "j.sal_zos.zerodb"

    def get(self, node, name, node_port, path=None, mode="user", sync=False, admin=""):
        """
        Get sal for Zerobd

        Arguments:
            node, name, path=None, mode='user', sync=False, admin=''

        Returns:
            the sal layer
        """
        return Zerodb(node=node, name=name, node_port=node_port, path=path, mode=mode, sync=sync, admin=admin)
