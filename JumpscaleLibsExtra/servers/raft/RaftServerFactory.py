from pprint import pprint as print

from Jumpscale import j

from .RaftServer import RaftServer
from .RaftCluster import RaftCluster


class RaftServerFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.servers.raftserver"

    def _init(self, **wargs):
        super(RaftServerFactory, self).__init__(RaftCluster)

    def get_by_params(
        self,
        instance="main",
        secret="1233",
        members="localhost:4441,localhost:4442,localhost:4443",
        cmd="j.servers.raftserver.example_server_class_get()",
    ):
        # TODO: use new style config management
        data = {}
        data["secret_"] = secret
        data["members"] = members
        data["cmd"] = cmd
        return self.get(instance=instance, data=data, create=True)

    def example_server_class_get(self):
        return RaftServer

    def start_local(
        self, nrservers=3, startport=4000, cmd="j.servers.raftserver.example_server_class_get()", secret="1233"
    ):
        """
        start local cluster of 5 nodes, will be run in tmux
        """
        members = ""
        for i in range(nrservers):
            members += "localhost:%s," % (startport + i)

        members = members.rstrip(",")

        cluster = self.get_by_params(instance="main", secret=secret, members=members, cmd=cmd)
        cluster.start(background=True)

    def test(self):
        """
        js_shell 'j.servers.raftserver.test()'
        """
        self.start_local(nrservers=4, startport=6000, cmd="j.servers.raftserver.example_server_class_get()")

    def test_nopasswd(self):
        """
        js_shell 'j.servers.raftserver.test_nopasswd()'
        """
        self.start_local(nrservers=4, startport=6000, cmd="j.servers.raftserver.example_server_class_get()", secret="")
