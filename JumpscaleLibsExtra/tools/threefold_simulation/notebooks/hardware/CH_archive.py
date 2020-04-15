from Jumpscale import j

# as used in bancadati farm, compute frontend to archive


def bom_calc(environment):

    from hardware.components.components_supermicro import bom_populate

    environment.bom = bom_populate(environment.bom)

    # see the bill of material sheet to define the devices
    # compute = environment.bom.device_get("archive_compute_frontend", environment=environment)
    # storage = environment.bom.device_get("storage_server", environment=environment)
    # switch = environment.bom.device_get("switch_48", environment=environment)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("compute", template="archive_compute_frontend", nr=29)
    environment.device_node_add("storage", template="storage_server", nr=285)
    environment.device_overhead_add("switch", template="switch_48", nr=30)
