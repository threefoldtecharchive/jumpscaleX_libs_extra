from Jumpscale import j


def bom_calc(environment):

    from hardware.components.components_s3s import bom_populate

    environment.bom = bom_populate(environment.bom)

    # medium
    environment.device_node_add("compute", template="medium", nr=1)
