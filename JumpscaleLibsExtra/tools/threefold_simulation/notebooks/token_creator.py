from Jumpscale import j


def tft_farm(self, month, nodes_batch):
    """
    @param month is the month to calculate the added tft for
    @param month_batch is when the node batch was originally added
    """
    tftprice_now = simulator.tft_price_get(month)
    nodes_batch_investment = nodes_batch.node.cost_hardware * nodes_batch.nrnodes
    nr_months_return = (
        12  # means if difficulty level would be 1, then the investment paid back in nr_months_return months
    )

    # FARMING ARGUMENTS ARE CREATED HERE, THIS IS THE MAIN CALCULATION
    tft_new = nodes_batch_investment / tftprice_now / self.difficulty_level_get(month) / nr_months_return

    return tft_new


def tft_cultivate(self, month, nodes_batch):
    """
    calculate the nr of TFT cultivated for the full batch
    cultivation means selling of capacity which results in TFT income

    @param month is the month to calculate the added tft for
    @param month_batch is when the node batch was originally added
    """
    utilization = simulator.utilization_get(month)
    assert utilization < 100
    tft_price = simulator.tft_price_get(month)
    cpr_sales_price = simulator.cpr_sales_price_get(month)

    tft_new = utilization * float(cpr_sales_price) / float(tft_price) * nodes_batch.node.cpr * nodes_batch.nrnodes

    return tft_new


def tft_burn(self, month, nodes_batch):
    return 0


def difficulty_level_get(self, month):
    """
    now a predefined extrapolated row, but could be calculated
    """
    return simulator.sheet.rows["difficulty_level"].cells[month]
