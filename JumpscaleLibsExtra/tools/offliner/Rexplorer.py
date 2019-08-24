from Jumpscale import j

JSBASE = j.baseclasses.object


class Rexplorer(j.baseclasses.object):
    def __init__(self):
        self.__jslocation__ = "j.tools.rexplorer"
        JSBASE.__init__(self)

    def install(self):
        """
        use prefab to install rexplorer & get it started

        kosmos 'j.tools.rexplorer.install()'
        :return:
        """
        p = j.tools.prefab.local
        p.runtimes.golang.install()
        p.runtimes.golang.get("github.com/threefoldfoundation/rexplorer")

    def start(self):
        """
        starts rexplorer in tmux
        result goes to redis
        kosmos 'j.tools.rexplorer.start()'
        :return:
        """
        cmd = "cd /tmp;rexplorer -f 'threefold:*'"
        j.servers.tmux.execute(
            cmd, session="main", window="rexplorer", pane="rexplorer", session_reset=False, window_reset=True
        )
