from Jumpscale import j

JSBASE = j.baseclasses.object

from .ETCD import ETCD


class ETCDFactory(JSBASE):
    __jslocation__ = "j.sal_zos.etcd"

    def get(
        self,
        node,
        name,
        password,
        data_dir="/mnt/data",
        zt_identity=None,
        nics=None,
        token=None,
        cluster=None,
        host_network=False,
    ):
        """
        Get sal for etcd management in ZOS

        Arguments:
            node: the node sal instance the etcd will be created on
            name: the name of the etcd instance
            password: password of the root user
            data_dir: etcd data directory
            zt_identity: zt identity of the etcd container
            nics: nics to be attached to the etcd container
            token: etcd cluster token
            cluster: all the cluster members. ex: [{'name': 'etcd_one', 'address': 'http://172.22.14.232:2380'}]

        Returns:
            the sal layer
        """
        return ETCD(node, name, password, data_dir, zt_identity, nics, token, cluster, host_network)
