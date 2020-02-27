from Jumpscale import j

from .TFGridSimulator import TFGridSimulator


class TFGridSimulatorFactory(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tools.tfgrid_simulator"

    def _init(self, **kwargs):
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

    def calc(self):
        """
        kosmos 'j.tools.tfgrid_simulator.calc()'
        :return:
        """
        simulation = j.tools.tfgrid_simulator.default

        from .notebooks.params_bom_hardware_components import bom
        from .notebooks.params_environment import environment
        from .notebooks.token_creator import tft_burn, tft_cultivate, tft_farm, difficulty_level_get

        simulation.token_creator.tft_burn = tft_burn
        simulation.token_creator.tft_cultivate = tft_cultivate
        simulation.token_creator.tft_farm = tft_farm
        simulation.token_creator.difficulty_level_get = difficulty_level_get

        environment = simulation.environment

        # nb = simulation.nodesbatch_calc(10, 10)

        simulation.nodesbatch_start_set(nrnodes=1500, months_left=36, tft_farmed_before_simulation=20 * 1000 * 1000)

        # do the calculation of the simulation
        simulation.calc(nrnodes_new="0:5,6:150,12:1000,13:0")
        # nodes sold are the first sales nr's, after that the growth numbers above will count

        return environment

    def start(self, voila=False, background=False, base_url=None, name="tftest", reset=False):
        """
        to run:

        kosmos -p 'j.tools.tfgrid_simulator.start()'

        #means we run the notebook in the code env (careful)
        kosmos -p 'j.tools.tfgrid_simulator.start(name=None)'
        """

        j.application.start("tfsimulation")

        j.core.myenv.log_includes = []
        # e = self.calc()

        path_source = "{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks"
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
