from Jumpscale import j
from .ThreebotDeploy import ThreebotDeploy


class ThreebotDeployFactory(j.baseclasses.object_config_collection):
    """
    Factory for threebot deployment
    to deploy you will need a macine for tcp router and another for the packages you want
    """

    __jslocation__ = "j.me.encryptor.tools_deploy"
    _CHILDCLASS = ThreebotDeploy
