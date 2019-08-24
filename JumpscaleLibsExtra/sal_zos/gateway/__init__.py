from .gateway import Gateway


class Gateways:
    def __init__(self, node):
        self.node = node

    def get(self, name):
        """
        :param name: Get gateway with name
        :type name: str
        :return: gateway object
        :rtype: Gateway
        """
        return Gateway(self.node, name)
