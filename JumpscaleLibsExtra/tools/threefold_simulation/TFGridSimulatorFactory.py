from Jumpscale import j

from .TFGridSimulator import TFGridSimulator


class TFGridSimulatorFactory(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tools.tfgrid_simulator"

    def _init(self):
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
        j.shell()

        simulation_run = simulation.run()

        # month:growth_percent of nodes being added
        simulation_run.growth_percent_set("3:5,11:8,24:10,36:12,48:10,60:10")

        # means at end of period we produce 40% more cpr (*1.4)
        # cpr = capacity production rate (is like hashrate of bitcoin)
        simulation_run.cpr_improve_set("71:40")

        # price of a capacity unit goes down over time, here we say it will go down 40%
        # means we expect price to be lowered by X e.g. 40 (*0.6)
        simulation_run.cpr_sales_price_decline_set("0:0,71:40")

        # utilization of the nodes, strating with 0
        simulation_run.utilization_set("30:80,71:90")

        # super important factor, how does token price goes up, this is ofcourse complete speculation, no-one knows
        simulation_run.tokenprice_set("0:0.15,71:2")

        # simulation_run.difficulty_level_set("0:2,71:50")
        simulation_run.difficulty_level_set("0:2,71:2")

        # do the calculation of the simulation
        simulation_run.calc(
            nr_start_nodes=1500,
            months_remaining_start_nodes=36,
            environment=environment,
            tft_farmed_before_simulation=20 * 1000 * 1000,
        )

        print(simulation_run)

        return environment

    def start(self, voila=False, background=False):
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
        )  # it will open a browser with access to the right output
