from Jumpscale import j

from .DocSite import DocSite


class DocsFactory(j.baseclasses.object_config_collection_testtools):

    __jslocation__ = "j.data.docs"

    _CHILDCLASS = DocSite

    def _init(self, **kwargs):

        self._bcdb = j.data.bcdb.get("docs")  # will be a BCDB custom for this one using sqlite
        self._macros_modules = {}
        self._macros = {}

    def macros_load(self, pathOrUrl="https://github.com/threefoldtech/jumpscale_weblibs/tree/master/macros"):
        """
        @param pathOrUrl can be existing path or url
        e.g. https://github.com/threefoldtech/jumpscale_lib/docsite/tree/master/examples
        """
        self._log_info("load macros:%s" % pathOrUrl)
        path = j.clients.git.getContentPathFromURLorPath(pathOrUrl)

        if path not in self._macros_modules:

            if not j.sal.fs.exists(path=path):
                raise j.exceptions.Input("Cannot find path:'%s' for macro's, does it exist?" % path)

            for path0 in j.sal.fs.listFilesInDir(path, recursive=True, filter="*.py", followSymlinks=True):
                name = j.sal.fs.getBaseName(path0)[:-3]  # find name, remove .py
                self._macros[name] = j.tools.jinja2.code_python_render(
                    obj_key=name, path=path0, reload=False, objForHash=name
                )

    def test(self):
        """
        kosmos 'j.data.docs.test()'
        :return:
        """

        self.macros_load()

        ds = self.get(name="test")

        ds.git_url = "https://github.com/threefoldfoundation/info_foundation/tree/development/docs"
        # ds.update() #will update from github, will automatically pull if needed

        ds.push_to_redis()  # will make sure the docs are in redis

        # doc = ds.get_doc(name="page1")
        # doc = ds.get_file(name="page1")

        j.shell()
