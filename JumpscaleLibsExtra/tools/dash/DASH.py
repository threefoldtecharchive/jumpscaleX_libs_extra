from Jumpscale import j


JSBASE = j.baseclasses.object


class DASH(j.baseclasses.object):
    """
    """

    __jslocation__ = "j.tools.dash"

    def _init(self):
        self._default = None

    def install(self):
        """
        kosmos 'j.tools.dash.install()'
        :return:
        """
        p = j.tools.prefab.local
        if p.platformtype.platform_is_osx:
            # self._log_info("will install mactex, is huge, will have to wait long")
            # cmd="brew cask install mactex"
            # p.core.run(cmd)
            pass
        else:
            pass

        p.runtimes.pip.install("dash,dash-html-components,dash-core-components,dash-table,sd_material_ui")
        cmd = "pip3 install git+https://github.com/rmarren1/dash-ui.git"

    def start(self, path, background=False):
        """

        :param path: to file of dash
        :param background:
        :return:
        """
        j.shell()

    def run_example(self, name="graph1"):
        """
        kosmos 'j.tools.dash.run_example(name="graph1")'
        :param name:
        :return:
        """
        self._example_run("tutorials/%s" % name, obj_key="main")
