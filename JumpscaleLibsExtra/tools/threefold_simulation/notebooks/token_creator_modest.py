from Jumpscale import j


class TokenCreator:
    def __init__(self, simulation):
        simulation.difficulty_level_set("0:2,71:2")
        # super important factor, how does token price goes up, this is ofcourse complete speculation, no-one knows
        simulation.tokenprice_set("0:0.15,60:2")
        # simulation.tokenprice_set("0:1")
        simulation.difficulty_level_set("0:2,60:2")

        self.simulation = simulation

    def tft_farm(self, month, nodes_batch):
        """
        @param month is the month to calculate the added tft for
        @param month_batch is when the node batch was originally added
        """
        simulation = nodes_batch.simulation
        tftprice_now = simulation.tft_price_get(month)
        nodes_batch_investment = nodes_batch.node.cost_hardware * nodes_batch.nrnodes
        # means if difficulty level would be 1, then the investment paid back in nr_months_return months
        nr_months_return = 8

        # FARMING ARGUMENTS ARE CREATED HERE, THIS IS THE MAIN CALCULATION
        tft_new = nodes_batch_investment / tftprice_now / self.difficulty_level_get(month) / nr_months_return

        return tft_new

    def _tft_grow(self, month, nodes_batch):
        simulation = nodes_batch.simulation
        utilization = simulation.utilization_get(month)
        assert utilization < 100
        tft_price = simulation.tft_price_get(month)
        cpr_sales_price = simulation.cpr_sales_price_get(month)

        tft_new = (
            utilization
            * float(cpr_sales_price)
            / float(tft_price)
            * nodes_batch.node.cpr
            * nodes_batch.nrnodes
            / self.difficulty_level_get(month)
        )
        return tft_new

    def tft_cultivate(self, month, nodes_batch):
        """
        calculate the nr of TFT cultivated for the full batch
        cultivation means selling of capacity which results in TFT income

        @param month is the month to calculate the added tft for
        @param month_batch is when the node batch was originally added
        """
        return self._tft_grow(month=month, nodes_batch=nodes_batch) / 2

    def tft_burn(self, month, nodes_batch):
        # burn as much as we make
        return self._tft_grow(month=month, nodes_batch=nodes_batch) / 2

    def difficulty_level_get(self, month):
        """
        now a predefined extrapolated row, but could be calculated
        """
        return self.simulation.sheet.rows["difficulty_level"].cells[month]
