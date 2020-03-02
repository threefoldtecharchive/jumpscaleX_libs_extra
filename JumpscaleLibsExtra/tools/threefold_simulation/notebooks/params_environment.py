from Jumpscale import j

simulation = j.tools.tfgrid_simulator.default
environment = simulation.environment
environment.devices.clear()

environment.cost_power_kwh = "0.15 USD"
environment.cost_rack_unit = "12 USD"
environment.bandwidth_mbit = 20

# sales arguments
environment.sales_price_cu = "6 USD"
environment.sales_price_su = "4 USD"

device_edge = simulation.device_get("edge1")
# print(d1)

switch = simulation.device_get("switch")

environment.device_add("edge1", device_edge, 20)
environment.device_add("switch", switch, 2)

# means at end of period we produce 40% more cpr (*1.4)
# cpr = capacity production rate (is like hashrate of bitcoin)
simulation.cpr_improve_set("0:0,60:40")

# price of a capacity unit goes down over time, here we say it will go down 40%
# means we expect price to be lowered by X e.g. 40 (*0.6)
simulation.cpr_sales_price_decline_set("0:0,60:40")

# utilization of the nodes, strating with 0
simulation.utilization_set("20:80,40:90")
