from Jumpscale import j


class TokenCreator:
    def __init__(self, simulation):
        simulation.difficulty_level_set("0:2,71:2")
        # super important factor, how does token price goes up, this is ofcourse complete speculation, no-one knows
        simulation.tokenprice_set("0:0.15,60:2")
        # simulation.tokenprice_set("0:1")
        simulation.difficulty_level_set("0:2,60:2")

        self.simulation = simulation

        self.max_tokens = 2 * 1000 * 1000 * 1000  # 2 billion
        self.nrtokens_forhalving = 100 * 1000 * 1000  # 20 steps till 2 billion
        self.tft_farm_per_cpr = 4000  # very important start parameter

    def initial_step_calculation(self, nodes_batch):
        # # just to have idea how to get started
        self.start_tokens = self.simulation.nodesbatch_get(0).tft_farmed_before_simulation
        tft_price = self.simulation.tft_price_get(0)
        nr_months_payback = 8
        cpr_cost = nodes_batch.node.cost_hardware / nodes_batch.node.cpr
        cpr_gain_per_month_required = cpr_cost / nr_months_payback
        tft_gain_required = cpr_gain_per_month_required / tft_price * self.difficulty_level_get(0)
        print(tft_gain_required)
        tft_gain_required = 4000  # calculated

    def tft_farm(self, month, nodes_batch):
        """
        @param month is the month to calculate the added tft for
        @param month_batch is when the node batch was originally added
        """
        # if month==0:
        #     self.initial_step_calculation(nodes_batch)
        cpr_total = nodes_batch.node.cpr * nodes_batch.nrnodes
        tft_new = cpr_total * self.tft_farm_per_cpr / self.difficulty_level_get(month)
        return tft_new

    def _tft_grow(self, month, nodes_batch):
        simulation = nodes_batch.simulation
        utilization = simulation.utilization_get(month)
        assert utilization < 100
        tft_price = simulation.tft_price_get(month)
        cpr_sales_price = simulation.cpr_sales_price_get(month)

        tft_new = utilization * float(cpr_sales_price) / float(tft_price) * nodes_batch.node.cpr * nodes_batch.nrnodes
        return tft_new

    def tft_cultivate(self, month, nodes_batch):
        """
        calculate the nr of TFT cultivated for the full batch
        cultivation means selling of capacity which results in TFT income

        @param month is the month to calculate the added tft for
        @param month_batch is when the node batch was originally added
        """
        tft_new = self._tft_grow(month, nodes_batch)
        return tft_new * 0.7

    def tft_burn(self, month, nodes_batch):
        tft_new = self._tft_grow(month, nodes_batch)
        return tft_new * 0.3

    def difficulty_level_get(self, month):
        """
        now a predefined extrapolated row, but could be calculated
        """
        if month == 0:
            nrtokens = self.simulation.nodesbatch_get(0).tft_farmed_before_simulation
        else:
            nrtokens = self.simulation.rows.tft_cumul.cells[month - 1]  # from previous month
        y = int(nrtokens / self.nrtokens_forhalving)
        return 2 ** y
