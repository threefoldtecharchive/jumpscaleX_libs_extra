from Jumpscale import j

from .ZOS import ZOS


class ZOSVB(ZOS):
    def __init__(self, zosclient, name):
        ZOS.__init__(self, zosclient=zosclient, name=name)
        self._zos_private_address = None
        self.zos_private_address  # make sure we know the private addr
        self._type = "vbox"

    @property
    def zos_private_address(self):
        """
        private addr of the virtualbox, if not virtualbox will return False
        will also do a ping test
        :return: False if no virtualbox
        """
        if self._zos_private_address == None:

            if self.address_private != "":
                self._zos_private_address = self.address_private
            else:
                # assume vboxnet0 use an 192.168.0.0/16 address
                for nic in self.zosclient.client.info.nic():
                    if len(nic["addrs"]) == 0:
                        continue
                    if nic["addrs"][0]["addr"].startswith("127.0.0.1"):
                        self._zos_private_address = nic["addrs"][0]["addr"].split("/")[0]
                        if not j.sal.nettools.pingMachine(self._zos_private_address):
                            raise j.exceptions.Base(
                                "could not reach private addr:%s of VB ZOS" % self._zos_private_address
                            )
                        self.address_private = self._zos_private_address
                        self.save()
                        return self._zos_private_address
                raise j.exceptions.Base("could not find private addr of virtualbox for zos")
        return self._zos_private_address

    def _get_free_port(self):
        port = 4001
        while j.sal.nettools.checkListenPort(port) == True:
            self._log_debug("check for free tcp port:%s" % port)
            port += 1
        return port

    @property
    def vb_client(self):
        """
        virtualbox client
        """
        return j.clients.virtualbox.client

    def __repr__(self):
        return "zosvb:%s" % self.name

    __str__ = __repr__
