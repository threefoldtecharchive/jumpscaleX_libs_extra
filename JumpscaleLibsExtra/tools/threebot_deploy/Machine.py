from Jumpscale import j
from .Container import Containers
import os


class Machine(j.baseclasses.factory_data):
    _CHILDCLASSES = [Containers]
    _SCHEMATEXT = """
    @url = jumpscale.deployer.machine
    name** = (S)
    installed = False (B)
    capacity = 5 (I)
    size_slug = "s-1vcpu-1gb"
    branch = "development"
    """

    def _init(self, **kwargs):
        self._deployer = self._parent._parent
        self.do_machine_name = self.name.replace("_", "-")
        self.ssh_client = None
        self.ip_address = None
        self._machine = None
        self._do_client = None
        self._machine_init()

    def _machine_init(self):
        """
        : get digital ocean up machine
        : sets self._machine and self.sshcl
        """
        if not self._exists():
            my_droplet, sshcl = self.do_client.droplet_create(
                name=self.do_machine_name,
                sshkey=self._deployer.ssh_key,
                size_slug=self.size_slug,
                project_name=self._deployer.do_project_name,
            )
            j.sal.nettools.waitConnectionTest(my_droplet.ip_address, 22, 180)
        else:
            my_droplet = self.do_client.droplet_get(name=self.do_machine_name)
            j.sal.nettools.waitConnectionTest(my_droplet.ip_address, 22, 180)
            sshcl = j.clients.ssh.get(
                name=self.do_machine_name,
                addr=my_droplet.ip_address,
                client_type="paramiko",
                sshkey_name=self._deployer.ssh_key,
            )

        self._machine = my_droplet
        self.sshcl = sshcl
        self.ip_address = my_droplet.ip_address
        if not self.installed:
            self.install()

    def install(self):
        """
        install jumpscale non-interactivly on digital ocean machine
        """
        install_cmd = "export DEBIAN_FRONTEND=noninteractive;"
        install_cmd += f"curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/{self.branch}/install/jsx.py?$RANDOM > /tmp/jsx;"
        install_cmd += "chmod +x /tmp/jsx;"
        if not os.environ.get("SSH_AUTH_SOCK"):
            install_cmd += "eval `ssh-agent -s`;"
        install_cmd += "rm -rf ~/.ssh/id_rsa ~/.ssh/id_rsa.pub;"
        install_cmd += 'ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa -q -P "";'
        rc, out, err = self.sshcl.execute(install_cmd)
        if rc > 0:
            raise RuntimeError(out, "Error occured while creating installing machine at\n", err)

        self.wireguard_install()

        self.installed = True

    def wireguard_install(self):
        j.sal.nettools.waitConnectionTest(self.ip_address, 22, 180)
        j.tools.wireguard.get(name=self.do_machine_name, sshclient_name=f"do_{self.do_machine_name}", autosave=False).install()

    def threebot_deploy(self, name, start=True):
        if self.containers.exists(name):
            return self.containers.get(name)

        if self.containers.count() >= self.capacity:
            raise RuntimeError(
                "Can't deploy more containers on this machine, it's full already,"
                " use machines.get_available() to get an available machine"
            )
        order = self.containers.count()
        container = self.containers.get(name, branch=self.branch, gedis_port=8900 + order, ssh_port=9200 + order)
        container.deploy(start=start)
        return container

    @property
    def do_client(self):
        """
        : creats jumpscale digitalocean client using the provided data in init
        : return: jsx client object
        """
        if not self._do_client:
            client = j.clients.digitalocean.get(
                name=self.do_machine_name, token_=self._deployer.do_token, project_name=self._deployer.do_project_name
            )
            self._do_client = client
        return self._do_client

    def _exists(self):
        return self.do_client.droplet_exists(self.do_machine_name)


class Machines(j.baseclasses.object_config_collection):
    _CHILDCLASS = Machine

    def machine_create(self, name, capacity, install=True):
        machine = self.get(name, capacity=capacity)
        if install:
            machine.install()
        return machine

    def get_available(self, capacity=5):
        """
        gets an available machine
        A machine is available if the number of deployed containers is less than the max capacity of this machine
        :return: Machine
        """
        for machine in self.find():
            if machine.containers.count() < machine.capacity and machine.installed:
                return machine
        else:
            name = f"{j.data.randomnames.hostname()}_{j.data.time.epoch}"
            return self.machine_create(name, capacity)
