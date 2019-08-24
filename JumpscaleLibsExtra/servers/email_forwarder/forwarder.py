"""
Mail forwarder is Email server which accepts all our configured domains (wildcard) and forwards to other domain e.g. incubaid.com.
"""
from .gsmtpd.server import SMTPServer
import smtplib


class MailForwarder(SMTPServer):
    """The class accepts a configuration in the form
    {
        "domain" : {
            "sources": ["domain1", "domain2"],
            "port": <>,
            "user": <>,
            "password": <>,
            "ssl": True/False
        }
    }

    A server will be started to listen to incoming emails, once an incoming
    email is recieved and it matches one of the configured domains,
    then the email will be forwarded to the corosponding target domain.
    A client will be created for the target domain and the provided
    authentication parameters.
    """

    def __init__(self, addr_host, addr_port, forwarding_config, relay_config, logger):
        """Initializes a new mail forwarder
        :param addr_host: The host address for running an SMTP server
        :type addr_host: str
        :param addr_port: The port for running an SMTP server
        :type addr_port: int
        :param forwarding_config: Forwarder configurations
        :type forwarding_config: dictionary in the form
        {
            "domain" : ["domain1", "domain2"]
        }
        :param relay_config: Relay server configurations
        :type relay_config: dictionary in the form
        {
            "host": <smtpd host>,
            "port": <>,
            "user": <>,
            "password": <>,
            "ssl": True/False
        }
        :param logger: Logger object
        :type logger: object
        """
        self._addr_host = addr_host
        self._addr_port = addr_port
        self._forwarding_config = forwarding_config
        self._inverted_config = self._invert_config()
        self._relay_config = relay_config
        self._clients = {}
        self._logger = logger
        super(MailForwarder, self).__init__((self._addr_host, self._addr_port))

    def add_forward_config(self, destination_domain, source_domains):
        """Adds a new forward configuration
        """
        self._forwarding_config.update({destination_domain: source_domains})
        self._inverted_config = self._invert_config()

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        """Called by smtpd.SMTPServer when there's a message received.
        
        :param Peer: is a tuple containing (ipaddr, port) of the client that made the
        socket connection to our smtp port.
        :type Peer: tuple
        :param mailfrom: is the raw address the client claims the message is coming
        from.
        :type mailfrom: string
        :param rcpttos: is a list of raw addresses the client wishes to deliver the
        message to.
        :type rcpttos: list
        :param data: is a string containing the entire full text of the message,
        headers (if supplied) and all.  It has been `de-transparencied'
        according to RFC 821, Section 4.5.2.  In other words, a line
        containing a `.' followed by other text has had the leading dot
        removed.
        :type data: str
        """
        rcpttos = self._process_addresses(rcpttos)
        self._logger.debug("MSG received! and will be send to {}".format(rcpttos))
        if rcpttos:
            try:
                self._deliver(mailfrom, rcpttos, data)
            except Exception as e:
                self._logger.error("Failed to forward email. Error: {}".format(str(e)))
                raise

    def _deliver(self, mailfrom, rcpttos, data):
        try:
            cl = smtplib.SMTP(self._relay_config["host"], self._relay_config["port"])
            cl.ehlo()
            if self._relay_config["ssl"]:
                cl.starttls()
            cl.login(self._relay_config["user"], self._relay_config["password"])
            cl.sendemail(mailfrom, rcpttos, data)
            cl.close()
        except Exception as e:
            self._logger.error(
                "Errors while sending email to via {}. Error: {}".format(self._relay_config["host"], str(e))
            )
            raise

    def _process_addresses(self, rcpttos):
        result = []
        for address in rcpttos:
            name, domain = address.split("@")
            if domain in self._inverted_config:
                # TODO: check for forwarding cycles
                result.append("{}@{}".format(name, self._inverted_config[domain]))
            else:
                self._logger.warn("Address {} does not match any of the configured doamins".format(address))
        return result

    def _invert_config(self):
        result = {}
        for k, v in self._forwarding_config.items():
            for domain in v:
                if domain in result:
                    self._logger.warn("Domain {} already configured".format(domain))
                    continue
                result[domain] = k
        return result

    def run(self):
        """starts a forwarder server
        """
        print("Starting forwarder on port: {}".format(self._addr_port))
        self.serve_forever()
