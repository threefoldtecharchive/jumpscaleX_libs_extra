from Jumpscale import j
from .SimulatorBase import SimulatorBase


class NodesBatchMonth(SimulatorBase):

    _SCHEMATEXT = """
        @url = threefold.simulation.nodesbatch.month
        batch_nr = 0
        month_now = 0
        tft_farmed_total = 0 (F)
        tft_cultivated_total = 0 (F)

        """

    def _init(self, **kwargs):
        self._model_ = False
        self._cat = "NodesBatchMonth"
        self.month_now = kwargs["month_now"]
        self.nodesbatch = kwargs["nodesbatch"]
        self.batch_nr = self.nodesbatch.batch_nr
        j.shell()


class NodesBatchMonths(NodesBatchMonth):
    """
    aggregation of multiple months
    """

    def _init(self, batch_nr, months_from, months_to, **kwargs):
        """

        @param batchnr: is the nr of the batch (month 1 = 0, so batch_nr 0 is the first batch of nodes added)
        """
        self._model_ = False
        self._cat = "NodesBatchMonths"
        self.nodesbatch = kwargs["nodesbatch"]
        self.batch_nr = self.nodesbatch.batch_nr

        j.shell()


class NodesBatch(SimulatorBase):
    """
    a normalized node over time
    """

    _SCHEMATEXT = """
        @url = threefold.simulation.nodesbatch
        batch_nr = (I)  #0 is month 1
        cost_node = (N)
        power_node = (I)
        rackspace_u_node = (F)
        count = 0 #nr of nodes
        cost_hardware_month = (N)
        cost_power_month = (N)
        cost_rackspace_month = (N)
        cost_total_month = (N)
        cpr = (I)  #cloud production rate
        month_start = 0
        months_left = 60
        tft_farmed_before_simulation = 0 (F)
        """

    def _init(self, **kwargs):
        self._cat = "NodesBatch"
        self._model_ = False
        j.shell()

    def month_get(self, month):
        NodesBatchMonth(month_now=month, nodesbatch=self)

    def months_get(self, months_from=0, months_to="END"):
        if months_to == "END":
            j.shell()
            months_to = 0
        NodesBatchMonths(months_from=months_from, months_to=months_to, nodesbatch=self)

    def roi_farming_hwonly(self, tft_price=None):
        if not tft_price:
            tft_price = j.tools.tfsimulation.current.tft_price_get()
        farming_income = self.tft_farmed_total * tft_price
        return farming_income / self.cost_hardware_total

    def roi_farming(self, tft_price=None):
        if not tft_price:
            tft_price = j.tools.tfsimulation.current.tft_price_get()
        farming_income = self.tft_farmed_total * tft_price
        return farming_income / float(self.cost_total)

    @property
    def roi_farming_end(self):
        return self.roi_farming()
