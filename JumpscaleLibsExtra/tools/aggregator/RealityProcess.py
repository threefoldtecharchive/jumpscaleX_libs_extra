from Jumpscale import j

from .InfluxDumper import InfluxDumper
from .MongoDumper import MongoDumper
from .ECODumper import ECODumper

JSBASE = j.baseclasses.object


class RealitProcess(j.baseclasses.object):
    """
    """

    def __init__(self):
        self.__jslocation__ = "j.tools.realityprocess"
        JSBASE.__init__(self)

    def influxpump(self, influxdb, cidr="127.0.0.1", ports=[7777], rentention_duration="5d", workers=4):
        """
        will dump redis stats into influxdb(s)
        get connections from jumpscale clients...
        """

        InfluxDumper(influxdb, cidr=cidr, ports=ports, rentention_duration=rentention_duration).start(workers=workers)

    def monogopump(self, cidr="127.0.0.1", ports=[7777]):
        """
        will dump redis stats into influxdb(s)
        get connections from jumpscale clients...
        """

        MongoDumper(cidr=cidr, ports=ports).start()

    def ecodump(self, cidr="127.0.0.1", ports=[7777]):
        """
        Will dump redis ecos into mongodb

        :param cidr:
        :param port:
        :return:
        """
        ECODumper(cidr, ports).start()

    def logsdump(self, cidr="127.0.0.1", ports=[7777]):
        """
        Will dump redis logs into tar files.

        :param cidr:
        :param port:
        :return:
        """
        raise j.exceptions.NotImplemented
