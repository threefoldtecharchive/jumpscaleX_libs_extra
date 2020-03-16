from Jumpscale import j

from params.params_bom_hardware_components import *

simulation = j.tools.tfgrid_simulator.default
environment = simulation.environment
environment.devices.clear()

environment.cost_power_kwh = "0.15 USD"
#is the cost of 1U rackspace per month in USD
environment.cost_rack_unit = "12 USD"
#what is the cost price for a mbit/s bandwidth (would be more expensive in emerging countries)
# 20USD is maybe a global avg 
environment.bandwidth_mbit = 20

# sales arguments
# these are enduser prices for people buying capacity
# following prices are very aggressive
# compute unit = 4 GB memory and 2 virtual CPU, in market price between 40 and USD120
environment.sales_price_cu = "8 USD"
# storage unit = 1 TB of netto usable storage, in market prices between 20 and USD120 
environment.sales_price_su = "5 USD"

# see the bill of material sheet to define the devices
# edge device is our std node (in this simulation about 4.5k USD investment per node)
device_edge = simulation.device_get("edge1", environment=environment)
# the switch added to the node
switch = simulation.device_get("switch", environment=environment)

# an environment to simulate the overhead per node (eg. 1 switch per node)
environment.device_node_add("edge1", device_edge, 20)
environment.device_overhead_add("switch", switch, 2)

#cpr = cloud production rate (like hashrate for bitcoin)

# means at end of period we produce 40% more cpr (*1.4)
# cpr = capacity production rate (is like hashrate of bitcoin)
simulation.cpr_improve_set("0:0,60:40")

# price of a capacity unit goes down over time, here we say it will go down 40%
# means we expect price to be lowered by X e.g. 40 (/1.4)
simulation.cpr_sales_price_decline_set("0:0,60:40")

# utilization of the nodes, starting with 0, after 20 months starting March 2020 we go to 80% utilization
simulation.utilization_set("20:80,40:90")
