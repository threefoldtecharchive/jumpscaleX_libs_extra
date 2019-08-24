from Jumpscale import j
from .Doc import Doc
from .File import File
from .Navigation import Navigation


class DocSite(j.application.JSFactoryConfigsBaseClass, j.baseclasses.object_config):

    _SCHEMATEXT = """
        @url = jumpscale.docs.docsite.1
        name* = ""
        path = ""
        git_url = ""
        description = ""
        last_process_data = (D)
        """

    def __init__(self, factory=None, dataobj=None, childclass_name=None):
        j.baseclasses.object_config.__init__(self, factory=factory, dataobj=dataobj, childclass_name=childclass_name)
        j.application.JSFactoryConfigsBaseClass.__init__(self)

    def _childclass_selector(self, childclass_name="doc", **kwargs):
        """
        childclass name is file or doc
        :return:
        """
        if childclass_name == "doc":
            return Doc
        elif childclass_name == "file":
            return File
        elif childclass_name == "navigation":
            return Navigation
        else:
            raise j.exceptions.Base("did not find childclass type:%s" % childclass_name)

    def _init(self, **kwargs):
        self._git = None
        self._loaded = False

    @property
    def _error_file_path(self):
        if self.path is None or self.path is "":
            raise j.exceptions.Base("path should not be empty")
        return self.path + "/errors.md"

    def get_doc(self, name=None, id=None, die=True, create_new=False, **kwargs):
        name = j.core.text.strip_to_ascii_dense(name)
        self._check()
        return self.get(name=name, id=id, die=die, create_new=create_new, childclass_name="doc", docsite=self, **kwargs)

    def get_file(self, name=None, id=None, die=True, create_new=False, **kwargs):
        name = j.core.text.strip_to_ascii_dense(name)
        self._check()
        return self.get(
            name=name, id=id, die=die, create_new=create_new, childclass_name="file", docsite=self, **kwargs
        )

    def get_navigation(self, name=None, id=None, die=True, create_new=False, **kwargs):
        name = j.core.text.strip_to_ascii_dense(name)
        self._check()
        return self.get(
            name=name, id=id, die=die, create_new=create_new, childclass_name="navigation", docsite=self, **kwargs
        )

    @property
    def git(self):
        if self._git is None:
            if self.git_url != "":
                gitpath = self.git_url
            else:
                gitpath = j.clients.git.findGitPath(self.path, die=False)
                if not gitpath:
                    return
            self._git = j.clients.git.get(gitpath)
        return self._git

    def _check(self):
        if not self._loaded:
            if not self.data.path:
                if not self.data.git_url:
                    raise j.exceptions.Base("url not specified for %s" % self.name)
                self.data.path = j.clients.git.getContentPathFromURLorPath(
                    self.data.git_url, pull=False
                )  # just to make sure data there
                # if not j.sal.fs.exists(self.path):
                #     self.update_from_git()
            self._load()

    def push_to_redis(self):
        self._check()
        j.shell()

    def update(self):
        """
        will check the docs from git & get them local
        if the repo already exists will try to pull the changes in
        :return:
        """
        self.data.path = j.clients.git.getContentPathFromURLorPath(self.data.git_url, pull=True)

    def _load(self, reset=False):
        """
        load all the files/docs inside a directory
        the result will be stored in the BCDB which is attached to the DocsFactory (j.data.docs._bcdb)
        """
        if reset == False and self._loaded:
            return
        self._loaded = True
        self._files = {}
        self._docs = {}
        self._sidebars = {}

        j.sal.fs.remove(self.path + "errors.md")
        path = self.path
        if not j.sal.fs.exists(path=path):
            raise j.exceptions.NotFound("Cannot find source path in load:'%s'" % path)

        def callbackForMatchDir(path, arg):
            base = j.sal.fs.getBaseName(path).lower()
            if base.startswith("."):
                return False
            if base.startswith("_"):
                return False
            return True

        def callbackForMatchFile(path, arg):
            base = j.sal.fs.getBaseName(path).lower()
            if base == "_sidebar.md":
                return True
            if base.startswith("_"):
                return False
            ext = j.sal.fs.getFileExtension(path)
            if ext == "md" and base[:-3] in ["summary", "default"]:
                return False
            return True

        def callbackFunctionDir(path, arg):
            # will see if ther eis data.toml or data.yaml & load in data structure in this obj
            # self._processData(path + "/data")
            dpath = path + "/default.md"
            if j.sal.fs.exists(dpath, followlinks=True):
                C = j.sal.fs.readFile(dpath)
                rdirpath = j.sal.fs.pathRemoveDirPart(path, self.path)
                rdirpath = rdirpath.strip("/").strip().strip("/")
                self._content_default[rdirpath] = C
            return True

        def callbackFunctionFile(path, arg):
            self._log_debug("file:%s" % path)
            ext = j.sal.fs.getFileExtension(path).lower()
            base = j.sal.fs.getBaseName(path)
            if ext == "md":
                self._log_debug("found md:%s" % path)
                name = base[:-3].lower()  # remove extension
                doc = self.get_doc(name=name, path=path, create_new=True)
                j.shell()
                w
                # if base not in self.docs:
                #     self.docs[base.lower()] = doc
                self._docs[doc.name_dot_lower] = doc
            elif ext in ["html", "htm"]:
                self._log_debug("found html:%s" % path)
                # raise j.exceptions.Base()
                # l = len(ext)+1
                # base = base[:-l]  # remove extension
                # doc = HtmlPage(path, base, docsite=self)
                # # if base not in self.htmlpages:
                # #     self.htmlpages[base.lower()] = doc
                # self.htmlpages[doc.name_dot_lower] = doc
            else:

                if ext in [
                    "png",
                    "jpg",
                    "jpeg",
                    "pdf",
                    "docx",
                    "doc",
                    "xlsx",
                    "xls",
                    "ppt",
                    "pptx",
                    "mp4",
                    "css",
                    "js",
                    "mov",
                ]:
                    self._log_debug("found file:%s" % path)
                    base = self._clean(base)
                    if base in self._files:
                        raise j.exceptions.Input(message="duplication file in %s,%s" % (self, path))
                    self._files[base] = path
                # else:
                #     self._log_debug("found other:%s"%path)
                #     l = len(ext)+1
                #     base = base[:-l]  # remove extension
                #     doc = DocBase(path, base, docsite=self)
                #     if base not in self.others:
                #         self.others[base.lower()] = doc
                #     self.others[doc.name_dot_lower] = doc

        callbackFunctionDir(self.path, "")  # to make sure we use first data.yaml in root

        j.sal.fswalker.walkFunctional(
            self.path,
            callbackFunctionFile=callbackFunctionFile,
            callbackFunctionDir=callbackFunctionDir,
            arg="",
            callbackForMatchDir=callbackForMatchDir,
            callbackForMatchFile=callbackForMatchFile,
        )

        self._loaded = True

    def _error_raise(self, errormsg, doc=None):
        if doc is not None:
            errormsg2 = "## ERROR: %s\n\n- in doc: %s\n\n%s\n\n\n" % (doc.name, doc, errormsg)
            key = j.data.hash.md5_string("%s_%s" % (doc.name, errormsg))
            if not key in self._errors:
                errormsg3 = "```\n%s\n```\n" % errormsg2
                j.sal.fs.writeFile(filename=self._error_file_path, contents=errormsg3, append=True)
                self._log_error(errormsg2)
                doc.errors.append(errormsg)
        else:
            self._log_error("DEBUG NOW raise error")
            raise j.exceptions.Base("stop debug here")

    @property
    def errors(self):
        """
        return current found errors
        """
        errors = "DID NOT FIND ERRORSFILE, RUN js_doc verify in the doc directory"
        if j.sal.fs.exists(self._error_file_path):
            errors = j.sal.fs.readFile(self.error_file_path)
        return errors

    def __repr__(self):
        return "docsite:%s" % (self.path)

    __str__ = __repr__
