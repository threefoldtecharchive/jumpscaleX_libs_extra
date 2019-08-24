from Jumpscale import j
from .EtcdClient import EtcdClient


JSConfigs = j.baseclasses.objects_config_bcdb


class EtcdFactory(JSConfigs):

    __jslocation__ = "j.clients.etcd"
    _CHILDCLASS = EtcdClient

    def test(self):

        if j.core.platformtype.myplatform.platform_is_ubuntu:
            j.builders.db.etcd.start()

            cl = j.clients.etcd.test_client
            cl.save()
            cl.put("test_key", "test_value")
            assert cl.get("test_key") == "test_value"
            j.builders.db.etcd.stop()
            print("TEST OK")
