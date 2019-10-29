from Jumpscale import j
import os
from .Machine import Machines

class ThreebotDeploy(j.baseclasses.factory_data):
    """
    create a threebot deployer instance
    follow readme to know how to deploy
    """
    _CHILDCLASSES = [Machines]
    _SCHEMATEXT = """
    @url = jumpscale.threebot.deploy
    name** = "" (S)
    do_token = "" (S)
    do_project_name = "" (S)
    ssh_key = "" (S)
    """

    def _init(self, **kwargs):
        self._do_client = None
        self._sshcl = None
        self._container_ssh = None

    def get_by_double_name(self, name):
        """
        searches for the threebot in all machines
        :param name: double name to look for
        :return:
        """
        for machine in self.machines.find():
            for container in machine.containers.find():
                if container.name == name:
                    return container
        raise RuntimeError(f"3bot with name {name} isn't found")