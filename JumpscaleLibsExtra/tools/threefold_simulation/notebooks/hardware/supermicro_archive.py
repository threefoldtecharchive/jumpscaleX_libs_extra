from Jumpscale import j


def bom_calc(bom, environment):
    
    from hardware.bom_supermicro import bom_populate
    bom=bom_populate(bom)

    # see the bill of material sheet to define the devices
    server = bom.device_get("storage_server", device_template_name="storage_server", environment=environment)
    # the switch added to the node
    switch = bom.device_get("switch_48", device_template_name="switch_48", environment=environment)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("server", server, 20)
    environment.device_overhead_add("switch", switch, 2)

    return bom, environment
