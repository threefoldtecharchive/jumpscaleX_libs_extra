import os
import time
from Jumpscale import j
from random import SystemRandom
from string import ascii_uppercase
from string import digits


DEF_PORTS = {"CONFIG": 27018, "SHARD": 27019, "ROUTE": 27017}


class Mongod:
    """ Class  Mongod is responsible to manage a single instance of mongod
    """

    _CMD = {"shard": "shardsvr", "config": "configsvr"}

    def __init__(self, container, replica_set, port, dir, db_type):
        self.container = container
        self.replica_set = replica_set
        self.dir = dir
        self._job_id = "".join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(5))
        self.ip = self.container.default_ip().ip.format()
        self.port = port
        if db_type not in ["shard", "config"]:
            raise j.exceptions.Value(
                '"{}" is not a valid role, only roles "config" and "shard" are allowed'.format(db_type)
            )
        self.db_type = db_type
        self._cmd = self._CMD[db_type]

    def start(self, timeout=30, log_to_file=False):
        """ Start instance of mongod

            :param timeout: timeout on starting the instance of mongod
            :param log_to_file: if True log mongod output to /tmp/log_shard or /tmp/log_config, depending on the instance type
        """

        if not self.is_running():
            j.tools.logger._log_info('start a member of the replica set "{}"'.format(self.replica_set))

        # ensure directory
        self.container.client.filesystem.mkdir(self.dir)

        cmd = "mongod --{} --replSet {} --dbpath {}  --bind_ip localhost,{} --port {}".format(
            self._cmd, self.replica_set, self.dir, self.ip, self.port
        )
        if log_to_file:
            cmd = "{} --logpath /tmp/log_{}".format(cmd, self.db_type)

        self.container.client.system(cmd, id=self._job_id)

        # wait for server to start
        start = time.time()
        while time.time() < start + timeout:
            time.sleep(1)
            if self.is_running():
                break
        else:
            raise j.exceptions.Base("Failed to start mongodb server")

    def init_replica_set(self, hosts):
        """ Init replica set

            :param hosts: list of addresses of other member of @self.replica_set
        """

        # check if server is running
        if not self.is_running():
            raise j.exceptions.Base(
                'Cannot initialize replica set, "{}" mongodb instance is not running'.format(self.replica_set)
            )

        j.tools.logger._log_info("init replica set {}".format(self.replica_set))

        # add current host to the list of hosts
        hosts.append("{}:{}".format(self.ip, self.port))

        # create js script
        config = ""
        for idx, host in enumerate(hosts):
            config = "%s { _id: %d, host: '%s' }," % (config, idx, host)

        config = """
        rs.initiate(
            {_id : '%s',
            members: [
                %s
            ]
        })""" % (
            self.replica_set,
            config,
        )

        # create config file to init config replica set
        conf_file = "/tmp/config.js"
        self.container.client.filesystem.remove(conf_file)
        self.container.client.bash('echo "%s" >> %s' % (config, conf_file)).get()
        cmd = "mongo --port {port} {file}".format(port=self.port, file=conf_file)
        result = self.container.client.system(cmd).get()
        error_check(result)

    def is_running(self):
        """ Check if instance is running  """
        try:
            for _ in self.container.client.job.list(self._job_id):
                return True
            return False
        except Exception as err:
            if str(err).find("invalid container id"):
                return False
            raise

    def stop(self, timeout=30):
        """
        Stop all started mongodb instances

        :param timeout: time in seconds to wait for the mongodb instance to stop
        """
        if not self.container.is_running():
            return

        if self.is_running():
            self.container.client.job.kill(self._job_id)
            # wait to stop
            start = time.time()
            while time.time() < start + timeout:
                time.sleep(1)
                if not self.is_running():
                    break
            else:
                raise j.exceptions.Base("failed to stop mongod instance")


