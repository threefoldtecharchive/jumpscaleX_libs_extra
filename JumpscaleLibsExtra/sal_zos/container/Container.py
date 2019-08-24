import logging
import signal
import time
from io import BytesIO

import netaddr
from Jumpscale import j
from JumpscaleLibs.clients.zero_os.protocol.Response import ResultError

from ..utils import get_zt_ip

logging.basicConfig(level=logging.INFO)
default_logger = logging.getLogger(__name__)


MiB = 1024 ** 2


class Containers:
    def __init__(self, node, logger=None):
        self.node = node

    def list(self):
        containers = []
        for container in self.node.client.container.list().values():
            containers.append(Container.from_containerinfo(container, self.node))
        return containers

    def get(self, name):
        try:
            container = self.node.client.container.get(name)
            if not container:
                raise j.exceptions.NotFound("Could not find container with name {}".format(name))
            container["container"]["id"] = container.pop("id")
            return Container.from_containerinfo(container, self.node)
        except ResultError:
            # get is not implemented, fall back to old method
            pass

        containers = list(self.node.client.container.find(name).values())
        if not containers:
            raise j.exceptions.NotFound("Could not find container with name {}".format(name))
        if len(containers) > 1:
            raise j.exceptions.NotFound("Found more than one containter with name {}".format(name))
        return Container.from_containerinfo(containers[0], self.node)

    def create(
        self,
        name,
        flist,
        hostname=None,
        mounts=None,
        nics=None,
        host_network=False,
        ports=None,
        storage=None,
        init_processes=None,
        privileged=False,
        env=None,
        identity=None,
        cpu=None,
        memory=None,
    ):
        """
        Create a new container

        :param name: name of the container
        :type name: string
        :param flist: location of the flist to use. It can be an URL or a absolute path on the host 0-OS.
        :type flist: string
        :param hostname: if specified set the hostname of the container, defaults to None
        :param hostname: string, optional
        :param mounts: a dict with {host_source: container_target} mount points.
                       where host_source directory must exists.
                       host_source can be a url to a flist to mount.
        :param mounts: dict, optional
        :param nics: Configure the attached nics to the container
                     nics is a list of dict
                     each nic object is a dict of the format
                     {
                        # one of default, bridge, zerotier, macvlan, passthrough, vlan, or vxlan (note, vlan and vxlan only supported by ovs)
                        'type': nic_type
                        'id': id # depends on the type
                            bridge: bridge name,
                            zerotier: network id,
                            macvlan: the parent link name,
                            passthrough: the link name,
                            vlan: the vlan tag,
                            vxlan: the vxlan id
                        'name': name of the nic inside the container (ignored in zerotier type)
                        'hwaddr': Mac address of nic.
                        'config': { # config is only honored for bridge, vlan, and vxlan types
                            'dhcp': bool,
                            'cidr': static_ip # ip/mask
                            'gateway': gateway
                            'dns': [dns]
                        }
                     }
        :param nics: list, optional
        :param host_network: Specify if the container should share the same network stack as the host.
                             if True, container creation ignores ports arguments below.
        :param host_network: bool, optional
        :param ports: A dict of host_port: container_port pairs (only if default networking is enabled)
                       Example: ports={8080: 80, 7000:7000}
                       Source Format: NUMBER, IP:NUMBER, IP/MAST:NUMBER, or DEV:NUMBER
                       Check https://github.com/threefoldtech/0-core/blob/development/docs/networking/portforwards.md for full syntax
        :param ports: dict, optional
        :param storage: An Url to the 0-db storage to use to mount the root flist (or any other mount that requires 0-fs)
                        if not provided, the default one from core0 configuration will be used.
        :param storage: string, optional
        :param init_processes: a list of dict describing some processes to run when starting the container
                               examples:
                               [{
                                    "name": "echo",
                                    "args": ["hello", "world"],
                                    "pwd": "/root",
                                    "stdin": "",
                                    "id": None,
                                    "environment": ["DEBUG=0"]
                                }]
        :param init_processes: list, optional
        :param privileged: If true, container runs in privileged mode.
        :param privileged: bool, optional
        :param env: a dict with the environment variables needed to be set for the container, defaults to None
        :param env: dict, optional
        :param identity: zerotier identity to assign to the container, if not specified an identify will be created automatically
        :param identity: string, optional
        :param cpu: if not None, specified the number of CPU the container can use
                    if None, on limitation
        :param cpu: int, optional
        :param memory: if not None, specified the amount of memory in MiB the container can allocate
                       if None, no limitation
        :param memory: int, optional
        :return: a Container
        :rtype: Container
        """

        default = False
        nics = nics or []
        for nic in nics:
            if "default" in nic["type"]:
                default = True
                break
        if not default:
            nics.append({"type": "default", "id": "None", "hwaddr": "", "name": "nat0"})
        container = Container(
            name=name,
            node=self.node,
            flist=flist,
            hostname=hostname,
            mounts=mounts,
            nics=nics,
            host_network=host_network,
            ports=ports,
            storage=storage,
            init_processes=init_processes,
            privileged=privileged,
            env=env,
            identity=identity,
            cpu=cpu,
            memory=memory,
        )
        container.start()
        return container


