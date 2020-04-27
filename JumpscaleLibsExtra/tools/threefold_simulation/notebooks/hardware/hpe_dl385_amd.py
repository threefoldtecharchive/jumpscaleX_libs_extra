from Jumpscale import j

# as used in dl385 farms 
# Note: you can change the amount of severs to fit your environment

def bom_calc(environment):

    from hardware.components.components_hpe import bom_populate

    environment.bom = bom_populate(environment.bom)
    # see the bill of material sheet in components_hpe to define the devices
    # make sure to set the prices of the compoments according to your offer
    
    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("compute", template="hpe_compute_server", nr=1)
    environment.device_overhead_add("switch", template="switch_48", nr=1)
