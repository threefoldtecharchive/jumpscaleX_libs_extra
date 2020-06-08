from Jumpscale import j


def bom_calc(environment):

    from hardware.components.components_s3s import bom_populate

    environment.bom = bom_populate(environment.bom)

