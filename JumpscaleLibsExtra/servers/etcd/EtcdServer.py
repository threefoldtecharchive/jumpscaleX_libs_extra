from Jumpscale import j


class EtcdServer(j.baseclasses.object):
    __jslocation__ = "j.servers.etcd"

    def start(self, config_file=None):
        """start etcd

        :param config_file: config file path, defaults to None
        :type config_file: str, optional
        :return: tmux pane
        :rtype: tmux.Pane
        """
        if not j.core.tools.cmd_installed("etcd"):
            self.install()
        cmd = j.sal.fs.joinPaths(j.core.dirs.BINDIR, "etcd")
        if config_file:
            cmd += " --config-file %s" % config_file
        return j.servers.tmux.execute(cmd, window="etcd", pane="etcd", reset=True)

    def stop(self, pid=None, sig=None):
        """Stops etcd process

        :param pid: pid of the process, if not given, will kill by name
        :type pid: long, defaults to None
        :param sig: signal, if not given, SIGKILL will be used
        :type sig: int, defaults to None
        """
        if not j.core.tools.cmd_installed("etcd"):
            raise RuntimeError("install etcd: 'j.builders.db.etcd.install()'")
        if pid:
            j.sal.process.kill(pid, sig)
        else:
            full_path = j.sal.fs.joinPaths(j.core.dirs.BINDIR, "etcd")
            j.sal.process.killProcessByName(full_path, sig)

    def install(self, reset=False):
        j.builders.db.etcd.install(reset=reset)
