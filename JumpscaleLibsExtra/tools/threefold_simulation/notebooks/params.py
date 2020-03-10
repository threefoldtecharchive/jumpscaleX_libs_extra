from lib import *
import bqplot.pyplot as plt
from params_bom_hardware_components import *
from params_environment import *

# choose your token simulation !!!
from token_creator_modest import TokenCreator

simulation = j.tools.tfgrid_simulator.default
simulation.token_creator = TokenCreator(simulation)

# month:growth_percent of nodes being added
simulation.nrnodes_new_set("0:5,6:150,12:1000,18:2000,24:8000,36:12000,48:20000,60:20000")
simulation.nodesbatch_start_set(nrnodes=1500, months_left=36, tft_farmed_before_simulation=700 * 1000 * 1000)


simulation.calc()
