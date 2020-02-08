from Jumpscale import j
from .SimulatorLib import Simulation


class BaseClasses_Object_Structure_2(j.baseclasses.testtools, j.baseclasses.object):

    __jslocation__ = "j.tools.tfsimulation"

    def simulation(self):
        """
        c=j.tools.tfsimulation.test()
        :return:
        """

    def calc(self):
        """
        c=j.tools.tfsimulation.test()
        :return:
        """

        from .SimulationComponents import simulation

        environment = simulation.environment_get("main")
        environment.cost_power_kwh = "0.15 USD"
        environment.cost_rack_unit = "12 USD"
        environment.bandwidth_mbit = 20

        # sales arguments
        environment.sales_price_cu = "10 USD"
        environment.sales_price_su = "6 USD"

        d1 = simulation.device_get("edge1", environment=environment)
        print(d1)
        switch = simulation.device_get("switch", environment=environment)

        environment.device_add("edge1", d1, 20)
        environment.device_add("switch", switch, 2)

        print(environment)

        simulation = Simulation()

        # month:growth_percent of nodes being added
        simulation.growth_percent_set("3:5,11:8,24:10,36:12,48:10,60:10")

        # means at end of period we produce 40% more cpr (*1.4)
        # cpr = capacity production rate (is like hashrate of bitcoin)
        simulation.cpr_improve_set("71:40")

        # price of a capacity unit goes down over time, here we say it will go down 40%
        # means we expect price to be lowered by X e.g. 40 (*0.6)
        simulation.cpr_sales_price_decline_set("0:100,71:40")

        # utilization of the nodes, strating with 0
        simulation.utilization_set("30:80,71:90")

        # super important factor, how does token price goes up, this is ofcourse complete speculation, no-one knows
        simulation.tokenprice_set("0:0.15:71:2")

        # are the parameters for a batch of nodes to be added
        nb = simulation.nodes_batch_template_get(environment)
        print(nb)

        # do the calculation of the simulation
        simulation.calc(nr_start_nodes=1500, months_remaining_start_nodes=36, nodes_batch_template=nb)

        j.shell()

        return environment

    def test(self):
        """
        to run:

        kosmos -p 'j.tools.tfsimulation.test()'
        """

        j.application.start("tfsimulation")

        j.core.myenv.log_includes = []
        e = self.calc()
