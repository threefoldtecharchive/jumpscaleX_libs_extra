from Jumpscale import j
from . import TestMacros


class ThreebotDeploy(j.baseclasses.object_config):
    """
    create a threebot deployer instance
    """

    _SCHEMATEXT = """
    @url = jumpscale.threebot.deploy
    name* = "" (S)
    do_machine_name = "" (S)
    do_token = "" (S)
    do_project_name = "" (S)
    ssh_key = "" (S)
    """

    def _init(self, **kwargs):
        self._do_client = None
        self._machine = None
        self._sshcl = None

    @property
    def do_client(self):
        """
        : creats jumpscale digitalocean client using the provided data in init
        : return: jsx client object
        """
        if not self._do_client:
            client = j.clients.digitalocean.get(
                name=self.do_machine_name, token_=self.do_token, project_name=self.do_project_name
            )
            self._do_client = client
        return self._do_client

    @property
    def do_machine(self):
        """
        : get digital ocean up machine
        : return: digital ocean droplet object and sshclient object
        """
        if not self._machine:
            my_droplet = self.do_client._droplet_get(name=self.do_machine_name)
            sshcl = j.clients.ssh.get(
                name=self.do_machine_name, addr=my_droplet.ip_address, client_type="paramiko", sshkey_name=self.ssh_key
            )
            self._machine = my_droplet
            self._sshcl = sshcl
        return self._machine

    @property
    def sshcl(self):
        if not self._sshcl:
            self.do_machine
        return self._sshcl

    def create_new_do_machine(self, size_slug="s-1vcpu-1gb"):
        """
        : get digital ocean up machine
        : return: digital ocean droplet object and sshclient object
        """
        my_droplet, sshcl = self.do_client.droplet_create(
            name=self.do_machine_name, sshkey=self.ssh_key, size_slug=size_slug
        )

        if not my_droplet and not sshcl:
            raise RuntimeError("Failed to create the machine!")

        self._machine = my_droplet
        self._sshcl = sshcl

    def jsx_install(self):
        """
        : install jumpscale non-interactivly on digital ocean machine
        """
        rc, out, err = self.sshcl.execute(
            """
        export DEBIAN_FRONTEND=noninteractive;
        curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/development/install/jsx.py?$RANDOM > /tmp/jsx;
        chmod +x /tmp/jsx; \
        eval `ssh-agent -s`; \
        rm -rf ~/.ssh/id_rsa ~/.ssh/id_rsa.pub ~/.ssh/known_hosts;\
        ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa -q -P "";\
        ssh-add ~/.ssh/id_rsa;\
        /tmp/jsx install -s -b development;
        """
        )
        if rc == 0:
            print("TEST OK")
        else:
            raise RuntimeError("Error occured at\n", err)

    def install_tcprouter_coredns(
        self, subdomain="wikis", domain="web.grid.tf", wikis_machine_ip=None, wikis_machine_port="443"
    ):
        """
        : deploy tcp router and coredns on digital ocean machine
        """
        if not wikis_machine_ip:
            wikis_machine_ip = self.do_machine.ip_address
        rc, _, err = self.sshcl.execute(
            """
        kosmos 'j.builders.network.coredns.install()';
        kosmos 'j.builders.network.tcprouter.install()';
        kosmos 'j.tools.tf_gateway.tcpservice_register(f"{subdomain}, f"{subdomain}.{domain}", f"{wikis_machine_ip} + ":" + f"{wikis_machine_port})';
        kosmos 'j.tools.tf_gateway.domain_register_a(f"{subdomain}, f"{domain} , f"{wikis_machine_ip})';
        kosmos 'j.builders.network.coredns.start()';
        kosmos 'j.builders.network.tcprouter.start()';
        """
        )
        if rc == 0:
            print("TEST OK")
        else:
            raise RuntimeError("Error occured at\n", err)

    def deploy_wikis(self):
        """
        : deploy 3bot and wikis
        """
        rc, out, err = self.sshcl.execute(
            """
        . /sandbox/env.sh;
        js_init generate;
        cd /sandbox/code/github/threefoldtech/jumpscaleX_core;
        git checkout 79a930098d114fbf43c98c5d5525d0ed7b599f98;
        git cherry-pick c2a6a4248dd6a8f3808d633665e18ecf0bb0ed87;
        git cherry-pick 5015c89be28c8dd9e9d74477fd672a03716c3bbb;
        git cherry-pick b01bef6a4d09e8a50a49d8f6e24c7f1744d46bb7;
        git cherry-pick e57cd41b93a5ea7b8eff9712875dc6917b97d659;
        kosmos 'j.data.bcdb.destroy_all()';
        pkill redis;
        pkill redis-server;
        kosmos 'j.application.bcdb_system_destroy()';
        kosmos 'j.servers.sonic.default.destroy()';
        kosmos -p 'j.threebot.package.wikis.install()';
        kosmos -p 'j.builders.apps.threebot.install()';
        kosmos -p 'wikis = j.servers.threebot.default; wikis.start(ssl=True, web=True)';
        """
        )
        if rc == 0:
            print("TEST OK")
        else:
            raise RuntimeError("Error occured at\n", err)

    def test_macros(self):
        """
        : add some wikis tests to test with some macros
        """
        self.deploy_wikis()
        # requires import this method from a file
        rc, out, err = self.sshcl.execute(
            """kosmos 'j.servers.myjobs.schedule(TestMacros.load_wiki, "testwikis", "https://github.com/Dinaamagdy/test_custom_md/tree/master/docs")'
        """
        )
        if rc > 0:
            raise RuntimeError("Error occured at\n", err)


class ThreebotDeployFactory(j.baseclasses.object_config_collection):
    """
    Factory for threebot deployment
    to deploy you will need a macine for tcp router and another for the packages you want
    """

    __jslocation__ = "j.tools.threebot_deploy"
    _CHILDCLASS = ThreebotDeploy
