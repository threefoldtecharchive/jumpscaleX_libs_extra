from Jumpscale import j
from lib import *
from params.params_environment import *

# choose your token simulation !!!
# from token_creators.token_creator_halving import TokenCreator  # like a bitcoin with halving, TFT price has no influence on farming

from token_creators.token_creator_classic import TokenCreator  # close to current rules but some important improvements

simulation = j.tools.tfgrid_simulator.default
simulation.token_creator = TokenCreator(simulation)

# super important factor, how does token price goes up, this is ofcourse complete speculation, no-one knows
simulation.tokenprice_set("0:0.15,60:2")

# month:growth_percent of nodes being added
simulation.nrnodes_new_set("0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000")
simulation.nodesbatch_start_set(nrnodes=1500, months_left=36, tft_farmed_before_simulation=700 * 1000 * 1000)


simulation.calc()
