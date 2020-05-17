from Jumpscale import j


def bom_calc(environment):

    from hardware.components.components_s3s import bom_populate

    environment.bom = bom_populate(environment.bom)

    # sn5
    environment.device_node_add("compute", template="sn5", nr=1)
