from Jumpscale import j

#as used in bancadati farm, compute frontend to archive

def bom_calc(bom, environment):

    from hardware.components_supermicro import bom_populate
    bom=bom_populate(bom)

    # see the bill of material sheet to define the devices
    compute = bom.device_get("archive_compute_frontend", device_template_name="archive_compute_frontend", environment=environment)
    storage = bom.device_get("storage_server", device_template_name="storage_server", environment=environment)
    switch = bom.device_get("switch_48", device_template_name="switch_48", environment=environment)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("compute", compute, 29)
    environment.device_node_add("storage", storage, 285)
    environment.device_overhead_add("switch", switch, 30)

    return bom, environment