class Container:
    """Zero-OS Container"""

    def __init__(
        self,
        name,
        node,
        flist,
        hostname=None,
        mounts=None,
        nics=None,
        host_network=False,
        ports=None,
        storage=None,
        init_processes=None,
        privileged=False,
        identity=None,
        env=None,
        cpu=None,
        memory=None,
        logger=None,
    ):
        """
        TODO: write doc string
        filesystems: dict {filesystemObj: target}
        """

        self.name = name
        self.node = node
        self.mounts = mounts or {}
        self.hostname = hostname
        self.flist = flist
        self.ports = ports or {}
        self._nics = nics or []
        self.host_network = host_network
        self.storage = storage
        self.init_processes = init_processes or []
        self.privileged = privileged
        self._identity = identity
        self.env = env or {}
        self.cpu = cpu
        self.memory = memory
        self._client = None
        self.logger = logger or default_logger

        for nic in self.nics:
            nic.pop("ztClient", None)
            if nic.get("config", {}).get("gateway", ""):
                nic["monitor"] = True

    @classmethod
    def from_containerinfo(cls, containerinfo, node, logger=None):
        logger = logger or default_logger
        j.tools.logger._log_debug("create container from info")

        arguments = containerinfo["container"]["arguments"]
        return cls(
            name=arguments["name"],
            node=node,
            flist=arguments["root"],
            hostname=arguments["hostname"],
            mounts=arguments["mount"],
            nics=arguments["nics"],
            host_network=arguments["host_network"],
            ports=arguments["port"],
            storage=arguments["storage"],
            privileged=arguments["privileged"],
            identity=arguments["identity"],
            env=arguments["env"],
            logger=logger,
        )

    @property
    def id(self):
        j.tools.logger._log_debug("get container id")
        info = self.info
        if info:
            return info["container"]["id"]
        return

    @property
    def info(self):
        j.tools.logger._log_debug("get container info")
        try:
            data = self.node.client.container.get(self.name)
            if not data:
                # could be that the container with this name does not exist yet
                return
            # keep old data layout
            if "id" in data:
                data["container"]["id"] = data.pop("id")
                return data
        except ResultError:
            pass

        # fall back to old method
        j.tools.logger._log_debug("falling back to list iteration")
        for containerid, container in self.node.client.container.list().items():
            if self.name == container["container"]["arguments"]["name"]:
                containerid = int(containerid)
                container["container"]["arguments"]["identity"] = self._identity
                if self._client and self._client.container != containerid:
                    self._client = None
                container["container"]["id"] = int(containerid)
                return container
        return

    @property
    def identity(self):
        if not self._identity:
            if self.is_running():
                for nic in self.nics:
                    if nic["type"] == "zerotier":
                        self._identity = self.client.zerotier.info()["secretIdentity"]
        return self._identity

    @property
    def public_identity(self):
        if self.is_running():
            for nic in self.nics:
                if nic["type"] == "zerotier":
                    return self.client.zerotier.info()["publicIdentity"]

    @property
    def ipv6(self, interface=None):
        """
        return a list of all the ipv6 present in the container

        the local ip are skipped

        :param interface: only return the ips of a certain interface.
                          If none scan all the existing interfaces , defaults to None
        :param interface: str, optional
        :return: list of ip
        :rtype: list
        """

        interfaces = [interface]
        if interface is None:
            interfaces = [l["name"] for l in self.client.ip.link.list() if l["name"] not in ["lo"]]

        ips = []
        for interface in interfaces:
            for ip in self.client.ip.addr.list(interface):
                network = netaddr.IPNetwork(ip)
                if network.version == 6 and network.is_link_local() is False:
                    ips.append(network.ip)
        return ips

    def default_ip(self, interface=None):
        """
        Returns the ip if the container has a default nic
        :return: netaddr.IPNetwork
        """
        if interface is None:
            for route in self.client.ip.route.list():
                if route["gw"]:
                    interface = route["dev"]
                    break
            else:
                raise j.exceptions.NotFound("Could not find default interface")
        for ipaddress in self.client.ip.addr.list(interface):
            ip = netaddr.IPNetwork(ipaddress)
            if ip.version == 4:
                break
        else:
            raise j.exceptions.NotFound("Failed to get default ip")
        return ip

    def add_nic(self, nic):
        self.node.client.container.nic_add(self.id, nic)

    def remove_nic(self, nicname):
        for idx, nic in enumerate(self.info["container"]["arguments"]["nics"]):
            if nic["state"] == "configured" and nic["name"] == nicname:
                break
        else:
            return
        self.node.client.container.nic_remove(self.id, idx)

    @property
    def client(self):
        if not self._client:
            self._client = self.node.client.container.client(self.id)
        return self._client

    def upload_content(self, remote, content):
        if isinstance(content, str):
            content = content.encode("utf8")
        bytes = BytesIO(content)
        self.client.filesystem.upload(remote, bytes)

    def download_content(self, remote):
        buff = BytesIO()
        self.client.filesystem.download(remote, buff)
        return buff.getvalue().decode()

    def _create_container(self, timeout=60):
        j.tools.logger._log_debug("send create container command to zero-os (%s)", self.flist)
        tags = [self.name]
        if self.hostname and self.hostname != self.name:
            tags.append(self.hostname)

        # Populate the correct mounts dict
        if type(self.mounts) == list:
            mounts = {}
            for mount in self.mounts:
                try:
                    sp = self.node.storagepools.get(mount["storagepool"])
                    fs = sp.get(mount["filesystem"])
                except KeyError:
                    continue
                mounts[fs.path] = mount["target"]
            self.mounts = mounts

        cgroups = []
        if self.cpu:
            # create a cgroup for this container
            # and assign self.cpu number of cpu to the cgroup
            self.node.client.cgroup.ensure("cpuset", self.name)
            cpu_to_use = next_cpus(self.node, int(self.cpu))
            cpu_to_use = ",".join([str(x) for x in cpu_to_use])
            self.node.client.cgroup.cpuset(self.name, cpu_to_use)
            cgroups.append(("cpuset", self.name))

        if self.memory:
            self.node.client.cgroup.ensure("memory", self.name)
            memory = self.memory * MiB
            self.node.client.cgroup.memory(self.name, memory)
            cgroups.append(("memory", self.name))

        try:
            job = self.node.client.container.create(
                root_url=self.flist,
                mount=self.mounts,
                host_network=self.host_network,
                nics=self.nics,
                port=self.ports,
                tags=tags,
                name=self.name,
                hostname=self.hostname,
                storage=self.storage,
                privileged=self.privileged,
                identity=self.identity,
                env=self.env,
                cgroups=cgroups,
            )
        except:
            # clean up cgroups in case the container fails to start
            self.node.client.cgroup.remove("memory", self.name)
            self.node.client.cgroup.remove("cpuset", self.name)
            raise

        self._client = self.node.client.container.client(int(job.get(timeout)))
        self.identity  # try to get zerotier identity if any

    def is_job_running(self, id):
        try:
            for _ in self.client.job.list(id):
                return True
            return False
        except Exception as err:
            if str(err).find("invalid container id"):
                return False
            raise

    def stop_job(self, id, signal=signal.SIGTERM, timeout=30):
        is_running = self.is_job_running(id)
        if not is_running:
            return

        j.tools.logger._log_debug("stop job: %s", id)

        self.client.job.kill(id)

        # wait for the daemon to stop
        start = time.time()
        end = start + timeout
        is_running = self.is_job_running(id)
        while is_running and time.time() < end:
            time.sleep(1)
            is_running = self.is_job_running(id)

        if is_running:
            raise j.exceptions.Base("Failed to stop job {}".format(id))

    def is_port_listening(self, port, timeout=60, network=("tcp", "tcp6")):
        def is_listening():
            for lport in self.client.info.port():
                if lport["network"] in network and lport["port"] == port:
                    return True
            return False

        if timeout:
            start = time.time()
            while start + timeout > time.time():
                if is_listening():
                    return True
                time.sleep(1)
            return False
        else:
            return is_listening()

    def start(self):
        if not self.is_running():
            j.tools.logger._log_debug("start %s", self)
            self._create_container()
            for process in self.init_processes:
                cmd = "{} {}".format(process["name"], " ".join(process.get("args", [])))
                pwd = process.get("pwd", "")
                stdin = process.get("stdin", "")
                id = process.get("id")
                env = {}
                for x in process.get("environment", []):
                    k, v = x.split("=")
                    env[k] = v
                self.client.system(command=cmd, dir=pwd, stdin=stdin, env=env, id=id)

    def stop(self):
        """
        will stop the container and also his mountpoints
        :return:
        """
        if not self.is_running():
            return
        j.tools.logger._log_debug("stop %s", self)

        self.node.client.cgroup.remove("memory", self.name)
        self.node.client.cgroup.remove("cpuset", self.name)

        self.node.client.container.terminate(self.id)
        self._client = None

    def is_running(self):
        return self.node.is_running() and self.id is not None

    @property
    def nics(self):
        if self.is_running():
            return list(filter(lambda nic: nic["state"] == "configured", self.info["container"]["arguments"]["nics"]))
        else:
            nics = []
            for nic in self._nics:
                nic.pop("state", None)
                nics.append(nic)

            return nics

    def waitOnJob(self, job):
        MAX_LOG = 15
        logs = []

        def callback(lvl, message, flag):
            if len(logs) == MAX_LOG:
                logs.pop(0)
            logs.append(message)

            if flag & 0x4 != 0:
                erroMessage = " ".join(logs)
                raise j.exceptions.Base(erroMessage)

        resp = self.client.subscribe(job.id)
        resp.stream(callback)

    def get_forwarded_port(self, port):
        for k, v in self.ports.items():
            if v == port:
                return int(k.split(":")[-1])

    def authorize_networks(self, nics):
        public_identity = self.public_identity
        if not public_identity:
            raise j.exceptions.Base("Failed to get zerotier public identity")
        for nic in nics:
            if nic["type"] == "zerotier":
                client = j.clients.zerotier.get(nic["ztClient"], create=False, die=True, interactive=False)
                network = client.network_get(nic["id"])
                network.member_add(public_identity, self.name)

    @property
    def mgmt_addr(self):
        support_network = "172.29.0.0/16"
        return get_zt_ip(self.client.info.nic(), False, support_network)

    def __str__(self):
        return "Container <{}>".format(self.name)

    def __repr__(self):
        return str(self)


