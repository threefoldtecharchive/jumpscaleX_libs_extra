from Jumpscale import j
from lib import *
from params.params_environment import *

# choose your token simulation !!!


## like a bitcoin with halving, TFT price has no influence on farming
# from token_creators.token_creator_halving import TokenCreator

## close to current rules but some important improvements
# from token_creators.token_creator_classic_predefined_difficultylevel import TokenCreator
from token_creators.token_creator_classic_2billionTFT import TokenCreator

simulation = j.tools.tfgrid_simulator.default
simulation.token_creator = TokenCreator(simulation)

# super important factor, how does token price goes up
# this is ofcourse complete speculation, no-one knows
# 0:0 means month 0 we have value 0
# 60:3 means month 60: value is 3
# interpolation will happen between the values
# so below will let the price go from 0.15 first month to 3 over 60 months
simulation.tokenprice_set("0:0.15,119:6")  #means after 60 months the price will be +-3

# month:growth_percent of nodes being added
# this means month 1 (is 0 in this file) we add 5 nodes, month 12 we add 1000 new nodes
simulation.nrnodes_new_set("0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000")
# simulation.nrnodes_new_set("0:5,6:150,20:5000")

#first batch of nodes added is 1500 nodes
#each node is +-4.5k usd (check the bill of material sheet)
#and we start the simulation with 800m tokens already farmed by the TF Farmers
simulation.nodesbatch_start_set(nrnodes=1500, months_left=36, tft_farmed_before_simulation=800 * 1000 * 1000)

#month we start simulation for for the farming calculator (shows a specific simulation for a batch)
farming_startmonth = 10

simulation.calc()
