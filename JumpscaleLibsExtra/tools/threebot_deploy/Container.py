from Jumpscale import j


class Container(j.baseclasses.object_config):
    _SCHEMATEXT = """
        @url = jumpscale.deployer.container
        name** = (S)
        gedis_port = (I)
        ssh_port = (I)
        branch = "development"
        deployed = False
        """

    def _init(self, **kwargs):
        self._machine = self._parent._parent
        self.ip_address = self._machine.ip_address

    def deploy(self, start=True, web=True, ssl=True):
        install_cmd = (
            f"/tmp/jsx container-install -n {self.name} -s -b {self.branch}"
            f" --ports {self.ssh_port}:22 --ports {self.gedis_port}:8901"
        )

        rc, out, err = self._machine.sshcl.execute(install_cmd)

        if rc > 0:
            raise RuntimeError(out, "Error occured while installing on container at\n", err)

        if start:
            self.threebot_start(web=web, ssl=ssl)

        self.deployed = True

    def threebot_start(self, web=True, ssl=True):
        cmd = (
            f". /sandbox/env.sh; kosmos -p 'j.servers.threebot.install(); threefold = j.servers.threebot.default;"
            f"threefold.web={web};threefold.ssl={ssl};threefold.start(background=True)'"
        )
        self.ssh_client.execute(cmd)
        client = self.threebot_client
        client.actors.package_manager.package_add(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/registration"
        )
        client.actors.package_manager.package_add(
            "/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/tfgrid/tfgrid_network"
        )
        client.reload()
        return client

    @property
    def threebot_client(self):
        j.sal.nettools.waitConnectionTest(self.ip_address, self.gedis_port, 900)
        name = self.name.replace(".", "_")
        try:
            j.clients.gedis._model.get_by_name(name=name).delete()
        except j.exceptions.NotFound:
            pass
        return j.clients.gedis.get(name=name, port=self.gedis_port, host=self._machine.ip_address)

    @property
    def ssh_client(self):
        j.sal.nettools.waitConnectionTest(self.ip_address, self.ssh_port, 600)
        return j.clients.ssh.get(
            name=f"{self.name}_docker",
            addr=self._parent._parent._machine.ip_address,
            port=self.ssh_port,
            sshkey_name=self._machine._deployer.ssh_key,
        )


class Containers(j.baseclasses.object_config_collection):

    _CHILDCLASS = Container
