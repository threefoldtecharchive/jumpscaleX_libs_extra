from Jumpscale import j

from .TFGridSimulator import TFGridSimulator


class TFGridSimulatorFactory(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tools.tfgrid_simulator"

    def _init(self, **kwargs):
        j.application.start("simulator")
        self._instances = {}

    @property
    def default(self):
        s = self.simulation_get("default")
        return s

    def simulation_get(self, name="default"):
        """
        example how to use

        ```
        simulation = j.tools.tfgrid_simulator.simulation_get()
        ```

        """
        if name not in self._instances:
            self._instances[name] = TFGridSimulator(name=name)
        return self._instances[name]

    def calc(self, batches_simulation=True):
        """
        kosmos 'j.tools.tfgrid_simulator.calc()'
        :return:
        """

        simulation = j.tools.tfgrid_simulator.default

        from .notebooks.params_bom_hardware_components import bom
        from .notebooks.params_environment import environment

        # from .notebooks.token_creator_new import TokenCreator
        from .notebooks.token_creator_modest import TokenCreator

        simulation.token_creator = TokenCreator(simulation)
        environment = simulation.environment

        # month:growth_percent of nodes being added
        simulation.nrnodes_new_set("0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000")
        simulation.nodesbatch_start_set(nrnodes=1500, months_left=36, tft_farmed_before_simulation=700 * 1000 * 1000)

        # do the calculation of the simulation
        simulation.calc()

        if batches_simulation:
            # nrnodes is 2nd
            nb0 = simulation.nodesbatch_get(0)
            nb0.graph_tft(cumul=True)
            nb0.graph_usd(cumul=True)
            nb = simulation.nodesbatch_get(20)
            nb.graph_tft(single=True)
            # nb.graph_usd(cumul=True,single=True)
            for month in [1, 10, 30, 50]:
                simulation.nodesbatch_get(month).graph_usd(cumul=True, single=True)

        simulation.graph_nodesbatches_usd_simulation()
        simulation.graph_tft_simulation()

        return environment

    def start(self, voila=False, background=False, base_url=None, name=None, reset=False):
        """
        to run:

        kosmos -p 'j.tools.tfgrid_simulator.start()'

        #means we run the notebook in the code env (careful)
        kosmos -p 'j.tools.tfgrid_simulator.start(name=None)'
        """

        j.application.start("tfsimulation")

        j.core.myenv.log_includes = []
        # e = self.calc()

        path_source = "{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks/nodebatch_simulator.ipynb"
        path_source = j.core.tools.text_replace(path_source)
        if name:
            path_dest = j.core.tools.text_replace("{DIR_VAR}/notebooks/%s" % name)
            if reset:
                j.core.tools.remove(path_dest)
            j.sal.fs.copyDirTree(path_source, path_dest, overwriteFiles=False)
        else:
            path_dest = path_source

        self._log_info("start notebook on:%s" % path_dest)

        j.servers.notebook.start(
            path=path_dest, voila=voila, background=background, base_url=base_url,
        )  # it will open a browser with access to the right output
