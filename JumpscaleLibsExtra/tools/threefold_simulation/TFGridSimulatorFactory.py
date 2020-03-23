from Jumpscale import j

from .TFGridSimulator import TFGridSimulator
from .BillOfMaterial import Environment, BillOfMaterial
import sys


class TFGridSimulatorFactory(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tools.tfgrid_simulator"

    def _init(self, **kwargs):
        j.application.start("simulator")
        self._instances = j.baseclasses.dict()
        self._environments = j.baseclasses.dict()
        self._bom = j.baseclasses.dict()

        notebookpath = j.core.tools.text_replace(
            "{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks"
        )
        if notebookpath not in sys.path:
            sys.path.append(notebookpath)

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

    def environment_get(self, name="default"):
        """
        example how to use

        ```
        simulation = j.tools.tfgrid_simulator.environment_get()
        ```

        """
        if name not in self._environments:
            self._environments[name] = Environment(name=name)
        return self._environments[name]

    def bom_get(self, name="default"):
        """
        example how to use

        ```
        simulation = j.tools.tfgrid_simulator.environment_get()
        ```

        """
        if name not in self._bom:
            self._bom[name] = BillOfMaterial(name=name)
        return self._bom[name]

    def calc(self, batches_simulation=False):
        """
        kosmos 'j.tools.tfgrid_simulator.calc()'
        :return:
        """

        from params.default import simulation

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

        # simulation.graph_tft_simulation()

        simulation.graph_nodesbatches_usd_simulation()

        print(simulation.markdown_reality_check(10))

        return

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

        path_source = "{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks/home.ipynb"
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
        j.application.reset_context()
