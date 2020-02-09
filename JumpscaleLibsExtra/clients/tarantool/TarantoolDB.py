from Jumpscale import j

import tarantool
import pystache
import os

JSBASE = j.baseclasses.object


class TarantoolDB(j.baseclasses.object):
    def __init__(self, name="test", path="$DATADIR/tarantool/$NAME", adminsecret="admin007", port=3301):
        JSBASE.__init__(self)
        self.path = j.dirs.replace_txt_dir_vars(path).replace("$NAME", name).strip()
        j.sal.fs.createDir(self.path)
        self.name = name
        self.login = "root"
        self.adminsecret = adminsecret
        self.addr = "localhost"
        self.port = port
        self.configTemplatePath = None

    @property
    def _path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__)).rstrip("/")

    def _setConfig(self):
        """
        if path None then will use template which is in this dir
        """
        path = self.configTemplatePath
        if path is None:
            path = "%s/config_template.lua" % self._path
        C = j.sal.fs.readFile(path)
        data = {}
        data["PORT"] = self.port
        data["NAME"] = self.name
        data["DBDIR"] = self.path
        data["SECRET"] = self.adminsecret

        C2 = pystache.render(C, **data)

        # add path to systemscripts
        systempath = "%s/systemscripts" % self._path
        C3 = "\npackage.path = '$path/?.lua;' .. package.path\n"
        C3 = C3.replace("$path", systempath)
        for path0 in j.sal.fs.listFilesInDir(systempath, recursive=False, filter="*.lua"):
            bname = j.sal.fs.getBaseName(path0)[:-4]
            C3 += "require('%s')\n" % bname
        C2 += C3

        j.sal.fs.writeFile(j.clients.tarantool.cfgdir + "/%s.lua" % self.name, C2)

    def start_connect(self):
        """
        will start a local tarantool in console
        """
        self.start()
        j.sal.process.executeInteractive("tarantoolctl enter %s" % self.name)

        # FOR TEST PURPOSES (DEBUG ON CONSOLE)
        # rm 000*;rm -rf /Users/kristofdespiegeleer1/opt/var/data/tarantool/test;tarantoolctl start test; cat /Users/kristofdespiegeleer1/opt/var/data/tarantool/test/instance.log

    def start(self):
        # j.builders.db.tarantool.start()
        self._setConfig()
        cpath = j.clients.tarantool.cfgdir + "/%s.lua" % self.name
        j.servers.tmux.execute("tarantool -i %s" % cpath, window="tarantool")

        j.sal.nettools.waitConnectionTest("localhost", self.port, 5)

        c = j.clients.tarantool.client_get(name=self.name)
        c.call("ping")

        # IF WE USE THE FOLLOWING THEN HAVE SECURITY ISSUES BECAUSE WILL RUN AS TARANTOOL
        # j.sal.fs.chown(self.path,"tarantool")
        # j.sal.process.execute("tarantoolctl stop %s"%self.name)
        # j.sal.process.execute("tarantoolctl start %s"%self.name)
        # j.sal.process.executeInteractive("tarantoolctl enter %s"%self.name)

    def connect_shell(self):
        """
        connect over tcp to the running tarantool
        """
        cmd = "tarantoolctl connect %s:%s@%s:%s" % (self.login, self.adminsecret, self.addr, self.port)
        j.sal.process.executeInteractive(cmd)