class Mongodb:
    """ Class Mongodb is responsible to create and manage containers with mongodb instances.

        :method start: deploys instances of shard server and config servers in a single container.
        :method init_replica_sets: initializes shard replica set and config replica set.
        :method stop: stops all mongodb instances in the container.
        :method destroy: stop the container.
"""

    FLIST = "https://hub.grid.tf/ekaterina_evdokimova_1/ubuntu-16.04-mongodb.flist"
    _CONFIG_DIR = "/data/configdb"
    _SHARD_DIR = "/data/db"

    def __init__(
        self,
        name,
        node,
        container_name=None,
        config_replica_set=None,
        config_port=None,
        config_mount=None,
        shard_replica_set=None,
        shard_port=None,
        shard_mount=None,
        route_port=None,
    ):
        """
        :param name: instance name
        :param node: sal of the node to deploy mongodb on
        :param container_name: name of the container, if not given will be generated
        :param config_replica_set: name of config server replica set
        :param config_port: config server port. Default to 27018
        :param shard_replica_set: name of shard server replica set
        :param shard_port: shard server port. Default to 27019
        :param route_port: route server server port. Default to 27017
        :param config_mount: dictionary with configuration mount directory for config server.
                            If not given db directory will not be mounted on a persistent volume.
        :param shard_mount: dictionary with configuration of mongo shard server.
                            If not given db directory will not be mounted on a persistent volume.
        @config_mount and @shard_mount are expected in format:
            {'storagepool': 'zos-cache'      # storagepool name
             'fs': 'fs_name'                # filesystem mane
             'dir': '/mongo/configdb'}      # subdirectory

        """
        self.name = name
        self.node = node
        self._container_name = container_name or "mongodb_{}".format(self.name)
        self._container = None

        self.config_replica_set = config_replica_set
        self.shard_replica_set = shard_replica_set

        self.config_mount = config_mount
        self.config_mount["target_dir"] = self._CONFIG_DIR

        self.shard_mount = shard_mount
        self.shard_mount["target_dir"] = self._SHARD_DIR

        self.shard_port = shard_port or DEF_PORTS["SHARD"]
        self.config_port = config_port or DEF_PORTS["CONFIG"]

        self._validate()

        self.config_server = None
        self.shard_server = None

    def _validate(self):
        # check mount configs whether all required fields are provided
        for mount in [self.shard_mount, self.config_mount]:
            for key in ["storagepool", "fs", "dir"]:
                if not mount.get(key):
                    raise j.exceptions.Value(
                        """Mount point config should be set to None or given correctly.
                                        Current config: {}, expected: {}""".format(
                            mount,
                            """ {'storagepool': '<storagepool name>'
                                        'fs': '<fs_name>'
                                        'dir': '<subdir on fs_name>'}
                                    """,
                        )
                    )

    @property
    def _container_data(self):
        """
        :return: data used for mongodb container
        """
        # get node filesystem
        node_fs = self.node.client.filesystem

        # mount directories for instances SHARD and CONFIG
        mounts = {}
        for mount in [self.config_mount, self.shard_mount]:
            sp = self.node.storagepools.get(mount["storagepool"])
            fs = sp.get(mount["fs"])

            # get absolute path to the directory on persistent volume
            mount_dir = os.path.join(fs.path, "".join(mount["dir"].split("/", 1)))

            # ensure directory on the filesystem
            node_fs.mkdir(mount_dir)

            # mount directory on persistent storage
            mounts[mount_dir] = mount["target_dir"]

        # determine parent interface for macvlan
        candidates = list()
        for route in self.node.client.ip.route.list():
            if route["gw"]:
                candidates.append(route)
        if not candidates:
            raise j.exceptions.Base("Could not find interface for macvlan parent")
        elif len(candidates) > 1:
            raise j.exceptions.Base(
                "Found multiple eligible interfaces for macvlan parent: %s" % ", ".join(c["dev"] for c in candidates)
            )
        parent_if = candidates[0]["dev"]

        return {
            "name": self._container_name,
            "flist": self.FLIST,
            "nics": [{"type": "macvlan", "id": parent_if, "name": "stoffel", "config": {"dhcp": True}}],
            "mounts": mounts,
        }

    @property
    def container(self):
        """
        Get/create a container to run mongodb services on
        :return: mongodb container
        :rtype: container sal object
        """
        if not self._container:
            try:
                self._container = self.node.containers.get(self._container_name)
            except LookupError:
                self._container = self.node.containers.create(**self._container_data)

        return self._container

    @property
    def ip(self):
        """ Shortcut to ip address of the container """
        if not self.container.is_running:
            raise j.exceptions.Base('container "{}" is not running'.format(self._container_name))

        # return self.container.default_ip().ip.format()

        # wait for interface to start
        start, timeout = time.time(), 30
        while time.time() < start + timeout:
            try:
                ip = self.container.default_ip().ip.format()
                break
            except LookupError:
                time.sleep(1)
        else:
            raise j.exceptions.Base('cannot fetch container "{}" IP'.format(self._container_name))

        return ip

    def start(self, timeout=15, log_to_file=False):
        """ Start mongodb instance

            :param timeout: time in seconds to wait for the mongod gateway to start
            :param log_to_file: enable writing log for SHARD and CONFIG servers to
                the corrsponding files: /tmp/log_SHARD, /tmp/log_CONFIG
        """

        # get/start container
        container = self.container

        # wait until container ir fully running and able to return it's IP
        self.ip

        # start a member of the config replica set
        self.config_server = j.clients.zos.sal.get_mongod(
            container=container,
            replica_set=self.config_replica_set,
            port=self.config_port,
            dir=self.config_mount["target_dir"],
            db_type="config",
        )

        self.config_server.start(log_to_file=log_to_file)

        # start a member of the shard replica set
        self.shard_server = j.clients.zos.sal.get_mongod(
            container=container,
            replica_set=self.shard_replica_set,
            port=self.shard_port,
            dir=self.shard_mount["target_dir"],
            db_type="shard",
        )

        self.shard_server.start(log_to_file=log_to_file)

    def init_replica_sets(self, config_hosts, shard_hosts):
        """ Initialize config replica set and shard replica set """
        self.config_server.init_replica_set(config_hosts)
        self.shard_server.init_replica_set(shard_hosts)

    def stop(self):
        """ Stop config server and shard server in the container """
        self.config_server.stop()
        self.shard_server.stop()

    def destroy(self):
        """ Stop container where mongodb is running """
        self.stop()
        self.container.stop()


