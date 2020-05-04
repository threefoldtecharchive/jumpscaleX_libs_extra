from Jumpscale import j

class TokenCreator:
    def __init__(self, simulation, environment):
        self.simulation = simulation
        self.environment = environment
        self.sheet = j.data.worksheets.sheet_new("tokencreator", nrcols=120)
        self.uptime = 99.9
        self.certified_capacity=False #simulator only supports non certified today


    def farming_cpr_tft(self,month):
        """
        cpr is the cloud production rate, like a hashrate for a bitcoin miner
        in our case a production rate of capacity for the internet

        cost to buy 1 cpr production capability in Q1 2020 = 40USD
        we took as definition that nr for cpr to usd
        we say ROI for batch 1 (month 1) is 6 months, thats why we need to devide by 6

        ROI = Return on investment
        """

        cpr_investment_cost_in_usd_month = j.tools.tfgrid_simulator.simulator_config.tokenomics.cpr_investment_usd / 6
        cpr_investment_cost_in_tft_month = cpr_investment_cost_in_usd_month / self.simulation.tft_price_get(month)
        return cpr_investment_cost_in_tft_month

    def tft_farm(self, month, nodes_batch):
        """
        calculate the farming of tft's
        """
        #cpr is like a hashrate for a bitcoin miner
        #in our case it represents the capability for a node to produce cloud units (our IT capacity)
        tft_new = nodes_batch.cpr * self.farming_cpr_tft(month) * self.difficulty_level_get(month)

        return tft_new

    def difficulty_level_get(self, month):
        """
        return difficulty in relation to how many token there are
        the difficulty factor makes sure that there can never be more than 4 billion tokens
        """

        if month == 0:
            nr_of_tft_ever_farmed = int(self.simulation.tft_total(0))
        else:
            nr_of_tft_ever_farmed = int(self.simulation.tft_total(month - 1)) #look at previous month

        p = nr_of_tft_ever_farmed / 4000000000
        if p > 0.999:
            return 0
        else:
            diff_level = 1 - p

        return diff_level

    def tft_cultivate(self, month, nodes_batch):
        """
        calculate the nr of TFT cultivated for the full batch
        cultivation means selling of capacity which results in TFT income for farmer
        """
        tftprice_now = self.simulation.tft_price_get(month)
        revenue_usd = nodes_batch.revenue_get(month)
        return revenue_usd / tftprice_now * 0.9

    def tft_burn(self, month, nodes_batch):
        """
        burning is no part of the chosen tokenomics model
        """
        return 0

