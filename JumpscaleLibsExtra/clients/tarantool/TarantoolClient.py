from Jumpscale import j
import tarantool
import os
import sys
from .TarantoolQueue import TarantoolQueue

JSBASE = j.baseclasses.object_config


class Models:
    pass


class TarantoolClient(JSBASE):
    _SCHEMATEXT = """
    @url = jumpscale.tarantool.clients
    name** ="" (S)
    ip = "localhost" (S)
    port = 3301 (ipport)
    login = "root" (S)
    password_ = "" (S)
    """

    def _init(self, **kwargs):

        ip = self.ip
        port = self.port
        login = self.login
        password = self.password_

        self.db = tarantool.connect(ip, user=login, port=port, password=password)
        self.call = self.db.call
        self.models = Models()

    @property
    def _path(self):
        return j.sal.fs.getDirName(os.path.abspath(__file__))

    def getQueue(self, name, ttl=0, delay=0):
        return TarantoolQueue(self, name, ttl=ttl, delay=delay)

    def eval(self, code):
        code = j.core.text.strip(code)
        self.db.eval(code)

    def userGrant(self, user="guest", operation=1, objtype="universe", objname=""):
        """
        @param objtype the type of object - "space" or "function" or "universe",
        @param objname the name of object only relevant for space or function
        @param opstype in integer the type of operation - "read" = 1, or "write" = 2, or "execute" = 4, or a combination such as "read,write,execute".
        """
        if objname == "":
            C = "box.schema.user.grant('%s',%s,'%s')" % (user, operation, objtype)
        else:
            C = "box.schema.user.grant('%s',%s,'%s','%s')" % (user, operation, objtype, objname)

        self.db.eval(C)

    def addFunction(self, code=""):
        """
        example:
            function echo3(name)
              return name
            end

        then use with self.call...
        """
        self.eval(code)

    @property
    def _template_dir(self):
        return j.sal.fs.joinPaths(j.sal.fs.getParent(__file__), "templates")

    def _pyModelFix(self, path, name, dbtype, login, passwd):
        """
        This will generate the python models.
        some template file are required to be present in the template/python folder
        """

        lcontent = ""

        template_path = j.sal.fs.joinPaths(self._template_dir, "python", "model.py.template")
        template = j.sal.fs.readFile(template_path)
        lcontent += j.core.text.strip(template)

        # TODO: use real templating engine (puppet) ?
        lcontent = lcontent.replace("$dbtype", dbtype)
        lcontent = lcontent.replace("$name", name)
        name_upper = name[0].upper() + name[1:]
        lcontent = lcontent.replace("$Name", name_upper)
        lcontent = lcontent.replace("mymodelname", name)
        lcontent = lcontent.replace("$login", login)
        lcontent = lcontent.replace("$passwd", passwd)

        if not j.sal.fs.exists(path):
            j.sal.fs.writeFile(path, lcontent)
        path = path[:-3]
        path += "_template.py"
        j.sal.fs.writeFile(path, lcontent)

    def _luaModelFix(self, path, name, dbtype, login, passwd):
        """
        This will generate the lua models.
        some template file are required to be present in the template/lua folder
        """
        # The matching works like this: if you want to generate  method called
        # `set` then you need to have a template called model_set.lua in the template/lua folder
        # this method will walk over all the files match this model and add the lua stored procedure to tarantool

        lcontent = j.sal.fs.readFile(path)
        name_upper = name[0].upper() + name[1:]
        function_names = []
        for template_path in j.sal.fs.listFilesInDir(self._template_dir + "/lua", filter="model_*.lua"):
            # strip model_ and .lua out of the template path
            method = j.sal.fs.getBaseName(template_path)[len("model_") : -4]
            function_names.append(method)
            template_name = "model_{}.lua".format(method)

            if lcontent.find("local function {}".format(method)) == -1:
                template_path = j.sal.fs.joinPaths(self._template_dir, "lua", template_name)
                template = j.sal.fs.readFile(template_path)
                lcontent += "\n\n" + j.core.text.strip(template)

        lcontent = lcontent.replace("$dbtype", dbtype)
        lcontent = lcontent.replace("$name", name)
        lcontent = lcontent.replace("$Name", name_upper)
        lcontent = lcontent.replace("mymodelname", name)
        lcontent = lcontent.replace("$login", login)
        lcontent = lcontent.replace("$passwd", passwd)

        # FIXME: this is ugly
        if lcontent.find("return %s" % name) == -1:
            lcontent += "\n%s = {\n" % name
            for function_name in function_names:
                lcontent += "\t%s = %s,\n" % (function_name, function_name)
            lcontent += "}\n"
            lcontent += "return %s" % name

        j.sal.fs.writeFile(path, lcontent)

    def addModels(self, path="", login="user", passwd="secret", dbtype="memtx"):
        """
        @PARAM path is the directory where the capnp, lua, ... can be found, each subdir has a model name
               if not specified will look for models underneith the capnp extension
        @PARAM dbtype vinyl or memtx

        will be available in tarantool as require("model_capnp_$name")  $name of the model which is the directory name
        and the lua model as "model_$name" which has the required stored procedures set, get, delete, find...
        """

        if path == "":
            path = "%s/models" % self._path

        if path not in sys.path:
            sys.path.append(path)

        for name in j.sal.fs.listDirsInDir(path, False, True):
            if name == "__pycache__":
                continue
            name_upper = name[0].upper() + name[1:]
            cpath = j.sal.fs.joinPaths(path, name, "model.capnp")
            lpath = j.sal.fs.joinPaths(path, name, "model.lua")
            ppath = j.sal.fs.joinPaths(path, name, "%sCollection.py" % name_upper)
            j.sal.fs.touch(j.sal.fs.joinPaths(path, name, "__init__.py"))
            if j.sal.fs.exists(cpath):
                res = j.data.capnp.schema_generate_lua(cpath)
                self.addScript(res, "model_capnp_%s" % name)
                j.sal.fs.remove(res)

            if not j.sal.fs.exists(lpath):
                template_path = j.sal.fs.joinPaths(self._template_dir, "lua", "space_create.lua")
                template = j.sal.fs.readFile(template_path)
                j.sal.fs.writeFile(lpath, j.core.text.strip(template))

            self._luaModelFix(path=lpath, name=name, dbtype=dbtype, login=login, passwd=passwd)
            self._pyModelFix(path=ppath, name=name, dbtype=dbtype, login=login, passwd=passwd)

            self.addScript(lpath, "model_%s" % name)

            cmd = "from $name import $NameCollection"
            cmd = cmd.replace("$name", name)
            cmd = cmd.replace("$Name", name_upper)
            exec(cmd)
            exec("self.models.$NameCollection=$NameCollection.$NameCollection".replace("$Name", name_upper))
            exec("self.models.$NameModel=$NameCollection.$NameModel".replace("$Name", name_upper))

    def addScripts(self, path=None, require=False):
        """
        load all lua scripts in path (sorted) & execute in the tarantool instance

        if @path empty then path = testscripts subdir of this extension
        """
        if path == None:
            path = "%s/testscripts" % self._path
        for path0 in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.lua"):
            self.addScript(path0, require=require)

    def reloadSystemScripts(self):
        systempath = "%s/systemscripts" % self._path
        for path0 in j.sal.fs.listFilesInDir(systempath, recursive=False, filter="*.lua"):
            name = j.sal.fs.getBaseName(path0)[:-4]
            self.eval("package.loaded['%s']=nil" % name)
            self.eval("require ('%s')" % name)

    def addScript(self, path, name="", require=True):
        self._log_debug("addscript %s %s" % (path, name))
        C = j.sal.fs.readFile(path)
        if name == "":
            name = j.sal.fs.getBaseName(path)[:-4]
        # write the lua script to the location on server
        self.db.call("add_lua_script", (name, C))
        if require:
            self.eval("package.loaded['%s']=nil" % name)
            self.eval("require ('%s')" % name)
            cmd = "%s=require('%s')" % (name, name)
            self._log_debug(cmd)
            self.eval(cmd)
