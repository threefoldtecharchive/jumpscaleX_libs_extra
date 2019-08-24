from .Mongodb import Mongodb
from Jumpscale import j

JSBASE = j.baseclasses.object


class MongodbFactory(JSBASE):
    __jslocation__ = "j.sal_zos.mongodb"

    @staticmethod
    def get(
        name,
        node,
        container_name=None,
        config_replica_set=None,
        config_port=None,
        config_mount=None,
        shard_replica_set=None,
        shard_port=None,
        shard_mount=None,
        route_port=None,
    ):
        """
        Get sal for mongodb
        Returns:
            the sal layer 
        """
        return Mongodb(
            name,
            node,
            container_name,
            config_replica_set,
            config_port,
            config_mount,
            shard_replica_set,
            shard_port,
            shard_mount,
            route_port,
        )
