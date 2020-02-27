from Jumpscale import j

simulation = j.tools.tfgrid_simulator.default
environment = simulation.environment
environment.devices.clear()

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
