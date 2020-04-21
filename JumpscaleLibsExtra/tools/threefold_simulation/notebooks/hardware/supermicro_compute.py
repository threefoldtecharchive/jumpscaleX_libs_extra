from Jumpscale import j

# as used in bancadati farm, compute frontend to archive


def bom_calc(environment):

    from hardware.components.components_supermicro import bom_populate

    environment.bom = bom_populate(environment.bom)

    # see the bill of material sheet to define the devices
    # we get a device starting from a template
    server = environment.bom.device_get("archive_compute_frontend", environment=environment)
    # the switch added to the node
    switch = environment.bom.device_get("switch_48", environment=environment)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("compute", server, 20)
    environment.device_overhead_add("switch", switch, 2)

    server.calc(bom=bom)
