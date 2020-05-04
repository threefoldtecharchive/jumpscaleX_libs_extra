class TFTFarmingCalculator:

    def __init__(self, node_id, node_config, threefold_explorer ):
        self.threefold_explorer = threefold_explorer
        #configuration as used for the node
        self.node_config = node_config
        #unique node id in the TFGrid
        self.node_id = node_id

    @property
    def is_certified(self):
        """
        ThreeFold has created a certification program which Farmers can opt in for.
        Certified farmers will have to buy their hardware from a certified hardware vendor.
        ThreeFold makes sure that that hardware is optimal from energy perspective
            and that the security features
            are optimally implemented (silicon route of trust, secure bios & boot, ...)
        ThreeFold will also make sure that network is good enough to the internet,

        If certified farmers will be in breach with their farming contract, they loose
            their certification and become a default farmer.
            ThreeFold with the help of the ThreeFold Explorer nodes checks on quality achieved in
            relation to the certification contract.

        The foundation will give free certification to boxes which benefit the distribution
        of nodes in the grid e.g. right now in Africa almost no capacity, whoever put boxes which are
            well distributed and they are bought from a certified partner will not have to pay for the
            certification a monthly or setup fee for a certain period.
            The boxes will still be certified though and the network uptime & capacity measured, its
            not a free pass to get more TFT.

        """
        return self.threefold_explorer.is_certified(self.node_id)

    @property
    def network_capability_zone(self):
        """
        south america & africa are emerging location, today the explorer returns 10
        ThreeFold uses best possible technical means to define the location of the node
        depending of the location ad network capability map as maintained by the foundation
        a number is returned
        @return between 1 and 20, today check is very easy, when emerging country return 10, otherwise 1
        """
        return self.threefold_explorer.network_capability_zone_get(self.node_id)

    def bandwith_check(self):
        """
        returns between 0 an 1, 1 is 100%, 0 is None
        for certified hardware its always 100% (1)
        """
        if self.is_certified:
            return 1
        # checks the threefold explorer & returns available bandwidth in mbit/sec avg
        # measurement done 24 times per day each time from node region (europe to europe, ...)
        # 2 MB of data is uploaded and downloaded from a random chosen node in the grid
        # local nodes are not used (check is done to see if nodes are local)
        bandwidth_availability = self.threefold_explorer.bandwidth_availability_get(self.node_id) #mbit/sec
        if bandwidth_availability > 2 * self.network_capability_zone:
            return 1
        elif bandwidth_availability > 1 * self.network_capability_zone:
            return 0.5
        else:
            return 0

    def utilization_check(self,month):
        """
        checks the threefold explorer & returns the utilization of the node
        returns between 0 an 1, 1 is 100%, 0 is None
        for the first 12 months its always 1
        for certified hardware its always 100%
        """
        if self.is_certified():
            return 1
        startmonth = self.threefold_explorer.month_start_get(self.node_id)
        utilization_rate =  self.threefold_explorer.utilization_rate_get(self.node_id)
        if month - startmonth < 12:
            #first 12 months utilization rate is 1, means all is rewarded
            return 1
        else:
            if utilization_rate > 50:
                return 1
            if utilization_rate > 25:
                return 0.5
            return 0

    def uptime_check(self):
        if self.certified_capacity:
            #the threefold explorer return 1 if agreed sla achieved (part of certification)
            #the std requested SLA is 99.8% for a certified farmer (1.44h per month)
            return self.threefold_explorer.uptime_sla_achieved(self.node_id)
        else:
            uptime = self.threefold_explorer.uptime_achieved(self.node_id)
            if uptime < 99:
                #corresponds to 7.2h, so if non certified capacity node was out for more
                #than 7.2h then no TFT farmed
                return 0
        return 1

    def difficulty_level_get(self, month):
        """
        return difficulty in relation to how many token there are
        the difficulty factor makes sure that there can never be more than 4 billion tokens
        """

        if month == 0:
            nr_of_tft_ever_farmed = 800000000 #starting point
        else:
            nr_of_tft_ever_farmed = int(self.simulation.tft_total(month - 1)) #look at previous month

        p = nr_of_tft_ever_farmed / 4000000000
        if p > 0.999999:
            perc = 1000000
        else:
            perc = 1 / (1 - p)

        return perc

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
        return cpr_investment_cost_in_usd_month / self.simulation.tft_price_get(month)


    def tft_farm(self, month):
        """
        calculate the farming of tft's
        """

        #cpr is like a hashrate for a bitcoin miner
        #in our case it represents the capability for a node to produce cloud units (our IT capacity)
        tft_farmed = self.node_config.cpr * self.farming_cpr_tft(month) / self.difficulty_level_get(month)

        return tft_farmed * self.uptime_check() * self.utilization_check() * self.bandwith_check()
