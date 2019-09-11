from Jumpscale import j
from . import TestMacros


class ThreebotDeploy(j.baseclasses.object_config):
    """
    create a threebot deployer instance
    follow readme to know how to deploy
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
        : sets self._machine and self.sshcl
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
        : param size_slug: pass your machine specs check DO availabe slugs
        : return: digital ocean droplet object and sshclient object
        """
        my_droplet, sshcl = self.do_client.droplet_create(
            name=self.do_machine_name, sshkey=self.ssh_key, size_slug=size_slug
        )

        if not my_droplet and not sshcl:
            raise RuntimeError("Failed to create the machine!")

        self._machine = my_droplet
        self._sshcl = sshcl

    def jsx_install(self, branch="development"):
        """
        : install jumpscale non-interactivly on digital ocean machine
        """
        rc, out, err = self.sshcl.execute(
            """
        export DEBIAN_FRONTEND=noninteractive;
        curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/{branch}/install/jsx.py?$RANDOM > /tmp/jsx;
        chmod +x /tmp/jsx; \
        eval `ssh-agent -s`; \
        rm -rf ~/.ssh/id_rsa ~/.ssh/id_rsa.pub ~/.ssh/known_hosts;\
        ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa -q -P "";\
        ssh-add ~/.ssh/id_rsa;\
        /tmp/jsx install -s -b {branch};
        """.format(
                branch=branch
            )
        )
        if rc > 0:
            raise RuntimeError(out, "Error occured at\n", err)

    def install_tcprouter_coredns(self):
        """
        : deploy tcp router and coredns on digital ocean machine
        """
        rc, out, err = self.sshcl.execute(
            """
        kosmos 'j.builders.network.coredns.install()';
        kosmos 'j.builders.network.tcprouter.install()';
        """
        )
        if rc > 0:
            raise RuntimeError(out, "Error occured at\n", err)

    def add_dns_record(self, subdomain="wikis", domain="web.grid.tf", wikis_machine_ip=None, wikis_machine_port="443"):
        """
        add dns record on the dns server this will use coredns and tfgateway
        """
        if not wikis_machine_ip:
            wikis_machine_ip = self.do_machine.ip_address
        rc, out, err = self.sshcl.execute(
            """
        kosmos 'j.builders.network.coredns.stop()';
        kosmos 'j.builders.network.tcprouter.stop()';
        kosmos 'j.tools.tf_gateway.tcpservice_register(f"{subdomain}, f"{subdomain}.{domain}", f"{wikis_machine_ip} + ":" + f"{wikis_machine_port})';
        kosmos 'j.tools.tf_gateway.domain_register_a(f"{subdomain}, f"{domain} , f"{wikis_machine_ip})';
        kosmos 'j.builders.network.coredns.start()';
        kosmos 'j.builders.network.tcprouter.start()';
        """
        )
        if rc > 0:
            raise RuntimeError(out, "Error occured at\n", err)

    def deploy_wikis(self):
        """
        : deploy 3bot and wikis on the wikis machine
        """
        rc, out, err = self.sshcl.execute(
            """
        kosmos -p 'j.threebot.package.wikis.install()';
        kosmos -p 'j.builders.apps.threebot.install()';
        kosmos -p 'wikis = j.servers.threebot.default; wikis.start(ssl=True, web=True)';
        """
        )
        if rc > 0:
            raise RuntimeError(out, "Error occured at\n", err)

    def reset_env(self):
        """
        clears bcdb and sonic
        """
        rc, out, err = self.sshcl.execute(
            """
        kosmos 'j.data.bcdb.destroy_all()';
        pkill redis;
        pkill redis-server;
        kosmos 'j.application.bcdb_system_destroy()';
        kosmos 'j.servers.sonic.default.destroy()';
        """
        )
        if rc > 0:
            raise RuntimeError(out, "Error occured at\n", err)

    def test_macros(self):
        """
        : add some wikis tests to test with some macros
        """
        self.jsx_install()
        self.deploy_wikis()
        # requires import this method from a file
        rc, out, err = self.sshcl.execute(
            """kosmos 'j.servers.myjobs.schedule(TestMacros.load_wiki, "testwikis", "https://github.com/Dinaamagdy/test_custom_md/tree/master/docs")'
        """
        )
        if rc > 0:
            raise RuntimeError(out, "Error occured at\n", err)


class ThreebotDeployFactory(j.baseclasses.object_config_collection):
    """
    Factory for threebot deployment
    to deploy you will need a macine for tcp router and another for the packages you want
    """

    __jslocation__ = "j.tools.threebot_deploy"
    _CHILDCLASS = ThreebotDeploy
