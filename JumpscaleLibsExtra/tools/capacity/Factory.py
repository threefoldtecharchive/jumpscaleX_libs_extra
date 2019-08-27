from Jumpscale import j

from .capacity_parser import CapacityParser
from .reservation_parser import ReservationParser
from .reality_parser import RealityParser

JSBASE = j.baseclasses.object


class Factory(j.baseclasses.object):
    __jslocation__ = "j.tools.capacity"

    def _init(self, **kwargs):
        self.parser = CapacityParser()
        self.reservation_parser = ReservationParser()
        self.reality_parser = RealityParser()
