from Jumpscale import j


class SimulatorConfig(j.baseclasses.object_config_redis):
    _SCHEMATEXT = """
        @url = threefold.simulation.config
        name= ""
        tft_pricing_type = "fixed,auto" (E)
        tft_price_5y = 3 (F)
        node_growth = 1000000 (I)
        startmonth = 1 (I)
        hardwareconfig = "A_dc_rack"
        

        pricing = (O) !threefold.simulation.pricing        
        tokenomics= (O) !threefold.simulation.tokenomics
        network = (O) !threefold.simulation.network
        cloudvaluation = (O) !threefold.simulation.cloudvaluation.config

        @url = threefold.simulation.tokenomics
        cpr_investment_usd = 40 (I)
        burn_percent = 0 (I)        
        
        @url = threefold.simulation.network
        nu_multiplier_from_cu = 10 (I)
        nu_multiplier_from_su = 40 (I)        

        @url = threefold.simulation.pricing
        price_cu = 12 (F)
        price_su = 8 (F)
        price_nu = 0.05 (F)
        
        @url = threefold.simulation.cloudvaluation.config
        price_cu = 15 (F)
        price_su = 10 (F)
        price_nu = 0.05 (F)
        revenue_months = 30 (I)
        margin_months = 60 (I)
        indextype = "revenue,margin" (E)
        #is the price the token would achieve over 5 years as baseline
        tft_price_5y_baseline = 4 (I)      
        

        """
