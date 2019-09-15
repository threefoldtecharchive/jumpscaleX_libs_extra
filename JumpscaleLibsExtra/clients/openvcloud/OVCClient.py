import time
import jwt
import jose.jwt
from paramiko.ssh_exception import BadAuthenticationType
from Jumpscale import j

from .Account import Account
from .Machine import Machine
from .Space import Space

# NEED: pip3 install python-jose


TEMPLATE = """
address = ""
port = 443
jwt_ = ""
location = ""
account = ""
space = ""
"""

JSConfigBase = j.baseclasses.object_config


class OVCClient(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.openvcloud.client
    name** = "" (S)
    address = "" (S)
    port = 443 (ipport)
    jwt_ = "" (S)
    location = "" (S)
    account = "" (S)
    space = "" (S)
    """

    def _init(self, **kwargs):
        self._api = None
        self._config_check()

        if not self.location:
            if len(self.locations) == 1:
                self.location = self.locations[0]["locationCode"]
                self.save()

    @property
    def jwt(self):
        if self.jwt_:
            jwt = self.jwt_.strip()
            jwt = j.clients.itsyouonline.refresh_jwt_token(jwt, validity=3600)
            expires = j.clients.itsyouonline.jwt_expire_timestamp(jwt)
            if "refresh_token" not in jose.jwt.get_unverified_claims(jwt) and j.clients.itsyouonline.jwt_is_expired(
                expires
            ):
                raise j.exceptions.Base("JWT expired and can't be refreshed, please choose another token.")
        else:
            if j.tools.configmanager.sandbox_check():
                raise j.exceptions.Base("When in a sandbox, jwt is required")
            jwt = j.clients.itsyouonline.default.jwt_get(refreshable=True, use_cache=True)
        return jwt

    @property
    def api(self):
        if self._api is None:

            self._api = j.clients.portal.get(data={"ip": self.address, "port": self.port})
            # patch handle the case where the connection dies because of inactivity
            self.__patch_portal_client(self._api)
            self.__login()
            self._api.load_swagger(group="cloudapi")
        return self._api

    def _config_check(self):
        """
        check the configuration if not what you want the class will barf & show you where it went wrong
        """

        def urlClean(url):
            url = url.lower()
            url = url.strip()
            if url.startswith("http"):
                url = url.split("//")[1].rstrip("/")
            if "/" in url:
                url = url.split("/")[0]
            self._log_info("Get OpenvCloud client on URL: %s" % url)
            return url

        self.address = urlClean(self.address)

        if self.address.strip() == "":
            raise j.exceptions.Base(
                "please specify address to OpenvCloud server (address) e.g. se-gen-1.demo.greenitglobe.com"
            )

        if not self.jwt_.strip() and j.tools.configmanager.sandbox_check():
            raise j.exceptions.Base("When in a sandbox, jwt is required")

        # if not self.config.data.get("login"):
        #     raise j.exceptions.Base("login cannot be empty")

    def __patch_portal_client(self, api):
        # try to relogin in the case the connection is dead because of
        # inactivity
        origcall = api.__call__

        def patch_call(that, *args, **kwargs):
            from clients.portal.PortalClient import ApiError

            try:
                return origcall(that, *args, **kwargs)
            except ApiError as e:
                if e.response.status_code == 419:
                    self.__login()
                    return origcall(that, *args, **kwargs)
                raise

        api.__call__ = patch_call

    def __login(self):
        payload = jose.jwt.get_unverified_claims(self.jwt)
        # if payload['exp'] < time.time():
        #     j.clients.itsyouonline.reset()
        #     # Regenerate jwt after resetting the expired one
        #     self.config.data = {"jwt_": j.clients.itsyouonline.default.jwt}
        self.api._session.headers["Authorization"] = "bearer {}".format(self.jwt)
        self._login = "{}@{}".format(payload["username"], payload["iss"])

    @property
    def accounts(self):
        """Gets accounts to current user"""
        ovc_accounts = self.api.cloudapi.accounts.list()
        accounts = list()
        for account in ovc_accounts:
            accounts.append(Account(self, account))
        return accounts

    @property
    def locations(self):
        """Gets available locations"""
        return self.api.cloudapi.locations.list()

    def account_get(
        self,
        name="",
        create=True,
        maxMemoryCapacity=-1,
        maxVDiskCapacity=-1,
        maxCPUCapacity=-1,
        maxNASCapacity=-1,
        maxNetworkOptTransfer=-1,
        maxNetworkPeerTransfer=-1,
        maxNumPublicIP=-1,
    ):
        """Returns the OpenvCloud account with the given name, and in case it doesn't exist yet the account will be created.

        :param name: name of the account to lookup or create if it doesn't exist yet, e.g. "myaccount" if not set will get it from config manager data, defaults to ""
        :param name: str, optional
        :param create: if set to True the account is created in case it doesn't exist yet, defaults to True
        :param create: bool, optional
        :param maxMemoryCapacity: available memory in GB for all virtual machines in the account, defaults to -1(unlimited)
        :param maxMemoryCapacity: int, optional
        :param maxVDiskCapacity: available disk capacity in GiB for all virtual disks in the account, defaults to -1(unlimited)
        :param maxVDiskCapacity: int, optional
        :param maxCPUCapacity: total number of available virtual CPU core that can be used by the virtual machines in the account, defaults to -1(unlimited)
        :param maxCPUCapacity: int, optional
        :param maxNASCapacity: not implemented, defaults to -1(unlimited)
        :param maxNASCapacity: int, optional
        :param maxNetworkOptTransfer: not implemented, defaults to -1(unlimited)
        :param maxNetworkOptTransfer: int, optional
        :param maxNetworkPeerTransfer: not implemented, defaults to -1(unlimited)
        :param maxNetworkPeerTransfer: int, optional
        :param maxNumPublicIP: number of external IP addresses that can be used in the account, defaults to -1(unlimited)
        :param maxNumPublicIP: int, optional
        :raises RuntimeError: if name not specified and no acount name in config manager instance
        :raises KeyError: if account doesn't exist, and create argument was set to False
        :return: account data
        :rtype: object
        """

        if name == "":
            name = self.account
        if not name:
            raise j.exceptions.Base("name needs to be specified in account in config or on method.")
        for account in self.accounts:
            if account.model["name"] == name:
                return account
        else:
            if create is False:
                raise j.exceptions.NotFound('No account with name "%s" found' % name)
            self.api.cloudbroker.account.create(
                username=self.login,
                name=name,
                maxMemoryCapacity=maxMemoryCapacity,
                maxVDiskCapacity=maxVDiskCapacity,
                maxCPUCapacity=maxCPUCapacity,
                maxNASCapacity=maxNASCapacity,
                maxNetworkOptTransfer=maxNetworkOptTransfer,
                maxNetworkPeerTransfer=maxNetworkPeerTransfer,
                maxNumPublicIP=maxNumPublicIP,
            )
            return self.account_get(name, False)

    def space_get(
        self,
        accountName="",
        spaceName="",
        location="",
        createSpace=True,
        maxMemoryCapacity=-1,
        maxVDiskCapacity=-1,
        maxCPUCapacity=-1,
        maxNASCapacity=-1,
        maxNetworkOptTransfer=-1,
        maxNetworkPeerTransfer=-1,
        maxNumPublicIP=-1,
        externalnetworkId=None,
    ):
        """ Returns the OpenvCloud space with the given account_name, space_name, space_location and in case the account doesn't exist yet it will be created.

        :param accountName: name of the account to lookup, e.g. "myaccount", defaults to ""
        :param accountName: str, optional
        :param spaceName: name of the cloud space to lookup or create if it doesn't exist yet, e.g. "myvdc", defaults to ""
        :param spaceName: str, optional
        :param location: location when the cloud space needs to be created(only required when cloud space needs to be created), defaults to ""
        :param location: str, optional
        :param createSpace: if set to True the account is created in case it doesn't exist yet, defaults to True
        :param createSpace: bool, optional
        :param maxMemoryCapacity: available memory in GB for all virtual machines in the cloud space, defaults to -1(unlimited)
        :param maxMemoryCapacity: int, optional
        :param maxVDiskCapacity: available disk capacity in GiB for all virtual disks in the cloud space, defaults to -1(unlimited)
        :param maxVDiskCapacity: int, optional
        :param maxCPUCapacity: total number of available virtual CPU core that can be used by the virtual machines in the cloud space, defaults to -1(unlimited)
        :param maxCPUCapacity: int, optional
        :param maxNASCapacity: not implemented, defaults to -1(unlimited)
        :param maxNASCapacity: int, optional
        :param maxNetworkOptTransfer: not implemented, defaults to -1(unlimited)
        :param maxNetworkOptTransfer: int, optional
        :param maxNetworkPeerTransfer: not implemented, defaults to -1(unlimited)
        :param maxNetworkPeerTransfer: int, optional
        :param maxNumPublicIP: number of external IP addresses that can be used in the cloud space, defaults to -1(unlimited)
        :param maxNumPublicIP: int, optional
        :param externalnetworkId: id of the external network to attach to, defaults to None
        :param externalnetworkId: int, optional
        :raises RuntimeError: if name not specified and no acount name in config manager instance
        :raises j.exceptions.RuntimeError: if specified account can't be found
        :return: cloudspace data
        :rtype: object
        """

        if location == "":
            location = self.location

        if spaceName == "":
            spaceName = self.space

        if not spaceName:
            raise j.exceptions.Base("name needs to be specified in account in config or on method.")

        account = self.account_get(name=accountName, create=False)
        if account:
            return account.space_get(
                name=spaceName,
                create=createSpace,
                location=location,
                maxMemoryCapacity=maxMemoryCapacity,
                maxVDiskCapacity=maxVDiskCapacity,
                maxCPUCapacity=maxCPUCapacity,
                maxNASCapacity=maxNASCapacity,
                maxNetworkOptTransfer=maxNetworkOptTransfer,
                maxNetworkPeerTransfer=maxNetworkPeerTransfer,
                maxNumPublicIP=maxNumPublicIP,
                externalnetworkId=externalnetworkId,
            )
        else:
            raise j.exceptions.RuntimeError("Could not find account with name %s" % accountName)

    def get_available_images(self, cloudspaceId=None, accountId=None):
        """[summary]

        :param cloudspaceId: cloudspace Id, defaults to None
        :param cloudspaceId: int, optional
        :param accountId: account Id, defaults to None
        :param accountId: int, optional
        :return: list of dict representing image info
        :rtype: list
        """

        return self.api.cloudapi.images.list(cloudspaceId=cloudspaceId, accountId=accountId)

    @property
    def login(self):
        return self._login

    def __repr__(self):
        return "OpenvCloud client:\n%s" % self.config

    __str__ = __repr__
