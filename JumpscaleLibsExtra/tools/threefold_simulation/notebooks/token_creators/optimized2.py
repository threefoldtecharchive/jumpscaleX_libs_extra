from Jumpscale import j

"""
simulator quite in line with how we do it today

improvements

- burning of 50% of cultivated tokens, which means nr of tokens goes down
- max of tokens is 2 billion

"""


class TokenCreator:
    def __init__(self, simulation, environment):
        self.simulation = simulation
        self.environment = environment
        self.sheet = j.data.worksheets.sheet_new("tokencreator", nrcols=120)

        self._init_predefined_tft_price()

    def _init_predefined_tft_price(self):
        self.row_tft = self.sheet.addRow("tft", aggregate="LAST", ttype="float", empty=True, nrcols=120)
        self.row_tft.cells[0] = 0.15
        self.row_tft.cells[60] = 0.15 * 20
        self.row_tft.cells[119] = 0.15 * 30
        self.row_tft.interpolate()

    def cpr_usd(self, month):

        # cpr is the cloud production rate, like a hashrate for a bitcoin miner
        # in our case a production rate of capacity for the internet

        # cost to buy 1 cpr production capability in Q1 2020 = 40USD
        # we took as definition that nr for cpr to usd
        # we say ROI for batch 1 (month 1) is 6 months, thats why we need to devide by 6

        return 40 / 6

    def predefined_tft_price(self, month):
        return self.row_tft.cells[month]

    def cpr_tft(self, month):
        # we can choose the model we want
#         tftprice_now = self.simulation.tft_price_get(month)
        tftprice_now = self.predefined_tft_price(month)
        return self.cpr_usd(month) / tftprice_now

    def tft_farm(self, month, nodes_batch):
        """
        @param month is the month to calculate the added tft for
        @param month_batch is when the node batch was originally added
        """

        # if month == 50 and nodes_batch.month_start > 40:
        #     j.shell()
        #     w

        # FARMING ARGUMENTS ARE CREATED HERE, THIS IS THE MAIN CALCULATION
        tft_new = nodes_batch.cpr * self.cpr_tft(month) / self.difficulty_level_get(month)

        return tft_new

    def _tft_for_capacity_sold(self, month, nodes_batch):
        """
        tft which are coming back to system because of people buying capacity
        """
        utilization = self.simulation.utilization_get(month)
        assert utilization < 100
        tft_price = self.simulation.tft_price_get(month)
        cpr_sales_price = self.environment.sales_price_cpr_unit_get(self.simulation, month)
        tft_received = utilization * float(cpr_sales_price) / float(tft_price) * nodes_batch.cpr

        return tft_received

    def tft_cultivate(self, month, nodes_batch):
        """
        calculate the nr of TFT cultivated for the full batch
        cultivation means selling of capacity which results in TFT income for farmer

        @param month is the month to calculate the added tft for
        @param month_batch is when the node batch was originally added
        """
        return self._tft_for_capacity_sold(month=month, nodes_batch=nodes_batch) * 0.5

    def tft_burn(self, month, nodes_batch):
        """
        burn as much as we cultivate

        this is a serious burning policy, this keeps nr of TFT limited

        this is the benefit of any TFT holder because we burn (destroy) tokens as capacity is sold

        """

        if month < 24:
            # 10% is kept for foundation for first 24 months
            part = 0.4
        else:
            # 5% is kept for foundation
            part = 0.45
        return self._tft_for_capacity_sold(month=month, nodes_batch=nodes_batch) * part

    def difficulty_level_get(self, month):
        """
        return difficulty in relation to how many token there are
        if 99% of 2 billion then becomes quite impossible to farm tokens
        but because of cultivation & burning it will become easier again

        this is the main formulla to make sure we can never have more than 2billion tokens

        """
        tft_total = int(self.simulation.tft_total(month - 1))
        perc = tft_total / 2000000000 * 100
        if perc < 10:
            return 1
        elif perc < 20:
            return 2
        elif perc < 30:
            return 3
        elif perc < 40:
            return 3
        elif perc < 50:
            return 3
        elif perc < 60:
            return 4
        elif perc < 70:
            return 4
        elif perc < 80:
            return 5
        elif perc < 90:
            return 10
        elif perc < 95:
            return 15
        elif perc < 98:
            return 20
        else:
            return 10000000  # now there should be no farming any longer
