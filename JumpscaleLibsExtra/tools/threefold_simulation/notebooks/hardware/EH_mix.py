from Jumpscale import j

# as used in gec farms as standard rack


def bom_calc(environment):

    from hardware.components.components_hpe import bom_populate

    environment.bom = bom_populate(environment.bom)
    # # see the bill of material sheet to define the devices
    # compute = environment.bom.device_get("hpe_compute_server")
    # storage = environment.bom.device_get("hpe_storage_server")
    # switch = environment.bom.device_get("switch_48")
    #
    # # an environment to simulate the overhead per node (eg. 1 switch per node)
    # environment.device_node_add("compute", compute, 11)
    # environment.device_node_add("storage", storage, 5)
    # environment.device_overhead_add("switch", switch, 2)

    environment.device_node_add("compute", template="hpe_compute_server", nr=1)
    environment.device_node_add("storage", template="hpe_storage_server", nr=1)
    environment.device_overhead_add("switch", template="switch_48", nr=2)
