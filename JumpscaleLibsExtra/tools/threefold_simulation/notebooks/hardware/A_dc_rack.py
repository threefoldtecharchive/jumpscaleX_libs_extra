from Jumpscale import j

#as used in gec farms as standard rack

def bom_calc(bom, environment):

    from hardware.components_hpe import bom_populate
    bom=bom_populate(bom)

    # see the bill of material sheet to define the devices
    compute = bom.device_get("hpe_compute_server", device_template_name="hpe_compute_server", environment=environment)
    storage = bom.device_get("hpe_storage_server", device_template_name="hpe_storage_server", environment=environment)
    switch = bom.device_get("switch_48", device_template_name="switch_48", environment=environment)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("compute", compute, 11)
    environment.device_node_add("storage", storage, 5)
    environment.device_overhead_add("switch", switch, 2)

    return bom, environment

