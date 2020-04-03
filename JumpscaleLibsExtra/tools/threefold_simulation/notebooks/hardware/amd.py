from Jumpscale import j


def bom_calc(environment):

    from hardware.components.components_amd import bom_populate

    environment.bom = bom_populate(environment.bom)

    # see the bill of material sheet to define the devices
    server = environment.bom.device_get("server")
    # the switch added to the node
    switch = environment.bom.device_get("switch")

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("compute", server, 20)
    environment.device_overhead_add("switch", switch, 2)