class Mongos:
    """ Class Mongodb is responsible to create and manage MongoDB routing service.

        :method start: deploys instance of mongos server
        :method stop: stops mongos instance
    """

    _JOB_ID = "mongos-routing-service"

    def __init__(self, container, port=None):
        """
        :param container: container object
        :param port: port to run mongos instance on
        """
        self.container = container
        self.port = port or DEF_PORTS["ROUTE"]

    @property
    def ip(self):
        """ Shortcut to ip address of the container """
        if not self.container.is_running:
            raise j.exceptions.Base('container "{}" is not running'.format(self.container.name))

        # wait for interface to start
        start, timeout = time.time(), 30
        while time.time() < start + timeout:
            try:
                ip = self.container.default_ip().ip.format()
                break
            except LookupError:
                time.sleep(1)
        else:
            raise j.exceptions.Base('cannot fetch container "{}" IP'.format(self.container.name))

        return ip

    def start(self, config_replica_set, config_hosts, timeout=15, log_to_file=False):
        """
        Start mongos instance with access to previously configured mongodb cluster.

            :param config_replica_set: name of config replica set.
            :param config_hosts: list of addresses of config server shards
            :param timeout: time in seconds to wait for the mongod gateway to start
            :param log_to_file: enable writing log to file /tmp/log_mongos
        """
        if self.is_running():
            return

        j.tools.logger._log_info("start mongos service")

        cmd = "mongos --configdb {}/{}  --bind_ip localhost,{} --port {}".format(
            config_replica_set, ",".join(config_hosts), self.ip, self.port
        )

        if log_to_file:
            cmd = "{} --logpath /tmp/log_mongos".format(cmd)

        self.container.client.system(cmd, id=self._JOB_ID)

        # wait for mongos to start
        start = time.time()
        while time.time() < start + timeout:
            time.sleep(1)
            if self.is_running():
                break
        else:
            raise j.exceptions.Base(
                "Failed to start mongodb routing service in contaner {}".format(self.container.name)
            )

    def add_shards(self, shard_replica_set, shard_hosts):
        """ Add members of shards replica set """

        for shard in shard_hosts:
            cmd = """mongo --host {}:{} --eval 'sh.addShard("{}/{}")' """.format(
                self.ip, self.port, shard_replica_set, shard
            )
            result = self.container.client.system(cmd).get()
            error_check(result)

    def is_running(self):
        """ Check if server of type @role is running

            Roles: SHARD, CONFIG, ROUTE
        """
        try:
            for _ in self.container.client.job.list(self._JOB_ID):
                return True
            return False
        except Exception as err:
            if str(err).find("invalid container id"):
                return False
            raise

    def stop(self, timeout=30):
        """
        Stop all started mongodb instances
        :param timeout: time in seconds to wait for the mongodb instance to stop
        """
        if not self.container.is_running():
            return

        if self.is_running():
            self.container.client.job.kill(self._JOB_ID)
            # wait to stop
            start = time.time()
            while time.time() < start + timeout:
                time.sleep(1)
                if not self.is_running():
                    break
            else:
                raise j.exceptions.Base("failed to stop mongos instance")

    def destroy(self):
        """ Stop container where mongodb is running """
        self.stop()
        self.container.stop()


def error_check(result, message=""):
    """ Raise error if call wasn't successfull """

    if result.state != "SUCCESS":
        err = "{}: {} \n {}".format(message, result.stderr, result.data)
        raise j.exceptions.Base(err)
