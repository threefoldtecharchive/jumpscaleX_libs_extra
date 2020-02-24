from Jumpscale import j

# from .SimulatorBase import SimulatorBase


class TokenCreator(j.baseclasses.object):
    def _init(self, **kwargs):
        self.simulator = kwargs["simulator"]

    def tft_farm(self, month, nodes_batch):
        """
        @param month is the month to calculate the added tft for
        @param month_batch is when the node batch was originally added
        """
        tftprice_now = self.simulator.tft_price_get(month)
        nodes_batch_investment = nodes_batch.node.cost_hardware * nodes_batch.nrnodes

        # FARMING ARGUMENTS ARE CREATED HERE, THIS IS THE MAIN CALCULATION
        tft_new = nodes_batch_investment / tftprice_now / self.difficulty_level_get(month) / 10

        return tft_new

    def tft_cultivate(self, month, nodes_batch):

        utilization = self.simulator.utilization_get(month) / 100
        assert utilization < 100
        tft_price = self.simulator.tft_price_get(month)
        cpr_sales_price = self.simulator.cpr_sales_price_get(month)

        tft_new = utilization * float(cpr_sales_price) / float(tft_price) * nodes_batch.node.cpr

        return tft_new

    def tft_burn(self, month, nodes_batch):
        return 0

    def difficulty_level_get(self, month):
        """
        now a predefined extrapolated row, but could be calculated
        """
        return self.simulator.sheet.rows["difficulty_level"].cells[month]
