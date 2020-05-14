from Jumpscale import j


def bom_calc(environment):

    from hardware.components.components_amd import bom_populate

    environment.bom = bom_populate(environment.bom)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("compute", template="amd_starter", nr=1)
