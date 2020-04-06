# initialization
from Jumpscale import j


def simulation_calc(simulation, environment):

    # costs for environment
    # is the cost of 1 kwh
    environment.cost_power_kwh = "0.15 USD"
    # is the cost of 1U rackspace per month in USD
    environment.cost_rack_unit = "12 USD"

    # means at end of period we produce 40% more cpr (*1.4)
    # cpr = cloud production rate (is like hashrate of bitcoin mining box)
    simulation.cpr_improve_set("0:0,60:40")

    # price of a capacity unit goes down over time, here we say it will go down 40%
    # means we expect price to be lowered by X e.g. 40 (/1.4)
    simulation.cpr_sales_price_decline_set("0:0,60:40")

    # utilization of the nodes, starting with 0, after 20 months starting March 2020 we go to 80% utilization
    simulation.utilization_set("20:80,40:90")

    # super important factor, how does token price goes up
    # this is ofcourse complete speculation, no-one knows
    #     simulation.tokenprice_set_5years(3)

    ##if you want to do it more specific
    # 0:0 means month 0 we have value 0
    # 60:3 means month 60: value is 3
    # interpolation will happen between the values
    # so below will let the price go from 0.15 first month to 3 over 60 months
    # 119 is the last month we need to set (10 years from now, the relevant one is 5 years but simulator needs a further one
    # simulation.tokenprice_set("0:0.15,60:3,119:6")
    # simulation.tokenprice_set("0:0.15,12:0.3,60:3,119:6")

    # month:growth_percent of nodes being added
    # this means month 1 (is 0 in this file) we add 5 nodes, month 12 we add 1000 new nodes

    # simulation.nrnodes_new_set("0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000")
    # simulation.nrnodes_new_set("0:5,6:150,20:5000")

    # first batch of nodes added is 1500 nodes
    # each node is +-4.5k usd (check the bill of material sheet)
    # and we start the simulation with 800m tokens already farmed by the TF Farmers
    simulation.nodesbatch_start_set(
        environment=environment, nrnodes=1500, months_left=36, tft_farmed_before_simulation=700 * 1000 * 1000
    )

    return (simulation, environment)
