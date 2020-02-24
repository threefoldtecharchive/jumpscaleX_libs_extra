from Jumpscale import j

from .TFGridSimulator import TFGridSimulator


class TFGridSimulatorFactory(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tools.tfgrid_simulator"

    def _init(self, **kwargs):
        self._instances = {}

    @property
    def default(self):
        return self.simulator_get("default")

    def simulator_get(self, name="default"):
        """
        example how to use

        ```
        simulation = j.tools.tfgrid_simulator.simulator_get()
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

        simulation = self.default

        # populate the bom (bill of material)
        from .SimulationComponents import bom_fill

        bom_fill(simulation)

        environment = simulation.environment

        environment.cost_power_kwh = "0.15 USD"
        environment.cost_rack_unit = "12 USD"
        environment.bandwidth_mbit = 20

        # sales arguments
        environment.sales_price_cu = "10 USD"
        environment.sales_price_su = "6 USD"

        device_edge = simulation.device_get("edge1")
        # print(d1)

        switch = simulation.device_get("switch")

        environment.device_add("edge1", device_edge, 20)
        environment.device_add("switch", switch, 2)

        print(environment)

        # month:growth_percent of nodes being added
        simulation.growth_percent_set("3:5,11:8,24:10,36:12,48:10,60:10,61:0")

        # means at end of period we produce 40% more cpr (*1.4)
        # cpr = capacity production rate (is like hashrate of bitcoin)
        simulation.cpr_improve_set("71:40")

        # price of a capacity unit goes down over time, here we say it will go down 40%
        # means we expect price to be lowered by X e.g. 40 (*0.6)
        simulation.cpr_sales_price_decline_set("0:0,71:40")

        # utilization of the nodes, strating with 0
        simulation.utilization_set("20:80,40:90")

        # super important factor, how does token price goes up, this is ofcourse complete speculation, no-one knows
        simulation.tokenprice_set("0:0.15,71:2")

        # simulation.difficulty_level_set("0:2,71:50")
        simulation.difficulty_level_set("0:2,71:2")

        simulation.nodesbatch_start_set(nrnodes=10, months_left=36, tft_farmed_before_simulation=20 * 1000 * 1000)

        # do the calculation of the simulation
        simulation.calc(nrnodes_new="0:5,6:150,12:1000,13:0")
        # nodes sold are the first sales nr's, after that the growth numbers above will count

        print(simulation)

        return environment

    def start(self, voila=False, background=False, base_url=None):
        """
        to run:

        kosmos -p 'j.tools.tfgrid_simulator.start()'
        """

        j.application.start("tfsimulation")

        j.core.myenv.log_includes = []
        # e = self.calc()

        j.servers.notebook.start(
            path="{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks",
            voila=voila,
            background=background,
            base_url=base_url,
        )  # it will open a browser with access to the right output
