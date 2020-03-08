from .forwarder import MailForwarder

from Jumpscale import j

skip = j.baseclasses.testtools._skip


class JSMailForwarderBase(j.baseclasses.object_config):
    """Base class that holds the forwarder's configurations as 
    A JSX schema
    """

    _SCHEMATEXT = """
        @url = jumpscale.mailforwarder.1
        name** = ""
        listening_host = ""
        listening_port = (I)
        relay_host = ""
        relay_port = (I)
        relay_user = ""
        relay_password = ""
        relay_ssl = (B)
        forward_config = (LO) !jumpscale.mailforwarder.forward_config.1

        @url = jumpscale.mailforwarder.forward_config.1
        destination_domain = ""
        source_domains = (LS)
    """

    def add_forward_config(self, destination_domain, source_domains):
        """Adds a new forward configurations
        """
        model = j.data.schema.get(url="jumpscale.mailforwarder.forward_config.1").new()
        model.destination_domain = destination_domain
        model.source_domains = source_domains
        self.forward_config.append(model)
        self._forwarder.add_forward_config(destination_domain, source_domains)

    def _init(self, **kwargs):
        self._forward_config = {}
        relay_config = {
            "host": self.relay_host,
            "port": self.relay_port,
            "user": self.relay_user,
            "password": self.relay_password,
            "ssl": self.relay_ssl,
        }
        for item in self.forward_config:
            self._forward_config[item.destination_domain] = item.source_domains
        logger = LoggerAdaptor(self)
        self._forwarder = MailForwarder(
            self.listening_host, self.listening_port, self._forward_config, relay_config, logger
        )

    def start(self):
        """Starts a forwarder server
        """
        self._forwarder.run()


class JSMailForwarderFactory(j.baseclasses.object_config_collection_testtools):
    """Factory class
    """

    __jslocation__ = "j.servers.mail_forwarder"
    _CHILDCLASS = JSMailForwarderBase

    @skip("https://github.com/threefoldtech/jumpscaleX_libs_extra/issues/19")
    def test(self, gdomain_user, gdomain_password):
        mf = j.servers.mail_forwarder.get(
            name="test",
            listening_host="localhost",
            listening_port=8823,
            relay_host="smtp.gmail.com",
            relay_port=587,
            relay_user=gdomain_user,
            relay_password=gdomain_password,
            relay_ssl=True,
        )
        mf.add_forward_config("codescalers.com", ["incubaide.com", "threefoldtech.com"])
        mf.start()


class LoggerAdaptor:
    def __init__(self, js_obj):
        self._js_obj = js_obj

    def info(self, msg):
        self._js_obj._log_info(msg)

    def error(self, msg):
        self._js_obj._log_error(msg)

    def warn(self, msg):
        self._js_obj._log_warning(msg)

    def debug(self, msg):
        self._js_obj._log_debug(msg)
