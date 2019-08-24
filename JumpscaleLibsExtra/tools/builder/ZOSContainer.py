from Jumpscale import j
import os

import time


class ZOSContainer(j.baseclasses.object_config):

    _SCHEMATEXT = """
    @url = zos.container.config
    date_start = 0 (D)
    description = ""
    name = ""
    authorized = False (B)
    pid = 0 (I)
    container_id = 0 (I) 
    progress = (LS)
    flist = ""
    nics = (LO) !zos.container.nic
    sshport = 0 (I)
    
    @url = zos.container.nic
    type = "default"    
    """

    def __init__(self, zos, name):

        j.baseclasses.object_config.__init__(self)

        self.zos = zos
        self.name = name
        self.zosclient = zos.zosclient

    def _init(self, **kwargs):

        self._container = None
        self._node_connected = False

        self.flist = "https://hub.grid.tf/tf-bootable/ubuntu:18.04.flist"
        self._create()

    def clean(self):
        """

        :return:
        """

        C = """
        find / -name "*.pyc" -exec rm -rf {} \;
        find / -name "*.pyo" -exec rm -rf {} \;
        find / -name "*.bak" -exec rm -rf {} \;
        find / -name "*.deb" -exec rm -rf {} \;
        find / -name "*.log" -exec rm -rf {} \;
        find /root/code -name "*.git" -exec rm -rf {} \;
        find /root/code -name "*.vscode" -exec rm -rf {} \;
        find /root/code -name "*.idea" -exec rm -rf {} \;
        find / -name "*.log.xz" -exec rm -rf {} \;
        rm -rf /tmp
        rm -f /var/log/*
        mkdir -p /tmp
                
        """

    @property
    def nics_dict(self):
        """
        e.g.

        nics = '[
            {
            "type": "default"
            }
        ]'

        :return:
        """
        nics_ret = []
        for nic in self.nics:
            d = {"type": nic.type}
            nics_ret.append(d)
        return nics_ret

    @property
    def zos_private_address(self):
        return self.zos.zos_private_address

    def start(self):
        self.api

    def stop(self):
        self.zosclient.client.container.terminate(self._container_id)

    def _create(self):
        print("creating builder container...")
        self.progress = []  # make sure we don't remember old stuff
        self.model_save()

        self._log_warning("A")
        self.nics = []
        # TODO: something wrong here, it keeps on adding nics, have no idea why
        if len(self.nics) == 0:
            self._log_warning("ADDNIC")
            nic = self.nics.new()
            nic.type = "default"
            self.model_save()
        # j.shell()

        self._log_info(
            "create container: %s %s sshport:%s \nnics:\n%s" % (self.name, self.flist, self.sshport, self.nics_dict)
        )

        def getAgentPublicKeys():
            rc, keys, _ = j.sal.process.execute("ssh-add -L", die=False)
            if rc == 0:
                return keys
            return ""

        keys = getAgentPublicKeys()

        if keys == "":
            raise j.exceptions.Base("couldn't find sshkeys in agent or in default paths [generate one with ssh-keygen]")

        # zos client here is node client WHICH doesn't support config parameter.
        try:
            if self.zos._zostype == "vbox":
                self.sshport = self.sshport + 20
                self.model_save()
            self._container_id = self.zosclient.client.container.create(
                name=self.name,
                hostname=self.name,
                root_url=self.flist,
                nics=self.nics_dict,
                port={self.sshport: 22},
                config={"/root/.ssh/authorized_keys": keys},
            ).get()

            # TODO ONLY IF VBOX
            self.zosclient.client.nft.open_port(self.sshport)

            # RUN SSHD
            container_client = self.zosclient.client.container.client(self._container_id)
            print(container_client.system("service ssh start").get())
            print(container_client.system("service ssh status").get())

        except Exception as e:
            print(self._container_id, e)
            if self._container_id:
                self.zosclient.client.container.terminate(self._container_id)
            print(e)
            if self.zos._zostype == "vbox":
                self.sshport = self.sshport - 20
                self.model_save()
            raise j.exceptions.Operations("?")

        info = self.zosclient.client.container.list()[str(self._container_id)]["container"]
        while "pid" not in info:
            time.sleep(0.1)
            self._log_debug("waiting for container to start")
        self.pid = info["pid"]
        self.container_id = str(self._container_id)
        self.model_save()
        assert self.zosclient.client.container.client(self._container_id).ping()

    @property
    def container(self):
        if self._container is None:
            try:
                self._container = self.zosclient.client.container.client(self._container_id)
            except:
                self._create()
                self._container = self.zosclient.client.container.client(self._container_id)

        return self._container

    @property
    def info(self):
        # assert self.port == self.container.info
        return self.container.info

    @property
    def api(self):
        """
        :return: zero-os container object
        """

        return self.container

    @property
    def prefab(self):
        return self.node.prefab

    @property
    def node(self):
        """
        :return: node object as used in node manager, allows you to get to prefab, ...
        """
        if self._node_connected:
            return self._node

        self.start()

        if self.authorized is False:

            sshclient = j.clients.ssh.new(
                addr=self.zos_private_address,
                port=self.sshport,
                instance=self.name,
                die=True,
                login="root",
                passwd="rooter",
                stdout=True,
                allow_agent=False,
                use_paramiko=True,
            )

            print(
                "waiting for ssh to start for container:%s\n (if the ZOS VM is new, will take a while, OS files are being downloaded)"
                % self.name
            )
            for i in range(50):
                try:
                    res = sshclient.connect()
                    rc, out, err = sshclient.execute("which bash")
                    if "bash" in out:
                        break
                except j.exceptions.RuntimeError as e:
                    if "Could not connect to" in str(e):
                        continue
                    raise e

            self._log_info("ssh connected")
            key = j.clients.sshkey.list()[0]

            sshclient.ssh_authorize(user="root", key=key)

            self.authorized = True
            self.model_save()

            self._log_info("container deployed")
            self._log_info(
                "to connect to it do: 'ssh root@%s -p %s' (password: rooter)" % (self.zos_private_address, self.port)
            )
            self._log_info("can also connect using js_node toolset, recommended: 'js_node ssh -i %s'" % self.name)
        if j.clients.ssh.get("builder").sshkey:
            key_path = j.clients.ssh.get("builder").sshkey.path
            keyname_paths = os.path.split(key_path)
            keyname = keyname_paths[len(keyname_paths) - 1]
        else:
            keyname = ""
        sshclient = j.clients.ssh.new(
            addr=self.zos_private_address,
            port=self.port,
            instance=self.name,
            die=True,
            login="root",
            keyname=keyname,
            stdout=True,
            allow_agent=True,
            use_paramiko=True,
        )
        self._node_connected = True

        return self._node

    @property
    def sshport(self):

        # CHECK IF VBZOS if yes use port per SSH connection because is same ip addr
        # CHECK IF ZOS direct (no VB), then is zerotier addr with std ssh port...
        if self.zos._zostype == "vbox":
            if self.sshport == 0:
                if self.zos.sshport_last == 0:
                    self.zos.sshport_last = 6000
                else:
                    self.zos.sshport_last += 1
                self.sshport = self.zos.sshport_last

        return self.sshport

    # def zero_os_private(self, node):
    #     self._log_debug("resolving private virtualbox address")
    #
    #     private = j.clients.virtualbox.zero_os_private_address(node)
    #     self._log_info("virtualbox machine private address: %s" % private)
    #
    #     node = j.clients.zos.get('builder_private', data={'host': private})
    #     node.client.ping()
    #
    #     return node

    def build_python_jumpscale(self, reset=False):

        if reset:
            self.done_reset()

        if not self.done_check("jscore_install"):
            self.prefab.jumpscale.jumpscalecore.install()
            # TODO: *1 do some tests, did jumpscale install well e.g. do an echo test with shell
            self.done_set("jscore_install")

        self.node.sync()  # sync all local jumpscale code to the container

        if not self.done_check("python_build"):
            self.prefab.runtimes.python.build()
            # TODO: *1 do some tests, did python really build well
            self.done_set("python_build")

        cmd = "kosmos 'j.tools.sandboxer.python.do(build=False)'"  # building did already happen
        j.sal.process.execute(cmd)

        # TODO:*1 add some checks in there to make sure the building happened ok
        # TODO:*1 there is bug, the packaging does not find the right directories

    def __repr__(self):
        return "container:%s" % self.name

    __str__ = __repr__
