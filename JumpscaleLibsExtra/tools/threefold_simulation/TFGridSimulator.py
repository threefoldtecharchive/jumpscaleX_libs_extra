from Jumpscale import j

from .BillOfMaterial import *
from .NodesBatch import *
from .SimulatorBase import SimulatorBase
import matplotlib.pyplot as plt

class TokenCreator:
    pass


class TFGridSimulator(SimulatorBase):

    _SCHEMATEXT = """
        @url = threefold.simulation
        name = ""
        simulated = false (B)               
        """

    @property
    def sales_price_cu(self):
        return self.config.pricing.price_cu

    @property
    def sales_price_su(self):
        return self.config.pricing.price_su

    @property
    def sales_price_nu(self):
        return self.config.pricing.price_nu

    def export_(self):
        r = {}
        r["sheet"] = self.sheet.export_()
        r["data"] = self._data._ddict
        r["nodebatches"] = [i.export_() for i in self.nodebatches]
        return r

    def markdown_export(self,path):

        def export(name,data,indent=None):
            if not isinstance(data,str):
                data = j.data.serializers.json.dumps(data, sort_keys=True, indent=indent, encoding='ascii')
            j.sal.fs.writeFile(f"{path}/{name}.json", data)

        export("sheet",self.sheet.export_())
        export("config", self.config._data._ddict_hr,1)
        months=[1,20,40]
        for m in months:
            nb=self.nodebatches[m]
            nb.markdown_report(path=path)
            export("nodebatch_%s"%m, nb.export_())
            for m2 in months:
                md = nb.markdown_profit_loss(m2)
                j.sal.fs.writeFile(f"{path}/nodesbatch_profit_loss_{m}_{m2}.md",md)
        months = [1, 20, 40, 60]
        for m in months:
            md = self.markdown_reality_check(m)
            j.sal.fs.writeFile(f"{path}/reality_check_{m}.md",md)

        self.markdown_cloud_valuation(60,path=path)

        export("environment", self.environment._data._ddict_hr, 1)
        export("bom", self.environment.bom._data._ddict_hr, 1)

        self.environment.bom.markdown_get(path=path)

        self.environment.markdown_env_detail_get(path=path)

        self.markdown_grid_growth(path=path)

        j.sal.fs.writeFile(f"{path}/readme.md", "!!!include:wiki:simulator_readme\n")
        j.sal.fs.writeFile(f"{path}/nodebatches.md", "!!!include:wiki:simulator_nodebatches\n")
        j.sal.fs.writeFile(f"{path}/reality_checks.md", "!!!include:wiki:simulator_reality_checks\n")
        C="""
        - [home](readme.md)
        - [grid growth](tfgrid_growth.md)
        - [grid valuation](tfgrid_valuation.md)
        - [server details](device_normalized.md)
        - [nodebatches](nodebatches.md)
            - [added month 1](nodesbatch_1_report.md)
            - [added month 20](nodesbatch_20_report.md)
            - [added month 40](nodesbatch_40_report.md)
        - [reality checks](reality_checks.md)
            - [month 1](reality_check_1.md)
            - [month 20](reality_check_20.md)
            - [month 40](reality_check_40.md)
            - [month 60](reality_check_60.md)
        """
        j.sal.fs.writeFile(f"{path}/_sidebar.md", j.core.tools.text_strip(C))
        j.sal.fs.writeFile(f"{path}/_navbar.md", "!!!include:wiki:simulator_navbar\n")



    def export_redis(self):
        data = j.data.serializers.msgpack.dumps(self.export_())
        j.core.db.hset("simulations", self.name, data)

    def import_(self, ddict):
        self.sheet.import_(ddict["sheet"])
        self._data_update(ddict["data"])
        month = 0
        self.nodebatches = []
        for nb_dict in ddict["nodebatches"]:
            nb = NodesBatch(
                simulation=self, name=f"month_{month}", environment=self.environment, nrnodes=0, month_start=0
            )
            month += 1
            nb.import_(nb_dict)
            self.nodebatches.append(nb)
        self.sheet.clean()

    def import_redis(self, key, autocacl=True, reset=False):
        """
        @parama autocalc True means we will calc automatically if we cant find the info in redis
        """
        ddict = j.core.db.hget("simulations:%s" % key, self.name)
        if not reset and ddict:
            data = j.data.serializers.msgpack.loads(ddict)
            self.import_(data)
        else:
            self.nodesbatches_add_auto()
            self.calc()
            self.export_redis()

    def _init(self, **kwargs):
        self.sheet = j.data.worksheets.sheet_new("simulation", nrcols=120)
        self.rows = self.sheet.rows
        self.nodebatches = []  # 0 is the first batch, which stands for month 1
        self.token_creator = TokenCreator()
        self.config = j.tools.tfgrid_simulator.simulator_config

    def nodesbatch_add(self, environment, month, nrnodes):
        self._nodesbatch_start_check(environment=environment)
        assert environment.nodes_production_count > 0
        nb = NodesBatch(
            simulation=self, name=f"month_{month}", environment=environment, nrnodes=nrnodes, month_start=month
        )
        while len(self.nodebatches) < month + 1:
            self.nodebatches.append(None)
        self.nodebatches[month] = nb
        return self.nodebatches[month]

    def _nodesbatch_start_check(self, environment):
        if not "cost_rack_unit" in self.sheet.rows:
            self.cost_rack_unit_set(environment)
            self.cost_power_kwh_set(environment)

    def nodesbatch_start_set(self, environment, nrnodes=1500, months_left=36, tft_farmed_before_simulation=0):
        self._nodesbatch_start_check(environment=environment)
        nb = self.nodesbatch_add(environment=environment, month=0, nrnodes=nrnodes)
        nb.tft_farmed_before_simulation = tft_farmed_before_simulation
        nb.months_left = months_left
        return nb

    def nrnodes_new_set(self, growth):
        """
        define growth rate
        :param growth:
        :return:
        """
        self._interpolate("nrnodes_new", growth)

    def cpr_improve_set(self, args):
        """
        cpr = Cloud Production Rate (its like the hashrate on bitcoin)
        define how cpr improves
        args is month:improve_in_percent from original
        args e.g. 72:40
        means over 72 months 40% off of the cpr
        :param args:
        :return:
        """
        self._interpolate("cpr_improve", args)

    def cpr_improve_get(self, month):
        """
        return 0->0.4
        0.4 means price declide of 40%
        """
        cpr_improve = self.rows.cpr_improve.cells[month]
        assert cpr_improve >= 0
        assert cpr_improve < 101
        return self._float(cpr_improve / 100)

    def cpr_sales_price_decline_set(self, args):
        """
        The salesprice will decline over time

        args e.g. 72:40
        means over 72 months 40% off of the cpr
        :param args:
        :return:
        """
        self._interpolate("cpr_sales_price_decline", args)

    def sales_price_decline_get(self, month):
        """
        return 0->0.4
        0.4 means price declide of 40%
        """
        cpr_sales_price_decline = self.rows.cpr_sales_price_decline.cells[month]
        assert cpr_sales_price_decline >= 0
        assert cpr_sales_price_decline < 101
        return self._float(cpr_sales_price_decline / 100)

    def utilization_set(self, args):
        """
        define how cpr improves
        args is month:utilization of capacity
        args e.g. 72:90
        :param args:
        :return:
        """
        self._interpolate("utilization", args)

    def tokenprice_set(self):
        """
        define how tokenprice goes up (in $)
        :param args:
        :return:
        """
        config = j.tools.tfgrid_simulator.simulator_config
        if config.tft_pricing_type == "auto":
            tft_price_5y = config.cloudvaluation.tft_price_5y_baseline
        else:
            tft_price_5y = config.tft_price_5y
        assert tft_price_5y > 0.09

        # need to do over 12 years or the price of tokens weirdly stops
        val = (tft_price_5y - 0.15) * 2 + 0.15
        self._interpolate("tokenprice", "0:0.15,119:%s" % val)

    def difficulty_level_set(self, args):
        """
        difficulty level changes over time
        :param args:
        :return:
        """
        self._interpolate("difficulty_level", args)

    def _interpolate(self, name, args, ttype="float"):
        if name in self.sheet.rows:
            self.sheet.rows.pop(name)
        args = [i.strip().split(":") for i in args.split(",") if i.strip()]
        row = self._row_add(name, ttype=ttype, aggregate="FIRST", empty=False, clean=False, defval=None)
        for x, g in args:
            row.cells[int(x)] = float(g)
        if not row.cells[0]:
            row.cells[0] = 0
        row.interpolate()
        return row

    def grid_valuation(self, month=None):
        if month == None:
            month = self.sheet.nrcols - 1
        return self.cloud_valuation_get(x=month)

    def grid_valuation_values(self,rev=None,multiple=None):
        res=[]
        for x in range(24,60):
            v=self.cloud_valuation_get( x, rev=rev, multiple=multiple)
            res.append(v/1000000)
        return res

    def tft_price_get(self, month=None):
        config = j.tools.tfgrid_simulator.simulator_config
        if month > 12 and config.tft_pricing_type == "auto":
            if month == 0:
                month2 = 1
            else:
                month2 = month
            tft_baseline = self.sheet.rows.tokenprice.cells[month]
            grid_valuation = self.grid_valuation(month=month)
            nrtokens = self.sheet.rows.tft_farmed_cumul.cells[month2 - 1]
            tft_index_price = grid_valuation / nrtokens
            if tft_index_price < tft_baseline:
                tft_index_price = tft_baseline
            self.sheet.rows.tokenprice.cells[month] = tft_index_price
        r = self.sheet.rows.tokenprice.cells[month]
        assert r > 0
        return r

    def tft_total(self, month=None):
        """
        amounts of tft in the blockchain
        total nr of tft
        """
        assert month != None
        tft_total = int(self.rows.tft_farmed_cumul.cells[month])
        return tft_total

    def _row_add(self, name, aggregate="FIRST", ttype="int", defval=0, empty=True, clean=True):
        row = self.sheet.addRow(name, aggregate=aggregate, ttype=ttype, empty=empty, nrcols=120, defval=defval)
        if clean:
            row.clean()
        return row

    def _prepare(self):
        if not "nrnodes_total" in self.rows:

            self._row_add("nrnodes_total")

            self._row_add("tft_farmed")
            self._row_add("tft_farmed_cumul")
            self._row_add("tft_cultivated")
            # sold tft to cover power & rackspace costs
            self._row_add("tft_sold")
            self._row_add("tft_burned")
            self._row_add("tft_farmer_income")
            self._row_add("tft_farmer_income_cumul")

            self._row_add("cost_rackspace")
            self._row_add("cost_power")
            self._row_add("cost_hardware")
            self._row_add("cost_maintenance")
            self._row_add("cost_network")
            self._row_add("cost_total")
            self._row_add("rackspace_u", ttype="float")
            self._row_add("power_kw", ttype="float")

            self._row_add("investment", defval=0)
            self._row_add("revenue")

            self._row_add("tft_farmer_income_usd")
            self._row_add("tft_farmer_income_cumul_usd")  # What is cumul = cumulative (all aggregated)
            self._row_add("tft_marketcap")

            self._row_add("rev_compute")
            self._row_add("rev_storage")
            self._row_add("rev_network")
            self._row_add("rev_total")
            self._row_add("rev_compute_max")
            self._row_add("rev_storage_max")
            self._row_add("rev_network_max")
            self._row_add("rev_total_max")

            self.tokenprice_set()

    def _float(self, val):
        if val == None:
            return 0.0
        return float(val)

    def nodesbatches_add_auto(self, environment=None):
        """
        will calculate now many batches to add in line with the growth in nr nodes
        """

        self._prepare()
        if len(self.nodebatches) > 0:
            self.nodebatches = self.nodebatches[0:1]  # only maintain first one

        if not environment:
            environment = self.environment

        # calculate growth in nr nodes
        for month_now in range(0, 120):
            if len(self.nodebatches) == 0 or month_now > 0:
                nr_new = self.rows.nrnodes_new.cells[month_now]
                if nr_new > 0:
                    self.nodesbatch_add(environment=environment, month=month_now, nrnodes=nr_new)
                    self.rows.nrnodes_total.cells[month_now] = (
                        self.rows.nrnodes_total.cells[month_now - 1] + self.rows.nrnodes_new.cells[month_now]
                    )
            else:
                self.rows.nrnodes_total.cells[month_now] = self.nodebatches[0].nrnodes

        self.rows.nrnodes_new.clean()  # makes sure we get nicely formatted cells (int)
        self.rows.nrnodes_total.clean()

    def calc(self, environment=None):

        if not environment:
            environment = self.environment

        if self.simulated:
            raise j.exceptions.Input("cannot call this method twice: calc")

        self._prepare()

        for month in range(0, 120):
            tftprice_now = self.tft_price_get(month)
            # now walk over all batches which came live since day 0
            for month_batch in range(0, month + 1):
                nb = self.nodebatches[month_batch]  # previous batch, all there is already calculated
                nb._calc(month)
                self.rows.rackspace_u.cells[month] += self._float(nb.rows.rackspace_u.cells[month])
                self.rows.power_kw.cells[month] += self._float(nb.rows.power.cells[month]) / 1000
                self.rows.tft_farmed.cells[month] += self._float(nb.rows.tft_farmed.cells[month])
                self.rows.tft_cultivated.cells[month] += self._float(nb.rows.tft_cultivated.cells[month])
                self.rows.tft_sold.cells[month] += self._float(nb.rows.tft_sold.cells[month])
                self.rows.tft_burned.cells[month] += self._float(nb.rows.tft_burned.cells[month])
                self.rows.tft_farmer_income.cells[month] += self._float(nb.rows.tft_farmer_income.cells[month])

                # remove the burned ones from the total
                self.rows.tft_farmer_income_cumul.cells[month] += self._float(
                    nb.rows.tft_farmer_income_cumul.cells[month]
                ) - self._float(nb.rows.tft_burned.cells[month])

                self.rows.tft_farmer_income_usd.cells[month] += self._float(nb.rows.tft_farmer_income_usd.cells[month])
                self.rows.tft_farmer_income_cumul_usd.cells[month] += self._float(
                    nb.rows.tft_farmer_income_cumul_usd.cells[month]
                )

                self.rows.cost_rackspace.cells[month] += self._float(nb.rows.cost_rackspace.cells[month])
                self.rows.cost_power.cells[month] += self._float(nb.rows.cost_power.cells[month])
                self.rows.cost_hardware.cells[month] += self._float(nb.rows.cost_hardware.cells[month])
                self.rows.cost_maintenance.cells[month] += self._float(nb.rows.cost_maintenance.cells[month])
                self.rows.cost_network.cells[month] += self._float(nb.rows.cost_network.cells[month])

                self.rows.investment.cells[month] += self._float(nb.cost_hardware)

                self.rows.rev_compute.cells[month] += self._float(nb.rows.rev_compute.cells[month])
                self.rows.rev_storage.cells[month] += self._float(nb.rows.rev_storage.cells[month])
                self.rows.rev_network.cells[month] += self._float(nb.rows.rev_network.cells[month])
                self.rows.rev_total.cells[month] += self._float(nb.rows.rev_total.cells[month])
                self.rows.rev_compute_max.cells[month] += self._float(nb.rows.rev_compute_max.cells[month])
                self.rows.rev_storage_max.cells[month] += self._float(nb.rows.rev_storage_max.cells[month])
                self.rows.rev_network_max.cells[month] += self._float(nb.rows.rev_network_max.cells[month])
                self.rows.rev_total_max.cells[month] += self._float(nb.rows.rev_total_max.cells[month])

            self.rows.tft_farmer_income_usd.cells[month] = tftprice_now * self.rows.tft_farmer_income.cells[month]
            self.rows.tft_farmer_income_cumul_usd.cells[month] = (
                tftprice_now * self.rows.tft_farmer_income_cumul.cells[month]
            )
            self.rows.revenue.cells[month] = tftprice_now * self.rows.tft_cultivated.cells[month]
            if month > 0:
                self.rows.tft_farmed_cumul.cells[month] = (
                    self.rows.tft_farmed_cumul.cells[month - 1] + self.rows.tft_farmed.cells[month]
                )
            else:
                self.rows.tft_farmed_cumul.cells[month] = self.rows.tft_farmed.cells[month]

            self.rows.tft_marketcap.cells[month] = self.rows.tft_farmed_cumul.cells[month] * self.tft_price_get(month)

        self.rows.tft_farmed.clean()
        self.rows.tft_cultivated.clean()
        self.rows.tft_burned.clean()
        self.rows.tft_sold.clean()
        self.rows.tft_farmer_income.clean()
        self.rows.tft_farmer_income_cumul.clean()

        t = (
            self.rows.cost_network
            + self.rows.cost_hardware
            + self.rows.cost_maintenance
            + self.rows.cost_rackspace
            + self.rows.cost_power
        )
        self.rows.cost_total.cells = t.cells

        self._grid_valuation_calc()

    def _grid_valuation_calc(self):

        row = self._row_add("grid_valuation_usd", aggregate="FIRST", ttype="int", defval=0, empty=True, clean=True)

        def do(val, x, args):
            return self.cloud_valuation_get(x)

        row.function_apply(do)

    def cloud_cost_get(self, x):
        """
        is the max cost of the grid (at full utilization)
        for power, rackspace & hardware (written off over 5 years)
        """
        node = self.environment.node_normalized
        nrnodes = self.rows.nrnodes_total.cells[x]
        cost = float(node.total.cost_total_month) * float(nrnodes)
        return cost

    def cloud_valuation_get(self, x,rev=None,multiple=None):
        """
        the value of the grid at that month based on selected cloud index calculation method
        """
        rev = self.rows.rev_total_max.cells[x]
        if multiple!=None:
            if rev:
                rev = int(rev * multiple)
                return rev
            else:
                cost = self.cloud_cost_get(x)
                margin = rev - cost
                margin = int(margin * multiple)
                return margin
        else:
            config = j.tools.tfgrid_simulator.simulator_config.cloudvaluation
            if config.indextype == "revenue":
                rev = int(rev * config.revenue_months)
                return rev
            else:
                cost = self.cloud_cost_get(x)
                margin = rev - cost
                margin = int(margin * config.margin_months)
                return margin

    def markdown_grid_growth(self, path=None):
        fi = j.core.text.format_item

        def r(val):
            val=val/1000000
            return val

        def r2(val):
            val=val/1000
            return val

        tft_gr_120=self.sheet.graph(title="tft growth 120 months (million)", path=path, row_names=["tft_farmed","tft_cultivated","tft_sold","tft_farmer_income"], row_filters=r, row_labels=None, start=1, end=None)
        tft_gr_60=self.sheet.graph(title="tft growth 60 months (million)", path=path,
                         row_names=["tft_farmed", "tft_cultivated", "tft_sold", "tft_farmer_income"], row_filters=r,
                         row_labels=None, start=1, end=60)

        tft_gr_60_b=self.sheet.graph(title="tft growth 60 months cumulated (million)", path=path,
                         row_names=["tft_farmed_cumul", "tft_farmer_income_cumul"], row_filters=r,
                         row_labels=None, start=1, end=60)

        utilization=self.sheet.graph(title="utilization grid", path=path,row_names=["utilization"], start=1, end=60)

        revenue_month = self.sheet.graph(title="revenue per month (million)", path=path,row_names=["rev_compute", "rev_storage", "rev_network", "rev_total"],row_filters=r, row_labels=None, start=1, end=60)
        revenue_month_max = self.sheet.graph(title="revenue per month (million) if 100% used capacity", path=path,
                                         row_names=["rev_compute_max", "rev_storage_max", "rev_network_max", "rev_total_max"],
                                         row_filters=r, row_labels=None, start=1, end=60)

        power_kw=self.sheet.graph(title="power usage in giga watt/hour", path=path,row_names=["power_kw"],row_filters=r,start=1, end=60,row_labels=["gwh"])

        tft_marketcap = self.sheet.graph(title="tft marketcap in million usd", path=path, row_names=["tft_marketcap"],row_filters=r, start=1, end=60)

        nr_nodes_new = self.sheet.graph(title="nr nodes in grid new per month (per thousand)", path=path, row_names=["nrnodes_new"],row_filters=r2, start=1, end=60)
        nr_nodes_total = self.sheet.graph(title="nr nodes in grid total (per thousand)", path=path, row_names=["nrnodes_total"],row_filters=r2, start=1, end=60)

        C = f"""
        ## Grid Growth Report

        ### Default Node

        - [default node details](device_normalized.md)
        - [bill of material used, hardware components](bom.md)

        ### Token Growth 

        The price of the tokens in relation to the simulator (please note this does not predict any token price, its just a simulation)

        > disclaimer: the TFT is not an investment instrument.

        ![]({self.graph_token_price_png(path=path)})
        TFT price can be given by you (see arguments) or automatically calculated.

        ![]({tft_marketcap})
        What is the calculated marketcap of the TFT over 60 months?
        
        ### TFT movements

        Over 120 months, how do TFT get

        - farmed: means mined because farmers connect hardware to the grid
        - cultivated: means people buying capacity from the farmers
        - sold: means the farmers sell their TFT to pay for bandwidth, power, maintenance & rackspace
        - farmer income = farmed + cultivated = sold (basically the income for the farmer)

        ![]({tft_gr_120})
        Over 120 months

        ![]({tft_gr_60})        
        Over 60 months which is the time window we look at

        ![]({tft_gr_60_b})        
        - Over 60 months cumulated which means we sum the previous months (so the total with previous months in)
        - The income is higher than the total farmed because has cultivated TFT inside.
        - The max nr of farmed is 4 Billion

        ### Grid Growth

        ![]({utilization})  
        Utilization of the grid avg out.

        ![]({nr_nodes_new})
        ![]({nr_nodes_total})
        How many nodes active on the grid.

        ### Revenue of capacity sold on the grid

        ![]({revenue_month})

        ![]({revenue_month_max})
    
        ### Valuation of the grid

        - see [valuation grid](tfgrid_valuation.md)

        ### Power used of the grid

        ![]({power_kw})

        """

        C = j.core.tools.text_strip(C)
        if path:
            j.sal.fs.writeFile(f"{path}/tfgrid_growth.md", C)
        return C

    def markdown_cloud_valuation(self, month=60,path=None):
        fi = j.core.text.format_item
        rev_compute = self.rows.rev_compute.cells[month]
        rev_storage = self.rows.rev_storage.cells[month]
        rev_network = self.rows.rev_network.cells[month]
        rev_total = self.rows.rev_total.cells[month]
        rev_compute_max = self.rows.rev_compute_max.cells[month]
        rev_storage_max = self.rows.rev_storage_max.cells[month]
        rev_network_max = self.rows.rev_network_max.cells[month]
        rev_total_max = self.rows.rev_total_max.cells[month]

        cost_rackspace = self.rows.cost_rackspace.cells[month]
        cost_maintenance = self.rows.cost_maintenance.cells[month]
        cost_hardware = self.rows.cost_hardware.cells[month]
        cost_network = self.rows.cost_network.cells[month]
        cost_power = self.rows.cost_power.cells[month]
        cost_total = self.rows.cost_total.cells[month]

        if self.config.cloudvaluation.indextype == "REVENUE":
            nrmonths = self.config.cloudvaluation.revenue_months
        else:
            nrmonths = self.config.cloudvaluation.margin_months

        pi=self.price_index_get()

        C = f"""
        ## TF Grid Valuation Report.

        ### Token Price 

        The price of the tokens in relation to the simulator.
        Please note this is just a simulation, by no means a prediction of the TFT price.

        ![]({self.graph_token_price_png(path=path)} ':size=800x600')

        > disclaimer: the TFT is not an investment instrument.

        ### Valuation Of Grid Calculation

        | valuation mechanism | multiple | valuation in USD |
        | --- | --- | --- |
        | revenue | 12 | {fi(self.cloud_valuation_get( 60, rev=True, multiple=12))} |
        | revenue | 20 | {fi(self.cloud_valuation_get( 60, rev=True, multiple=20))} |
        | revenue | 30 | {fi(self.cloud_valuation_get( 60, rev=True, multiple=30))} |
        | revenue | 40 | {fi(self.cloud_valuation_get( 60, rev=True, multiple=40))} |
        | margin | 30 | {fi(self.cloud_valuation_get( 60, rev=False, multiple=30))} |
        | margin | 40 | {fi(self.cloud_valuation_get( 60, rev=False, multiple=40))} |
        | margin | 50 | {fi(self.cloud_valuation_get( 60, rev=False, multiple=50))} |
        | margin | 60 | {fi(self.cloud_valuation_get( 60, rev=False, multiple=60))} |

        ![]({self.graph_valuation_png(path=path,rev=True,multiple=[12,20,30,40])} ':size=800x600')        

        ![]({self.graph_valuation_png(path=path,rev=False,multiple=[30,40,50,60])} ':size=800x600')
        
        ### TFT price index

        If the token price would be ```value of the grid / nr of TFT in the network``` then we can calculate an estimate TFT price index.
        Disclaimer, this is by no means a suggestion that the TFT will go to this price, its just a logical index which could indicate a value for the TFT.
        Realize this is just a simulation, and no indication of any future price.

        | valuation mechanism | multiple | TFT Price Index USD |
        | --- | --- | --- |
        | revenue | 12 | {fi(pi[0])} |
        | revenue | 20 | {fi(pi[1])} |
        | revenue | 30 | {fi(pi[2])} |
        | revenue | 40 | {fi(pi[3])} |
        | margin | 30 | {fi(pi[4])} |
        | margin | 40 | {fi(pi[5])} |
        | margin | 50 | {fi(pi[6])} |
        | margin | 60 | {fi(pi[7])} |
        
        ### example detailed calculation for month {month}

        In case the TFT price is auto then it gets calculated with the params as defined below.

        #### revenues with utilization in account

        This does not take token price increase into consideration.

        | | USD |
        | --- | ---: |
        | rev cu                |  {fi(rev_compute)} | 
        | rev su                |  {fi(rev_storage)} | 
        | rev nu                |  {fi(rev_network)} | 
        | rev total             |  {fi(rev_total)} | 

        #### revenues if all resources used

        | | USD |
        | --- | ---: |
        | rev cu                |  {fi(rev_compute_max)} | 
        | rev su                |  {fi(rev_storage_max)} | 
        | rev nu                |  {fi(rev_network_max)} | 
        | rev total             |  {fi(rev_total_max)} | 

        #### costs
        
        | | USD |
        | --- | ---: |
        | cost hardware         |  {fi(cost_hardware)} | 
        | cost power            |  {fi(cost_power)} | 
        | cost maintenance      |  {fi(cost_maintenance)} | 
        | cost rackspace        |  {fi(cost_rackspace)} | 
        | cost network          |  {fi(cost_network)} | 
        | cost total            |  {fi(cost_total)} | 

        #### valuation report

        - valuation based on {nrmonths}  months of {self.config.cloudvaluation.indextype}
        - valuation is {fi(self.cloud_valuation_get(month))}

        """

        #TODO: to be added if ok again
        #        ![]({self.graph_price_index(path=path)} ':size=800x600')


        C =  j.core.tools.text_strip(C)
        if path:
            j.sal.fs.writeFile(f"{path}/tfgrid_valuation.md",C)
        return C

    def price_index_get(self):
        res=[]
        nrtft = self.tft_total(60)
        for m in [12,20,30,40]:
            res.append(self.cloud_valuation_get(60, rev=True, multiple=m))
        for m in [30,40,50,60]:
            res.append(self.cloud_valuation_get(60, rev=False, multiple=m))
        res = [i/nrtft for i in res]
        return res

    def graph_price_index(self,path):
        r=self.price_index_get()
        titles=[]
        titles.append(("revenue",12))
        titles.append(("revenue", 20))
        titles.append(("revenue", 30))
        titles.append(("revenue", 40))
        titles.append(("margin", 30))
        titles.append(("margin", 40))
        titles.append(("margin", 40))
        titles.append(("margin", 60))

        titles2 = [f"{t[0]} {t[1]}" for t in titles]

        title=f"tft_index"
        path2=f"{path}/{title}.png"

        #TODO: need to improve see https://matplotlib.org/3.2.1/gallery/ticks_and_spines/custom_ticker1.html#sphx-glr-gallery-ticks-and-spines-custom-ticker1-py

        with plt.style.context('Solarize_Light2'):
            # fig, ax = plt.subplots()
            # ax.yaxis.set_major_formatter(formatter)
            # j.shell()
            plt.bar(r,max(r))
            # plt.xticks(x, titles2)
            #plt.show()
            # plt.plot(x,y,label="usd")[0]
        plt.title(title.replace("_"," "))
        fig = plt.gcf()
        fig.set_size_inches(10, 7)
        # plt.legend(loc='best')
        #plt.show()
        plt.savefig(path2, dpi=200)
        plt.close()
        return f"{title}.png"

    def utilization_get(self, month):
        utilization = self.rows.utilization.cells[month] / 100
        return utilization

    def cost_rack_unit_get(self, month):
        return self.rows.cost_rack_unit.cells[month]

    def cost_power_kwh_get(self, month):
        return self.rows.cost_power_kwh.cells[month]

    def cost_rack_unit_set(self, environment=None):
        if not environment:
            environment = self.environment
        self._interpolate("cost_rack_unit", "0:%s" % environment.params.cost_rack_unit)

    def cost_power_kwh_set(self, environment=None):
        if not environment:
            environment = self.environment
        self._interpolate("cost_power_kwh", "0:%s" % environment.params.cost_power_kwh)

    def nodesbatch_get(self, nr):
        return self.nodebatches[nr]

    def nodesbatch_simulate(self, month=1, hardware_config_name=None, environment=None, nrnodes=None):
        if hardware_config_name:
            environment = j.tools.tfgrid_simulator.environment_get(hardware_config_name)
        if not environment:
            environment = self.environment
        name = f"nodesbatch_simulate_{environment.name}_{month}"
        if not nrnodes:
            nrnodes = environment.layout.nr_devices_production
        if not environment._calcdone:
            environment.calc()
        nb = NodesBatch(simulation=self, name=name, environment=environment, nrnodes=nrnodes, month_start=month)
        nb.calc()
        return nb

    def graph_nodesbatches_usd_simulation(self):
        import plotly.graph_objects as go

        fig = go.FigureWidget()
        for i in [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            nb = self.nodesbatch_get(i)
            x, name, values, row = nb._values_usd_get(names=["farmer_income_cumul"], single=True)[0]
            values = [i / float(nb.node_normalized.total.cost_hardware) for i in values]
            fig.add_trace(go.Scatter(x=x, y=values, name="batch_%s" % i, connectgaps=False))
        fig.update_layout(title="Return on investment per node over months.", showlegend=True)

        return fig

    def graph_tft_simulation(self, show=True):
        import plotly.graph_objects as go

        x = [i for i in range(1, 61)]

        fig_nrnodes = go.FigureWidget()
        fig_nrnodes.add_trace(
            go.Scatter(x=x, y=self.rows.nrnodes_total.values_all[0:60], name="nrnodes_total", connectgaps=False)
        )
        fig_nrnodes.add_trace(
            go.Scatter(x=x, y=self.rows.nrnodes_new.values_all[0:60], name="nrnodes_new", connectgaps=False)
        )
        fig_nrnodes.update_layout(title="Nr Nodes.", showlegend=True)
        if show:
            fig_nrnodes.show()

        fig_tft_movement = go.FigureWidget()
        fig_tft_movement.add_trace(
            go.Scatter(x=x, y=self.rows.tft_farmed.values_all[0:60], name="tft_farmed", connectgaps=False)
        )
        fig_tft_movement.add_trace(
            go.Scatter(x=x, y=self.rows.tft_cultivated.values_all[0:60], name="tft_cultivated", connectgaps=False)
        )
        fig_tft_movement.add_trace(
            go.Scatter(x=x, y=self.rows.tft_sold.values_all[0:60], name="tft_sold", connectgaps=False)
        )
        fig_tft_movement.add_trace(
            go.Scatter(x=x, y=self.rows.tft_burned.values_all[0:60], name="tft_burned", connectgaps=False)
        )
        fig_tft_movement.update_layout(title="TFT Movement per Month", showlegend=True)
        if show:
            fig_tft_movement.show()

        y = self.rows.tft_farmed_cumul.values_all[0:60]
        fig_nrtokens = go.FigureWidget()
        fig_nrtokens.add_trace(go.Scatter(x=x, y=y, name="tft_farmed_cumul", connectgaps=False))
        fig_nrtokens.update_layout(title="TFT Total Tokens Evolution (Farmed Total)", showlegend=True)
        if show:
            fig_nrtokens.show()

        row = self.rows.grid_valuation_usd
        fig_grid_valuation = go.FigureWidget()
        fig_grid_valuation.add_trace(
            go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="USD", connectgaps=False)
        )
        fig_grid_valuation.update_layout(title="GRID valuation.", showlegend=True)
        if show:
            fig_grid_valuation.show()

        row = self.rows.tft_marketcap
        fig_tft_marketcap = go.FigureWidget()
        fig_tft_marketcap.add_trace(
            go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="tft_marketcap", connectgaps=False)
        )
        fig_tft_marketcap.update_layout(title="TFT Market Cap (nrTFT X valueTFT).", showlegend=True)
        if show:
            fig_tft_marketcap.show()

        return (fig_nrnodes, fig_tft_movement, fig_nrtokens, fig_grid_valuation, fig_tft_marketcap)

    def graph_token_price_png(self,path):
        title=f"tokenprice"
        path2=f"{path}/{title}.png"
        with plt.style.context('Solarize_Light2'):
            x, y = self.rows.tokenprice.values_xy
            plt.plot(x,y,label="usd")[0]
        plt.title(title.replace("_"," "))
        fig = plt.gcf()
        fig.set_size_inches(10, 7)
        plt.legend(loc='best')
        #plt.show()
        plt.savefig(path2, dpi=200)
        plt.close()
        return f"{title}.png"

    def graph_valuation_png(self,path, rev=True, multiple=None):
        if not multiple:
            multiple = [30, 40, 50]
        if rev:
            title=f"TF Grid valuation based on recurring rev"
            title2 = f"tfgridvaluation_recurring_revenue"
        else:
            title = f"TF Grid valuation based on recurring net margin"
            title2=f"tfgridvaluation_recurring_margin"
        path2=f"{path}/{title2}.png"
        with plt.style.context('Solarize_Light2'):
            for m in multiple:
                if rev:
                    label = f"rev x {m} in million USD"
                else:
                    label = f"margin x {m} in million USD"
                y=self.grid_valuation_values(rev=rev,multiple=m)
                x=[i for i in range(24,60)]
                plt.plot(x,y,label=label)[0]
        plt.title(title.replace("_"," "))
        fig = plt.gcf()
        fig.set_size_inches(10, 7)
        plt.legend(loc='best')
        #plt.show()
        plt.savefig(path2, dpi=200)
        plt.close()
        return f"{title2}.png"

    def markdown_reality_check(self, month):
        cl = j.data.types.numeric.clean
        fi = j.core.text.format_item
        nrnodes = self.rows.nrnodes_total.cells[month]
        tft_cultivated = cl(self.rows.tft_cultivated.cells[month])
        tft_price = self.tft_price_get(month)
        usd_cultivated = cl(tft_cultivated * tft_price)
        usd_node_cultivated = cl(usd_cultivated / nrnodes)
        usd_farmed = cl(self.rows.tft_farmed.cells[month] * tft_price)
        usd_sold = cl(self.rows.tft_sold.cells[month] * tft_price)
        usd_burned = cl(self.rows.tft_burned.cells[month] * tft_price)
        usd_total = cl(self.rows.tft_farmer_income.cells[month] * tft_price)
        n = self.environment.node_normalized

        cpr_improve = self.rows.cpr_improve.cells[month]
        utilization = self.utilization_get(month)

        cu = n.production.cu * (1 + cpr_improve)
        su = n.production.su * (1 + cpr_improve)
        # no improvement on nu because we kept it same
        nu = float(n.production.nu_used_month)

        price_decline = self.sales_price_decline_get(month)  # 0-1

        cu_price = self.sales_price_cu / (1 + price_decline)
        su_price = self.sales_price_su / (1 + price_decline)
        # for nu no price decline because we also did not let the cost go down
        nu_price = self.sales_price_nu

        cost_node_all_nohw = float((self.rows.cost_total.cells[month] - self.rows.cost_hardware.cells[month]) / nrnodes)

        res = f"""
        ## Some Totals for the simulation: ({month} month mark)

        - nrnodes: {nrnodes}
        - nrtokens cultivated: {tft_cultivated}
        - tft price: {tft_price} USD
        - USD cultivated in that month: {usd_cultivated} USD
        - USD farmed in that month: {usd_farmed} USD

        ### simulation params in this month

        - utilization           : {fi(utilization)}
        - price decline         : {fi(price_decline)}
        - cu price              : {fi(cu_price)}
        - su price              : {fi(su_price)}
        - nu price              : {fi(nu_price)}

        ### cloud units sold total

        - #cu        : {fi(cu*nrnodes*utilization)}
        - #su        : {fi(su*nrnodes*utilization)}
        - #nu        : {fi(nu*nrnodes*utilization)}

        ### per node production

        #### per node setup

        - USD investment cost per node: {fi(n.total.cost_hardware)}

        #### cloud units per node

        - #cu               : {fi(cu)}
        - #su               : {fi(su)}
        - #nu               : {fi(nu)}
        - cost of 1 nu      : {fi(n.production.cost_nu_month/nu)}
        - passmark per cu   : {fi(n.production.cu_passmark)}

        #### resource units per node

        - cpr : {fi(n.production.cpr)}
        - cru : {fi(n.production.cru)}
        - sru : {fi(n.production.sru)}
        - hru : {fi(n.production.hru)}
        - mru : {fi(n.production.mru)}

        #### revenue per month per node based on simulation totals

        - rev compute month         : {fi(self.rows.rev_compute.cells[month]/nrnodes)}
        - rev storage month         : {fi(self.rows.rev_storage.cells[month]/nrnodes)}
        - rev network month         : {fi(self.rows.rev_network.cells[month]/nrnodes)}
        - rev total month           : {fi(self.rows.rev_total.cells[month]/nrnodes)}

        #### costs per month per node normalized over months

        - cost hardware month       : {fi(n.total.cost_hardware_month)}
        - cost rack month           : {fi(n.total.cost_rack_month)}
        - cost power month          : {fi(n.total.cost_power_month*utilization)}
        - cost maintenance month    : {fi(n.total.cost_maintenance_month)}
        - cost network month        : {fi(n.production.cost_nu_month*utilization)}

        #### costs per month per node based on simulation totals

        - cost hardware month       : {fi(self.rows.cost_hardware.cells[month]/nrnodes)}
        - cost rack month           : {fi(self.rows.cost_rackspace.cells[month]/nrnodes)}
        - cost power month          : {fi(self.rows.cost_power.cells[month]/nrnodes)}
        - cost maintenance month    : {fi(self.rows.cost_maintenance.cells[month]/nrnodes)}
        - cost network month        : {fi(self.rows.cost_network.cells[month]/nrnodes)}
        - cost total month          : {fi(self.rows.cost_total.cells[month]/nrnodes)}
        - cost total month no hw    : {fi(cost_node_all_nohw)}
        
        ### per node per month

        - USD cultivated per node                                   :  {usd_node_cultivated} USD
        - USD farmed per node                                       :  {fi(usd_farmed / nrnodes)} USD    
        - USD burned per node                                       :  {fi(usd_burned / nrnodes)} USD
        - USD monthly tft sold (rackspace/power/mgmt/net)           :  {fi(-usd_sold / nrnodes)} USD  
        - USD monthly cost per node (rackspace/power/mgmt/net)      :  {fi(cost_node_all_nohw )} USD
        - USD profit for farmer per node (profit from token income) :  {fi(usd_total / nrnodes)} USD

        """
        # print(j.core.tools.text_strip(res))

        return j.core.tools.text_strip(res)

    def graph_token_price(self, graph=True):
        x = [i for i in range(60)]
        cells = self.rows.tokenprice.cells[0:60]
        y = [round(i, 2) for i in cells]

        if graph:
            import plotly.graph_objects as go

            fig = go.FigureWidget(data=go.Scatter(x=x, y=y))
            fig.update_layout(title="Token Price (TFT).", showlegend=False)
            return fig
        else:
            return (x, y)

    def graph_nr_nodes(self):
        x = [i for i in range(60)]
        import plotly.graph_objects as go

        fig = go.FigureWidget()
        fig.add_trace(go.Scatter(x=x, y=self.sheet.rows.nrnodes_new.cells[0:60], name="new nodes"))
        fig.add_trace(go.Scatter(x=x, y=self.rows.nrnodes_total.cells[0:60], name="total nr nodes"))
        fig.update_layout(title="New/Total nr Nodes per Month", showlegend=True)
        return fig

    def __repr__(self):
        out = str(SimulatorBase.__repr__(self))
        out += "\n"
        out += self.sheet.text_formatted(period="B", aggregate_type=None, exclude=None)
        # out += " - %-20s %s\n" % ("tft_sum", int(self.tft_sum))
        return out

    __str__ = __repr__
