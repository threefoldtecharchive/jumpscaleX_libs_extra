from Jumpscale import j

#as used in bancadati farm, compute frontend to archive

def bom_calc(bom, environment):

    from hardware.components_supermicro import bom_populate
    bom=bom_populate(bom)

    # see the bill of material sheet to define the devices
    # we get a device starting from a template
    server = bom.device_get("archive_compute_frontend", device_template_name="archive_compute_frontend", environment=environment)
    # the switch added to the node
    switch = bom.device_get("switch_48", device_template_name="switch_48", environment=environment)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("compute", server, 20)
    environment.device_overhead_add("switch", switch, 2)

    server.calc(bom=bom)

    return bom, environment
