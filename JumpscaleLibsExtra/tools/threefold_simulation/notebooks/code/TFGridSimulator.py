from Jumpscale import j

from .BillOfMaterial import *
from .NodesBatch import *
from .SimulatorBase import SimulatorBase


class TokenCreator:
    pass


class TFGridSimulator(SimulatorBase):

    _SCHEMATEXT = """
        @url = threefold.simulation
        name = ""
        # cpr_sum = 0.0 (F)
        # tft_sum = 0.0 (F)
        simulated = false (B)               
        """

    @property
    def sales_price_cu(self):
        return self.config.price_cu

    @property
    def sales_price_su(self):
        return self.config.price_su

    @property
    def sales_price_nu(self):
        return self.config.price_nu

    def export_(self):
        r = {}
        r["sheet"] = self.sheet.export_()
        r["data"] = self._data._ddict
        r["nodebatches"] = [i.export_() for i in self.nodebatches]
        return r

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
        assert environment.nr_devices > 0
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

    def cpr_sales_price_decline_set(self, args):
        """
        The salesprice will decline over time

        args e.g. 72:40
        means over 72 months 40% off of the cpr
        :param args:
        :return:
        """
        self._interpolate("cpr_sales_price_decline", args)

    def cpr_sales_price_decline_get(self, month):
        """
        return 0->40
        40 means price declide of 40%
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
            tft_price_5y = config.cloudindex.tft_price_5y_baseline
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
        return self.cloud_index_get(x=month)

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
            self._row_add("rackspace_u", ttype="float")
            self._row_add("power_kw", ttype="float")

            self._row_add("investment", defval=0)
            self._row_add("revenue")

            self._row_add("tft_movement_usd")
            self._row_add("tft_farmer_income_cumul_usd")  # What is cumul = cumulative (all aggregated)
            self._row_add("tft_marketcap")

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

                self.rows.tft_movement_usd.cells[month] += self._float(nb.rows.tft_movement_usd.cells[month])
                self.rows.tft_farmer_income_cumul_usd.cells[month] += self._float(
                    nb.rows.tft_farmer_income_cumul_usd.cells[month]
                )

                self.rows.cost_rackspace.cells[month] += self._float(nb.rows.cost_rackspace.cells[month])
                self.rows.cost_power.cells[month] += self._float(nb.rows.cost_power.cells[month])
                self.rows.cost_hardware.cells[month] += self._float(nb.rows.cost_hardware.cells[month])
                self.rows.cost_maintenance.cells[month] += self._float(nb.rows.cost_maintenance.cells[month])

                self.rows.investment.cells[month] += self._float(nb.cost_hardware)

            self.rows.tft_movement_usd.cells[month] = tftprice_now * self.rows.tft_farmer_income.cells[month]
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

        self._grid_valuation_calc()

    def _grid_valuation_calc(self):

        row = self._row_add("grid_valuation_usd", aggregate="FIRST", ttype="int", defval=0, empty=True, clean=True)

        def do(val, x, args):
            return self.cloud_index_get(x)

        row.function_apply(do)

    def sales_price_cpr_unit_get(self, month=0, forindex=True):
        node = self.environment.node_normalized
        cpr_sales_price_decline = self.cpr_sales_price_decline_get(month)
        if forindex:
            pricegetter = j.tools.tfgrid_simulator.simulator_config.cloudindex
        else:
            pricegetter = j.tools.tfgrid_simulator.simulator_config.pricing
        sales_price_total = (
            pricegetter.price_cu * node.cu + pricegetter.price_su * node.su + pricegetter.price_nu * node.nu
        )
        sales_price_cpr_unit = (sales_price_total / node.cpr) / (1 + cpr_sales_price_decline)
        return sales_price_cpr_unit

    def cloud_index_revenue_get(self, x):
        """
        is the max revenue the grid can do at that time (per month)
        using our index calculation
        """
        node = self.environment.node_normalized
        # includes networking
        cpr_usd = self.sales_price_cpr_unit_get(month=x, forindex=True)
        nrnodes = self.rows.nrnodes_total.cells[x]
        rev = float(node.cpr) * float(nrnodes) * float(cpr_usd)
        return rev

    def cloud_index_cost_get(self, x):
        """
        is the max cost of the grid (at full utilization)
        for power, rackspace & hardware (written off over 5 years)
        """
        node = self.environment.node_normalized
        nrnodes = self.rows.nrnodes_total.cells[x]
        cost = float(node.cost_month) * float(nrnodes)
        return cost

    def cloud_index_margin_get(self, x):
        """
        is the max margin the grid can do at that time (per month)
        """
        return self.cloud_index_revenue_get(x=x) - self.cloud_index_cost_get(x=x)

    def cloud_index_get(self, x):
        """
        the value of the grid at that month based on selected cloud index calculation method
        """
        rev = self.cloud_index_revenue_get(x)
        config = j.tools.tfgrid_simulator.simulator_config.cloudindex

        if config.indextype == "revenue":
            rev = int(rev * config.revenue_months)
            return rev
        else:
            cost = self.cloud_index_cost_get(x)
            margin = rev - cost
            margin = int(margin * config.margin_months)
            return margin

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
        self._interpolate("cost_rack_unit", "0:%s" % environment.cost_rack_unit)

    def cost_power_kwh_set(self, environment=None):
        if not environment:
            environment = self.environment
        self._interpolate("cost_power_kwh", "0:%s" % environment.cost_power_kwh)

    def nodesbatch_get(self, nr):
        return self.nodebatches[nr]

    def nodesbatch_simulate(self, month=1, hardware_config_name=None, environment=None, nrnodes=None):
        if hardware_config_name:
            environment = j.tools.tfgrid_simulator.environment_get(hardware_config_name)
        if not environment:
            environment = self.environment
        name = f"nodesbatch_simulate_{environment.name}_{month}"
        if not nrnodes:
            nrnodes = environment.nr_nodes
        nb = NodesBatch(simulation=self, name=name, environment=environment, nrnodes=nrnodes, month_start=month)
        nb.calc()
        return nb

    def graph_nodesbatches_usd_simulation(self):
        import plotly.graph_objects as go

        fig = go.FigureWidget()
        for i in [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            nb = self.nodesbatch_get(i)
            x, name, values, row = nb._values_usd_get(names=["farmer_income_cumul"], single=True)[0]
            values = [i / float(nb.node.cost_hardware) for i in values]
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

    def markdown_reality_check(self, month):
        cl = j.data.types.numeric.clean
        nrnodes = self.rows.nrnodes_total.cells[month]
        tft_cultivated = cl(self.rows.tft_cultivated.cells[month])
        tft_price = self.tft_price_get(month)
        usd_cultivated = cl(tft_cultivated * tft_price)
        usd_node_cultivated = cl(usd_cultivated / nrnodes)
        usd_farmed = cl(self.rows.tft_farmed.cells[month] * tft_price)
        usd_sold = cl(self.rows.tft_sold.cells[month] * tft_price)
        usd_burned = cl(self.rows.tft_burned.cells[month] * tft_price)
        usd_total = cl(self.rows.tft_farmer_income.cells[month] * tft_price)

        res = f"""
        ## Some Checks ({month} month mark)

        - nrnodes: {nrnodes}
        - nrtokens cultivated: {tft_cultivated}
        - tft price: {tft_price} USD
        - USD cultivated in that month: {usd_cultivated} USD
        - USD farmed in that month: {usd_farmed} USD

        ### per node per month

        - USD cultivated per node:  {usd_node_cultivated} USD
        - USD farmed per node:  {cl(usd_farmed / nrnodes)} USD    
        - USD burned per node:  {cl(usd_burned / nrnodes)} USD  
        - USD sold per node (to pay for rackspace/power/mgmt):  {cl(usd_sold / nrnodes)} USD  
        - USD profit for farmer per node (profit from token income):  {cl(usd_total / nrnodes)} USD

        """

        return j.core.tools.text_strip(res)

    def graph_token_price(self, graph=True):
        x = [i for i in range(60)]
        cells = [i / 44 for i in self.sheet.rows.rackspace_u.cells[0:60]]
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