def next_cpus(node, nr):
    """
    return the cpu numbers of the cpu
    the least assgined

    :param nr: number of cpu to return
    :type nr: int
    :return: list of cpu number
    :rtype: list
    """
    max_cpu_nr = len(node.client.info.cpu())
    if nr > max_cpu_nr:
        raise j.exceptions.Value("maximum number of cpu is %s" % max_cpu_nr)

    cgroup = node.client.cgroup

    cgroup_names = cgroup.list()["cpuset"]
    all_used = []
    for name in cgroup_names:
        all_used.append(cpu_used(cgroup.cpuset(name)["cpus"]))

    appearances = {cpu: 0 for cpu in range(max_cpu_nr)}
    for outer in all_used:
        for cpu in outer:
            if cpu not in appearances:
                raise j.exceptions.Base("cpu number %s doesn't exist, but it is reported as used" % cpu)
            appearances[cpu] += 1

    # sort by less used
    appearances = sort_by_least_used(appearances)
    return sorted(appearances[:nr])


def cpu_used(cpuset):
    """
    parse the cpu used as outputed by cgroup
    """

    used = set()
    groups = cpuset.split(",")
    for group in groups:
        splitted = group.split("-")
        if len(splitted) == 1:
            # handle empty
            if not splitted[0]:
                continue
            used.add(int(splitted[0]))
        else:
            start = int(splitted[0])
            end = int(splitted[1])
            for i in range(start, end + 1):
                used.add(i)
    return list(used)


def sort_by_least_used(dict_):
    return [x[0] for x in sorted(dict_.items(), key=lambda kv: kv[1])]
