from Jumpscale import j


def bom_calc(environment):

    from hardware.components.components_amd import bom_populate

    environment.bom = bom_populate(environment.bom)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("compute", template="server", nr=20)
    environment.device_overhead_add("switch", template="switch", nr=2)
