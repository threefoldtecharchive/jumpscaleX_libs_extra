from .Minio import Minio, DEFAULT_PORT
from Jumpscale import j

JSBASE = j.baseclasses.object


class MinioFactory(JSBASE):
    __jslocation__ = "j.sal_zos.minio"

    @staticmethod
    def get(
        name,
        node,
        login,
        password,
        zdbs,
        namespace,
        private_key,
        node_port,
        namespace_secret="",
        block_size=1048576,
        meta_private_key="",
        nr_datashards=1,
        nr_parityshards=0,
        tlog_namespace=None,
        tlog_address=None,
        master_namespace=None,
        master_address=None,
        logo_url=None,
    ):
        """
        Get sal for minio
        Returns:
            the sal layer
        """
        return Minio(
            name=name,
            node=node,
            login=login,
            password=password,
            zdbs=zdbs,
            namespace=namespace,
            private_key=private_key,
            node_port=node_port,
            namespace_secret=namespace_secret,
            block_size=block_size,
            meta_private_key=meta_private_key,
            nr_datashards=nr_datashards,
            nr_parityshards=nr_parityshards,
            tlog_namespace=tlog_namespace,
            tlog_address=tlog_address,
            master_namespace=master_namespace,
            master_address=master_address,
            logo_url=logo_url,
        )
