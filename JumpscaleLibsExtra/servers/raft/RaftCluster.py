from Jumpscale import j


TEMPLATE = """
members = "localhost:4441,localhost:4442,localhost:4443"
secret_ = ""
giturl = ""
cmd = ""
"""

JSConfigBase = j.baseclasses.object


class RaftCluster(JSConfigBase):
    def __init__(self, instance, data=None, parent=None, interactive=False):
        if data is None:
            data = {}
        JSConfigBase.__init__(
            self, instance=instance, data=data, parent=parent, template=TEMPLATE, ui=None, interactive=interactive
        )

    @property
    def members(self):
        res = []
        for item in self.config.data["members"].split(","):
            addr, port = item.split(":")
            addr = addr.strip()
            port = int(port)
            res.append((addr, port))
        return res

    def start(self, background=True):
        def sstart(port):
            members = ""
            for addr0, port0 in self.members:
                if int(port0) != int(port):
                    members += "%s:%s," % (addr0, port0)
            members = members.rstrip(",")

            cmd0 = self.config.data["cmd"]
            secret = self.config.data["secret_"]
            cmd = 'mkdir -p /tmp/raft;cd /tmp/raft;js_shell \'cl=%s;cl(port=%s,members="%s",secret="%s" )\'' % (
                cmd0,
                port,
                members,
                secret,
            )
            print(cmd)
            j.servers.tmux.execute(
                cmd, session="main", window="raft_%s" % port, pane="main", session_reset=False, window_reset=True
            )

        for addr, port in self.members:
            if addr in ["localhost", "127.0.0.1", "local"]:
                sstart(port)

        if not j.core.platformtype.myplatform.platform_is_osx:
            raise Exception(
                "issue #33 - implement to find local ipaddr and "
                "then based on own addr decide to start locally or not"
            )
            # from IPython import embed;embed(colors='Linux')
