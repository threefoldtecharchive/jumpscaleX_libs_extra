from Jumpscale import j
from .OdooServer import OdooServer

JSConfigs = j.baseclasses.object_config_collection
TESTTOOLS = j.baseclasses.testtools


skip = j.baseclasses.testtools._skip


class OdooFactory(JSConfigs, TESTTOOLS):
    """
    """

    __jslocation__ = "j.servers.odoo"
    _CHILDCLASS = OdooServer

    def _init(self, **kwargs):
        self._default = None

    @property
    def default(self):
        if not self._default:
            self._default = self.get(name="default")
        return self._default

    def install(self, reset=False):
        """
        kosmos 'j.servers.odoo.build()'
        """
        j.builders.apps.odoo.install(reset=reset)

    @skip("https://github.com/threefoldtech/jumpscaleX_builders/issues/50")
    def test(self, start=True):
        """
        kosmos 'j.servers.odoo.test()'
        :return:
        """
        self.install()
        s = self.get(name="test")
        if start:
            s.start()
        dbobj = s.databases.new()
        dbobj.name = "test1"
        dbobj.admin_email = "info1@example.com"
        dbobj.admin_passwd_ = "123456"
        dbobj.country_code = "be"
        dbobj.lang = "en_US"
        dbobj.phone = ""

        s.databases_create()

        s.save()

        cl1 = s.client_get("test1")

        cl1.modules_default_install()
        cl1.user_add("odoo_test", "test1234")
        cl1.login("odoo_test", "test1234")
        cl1.user_delete("odoo_test", "test1234")
        try:
            cl1.login("odoo_test", "test1234")
        except:
            pass

        databases = cl1.databases_list()
        dbexists = False
        for i in databases:
            if dbexists:
                break
            if i == "test1":
                dbexists = True

        if not dbexists:
            raise j.exceptions.Value("db doesn't exist")

        cl1.module_install("note")

        cl1.module_remove("note")

        return "TESTS OK"

    @skip("https://github.com/threefoldtech/jumpscaleX_builders/issues/50")
    def test_tmux(self, name=""):
        self._tests_run(name=name, die=True)
