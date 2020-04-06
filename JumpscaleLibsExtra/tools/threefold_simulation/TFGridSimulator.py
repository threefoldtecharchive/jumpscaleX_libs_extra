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
        sales_price_cu = (N)
        sales_price_su = (N)
        sales_price_nu = (N)                
        """

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

    def tokenprice_set_5years(self, val=3):
        if isinstance(val, str) and val.startswith("auto"):
            self.tokenprice_set("0:0.15,24:0.4")
            self._tft_in_relation_to_grid_value = int(val.replace("auto", ""))
            assert self._tft_in_relation_to_grid_value > 10
            assert self._tft_in_relation_to_grid_value < 400
            return
        else:
            self._tft_in_relation_to_grid_value = None
        # need to do over 12 years or the price of tokens weirdly stops
        val = (val - 0.15) * 2 + 0.15
        self.tokenprice_set("0:0.15,119:%s" % val)

    def tokenprice_set(self, args):
        """
        define how tokenprice goes up (in $)
        :param args:
        :return:
        """
        if isinstance(args, int) or isinstance(args, float) or args.startswith("auto"):
            self.tokenprice_set_5years(args)
        else:
            self._tft_in_relation_to_grid_value = None
            self._interpolate("tokenprice", args)

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

    def tft_price_get(self, month=None):
        if month == None:
            month = self.sheet.nrcols - 1
        if self._tft_in_relation_to_grid_value:
            r = self.sheet.rows.tokenprice.cells[month]
            if month > 6:

                revenue = self.rows.revenue.cells[month - 1]

                cost_rackspace = self.rows.cost_rackspace.cells[month - 1]
                cost_power = self.rows.cost_power.cells[month - 1]
                cost_hardware = self.rows.cost_hardware.cells[month - 1]
                cost_maintenance = self.rows.cost_maintenance.cells[month - 1]
                cost = cost_rackspace + cost_power + cost_hardware + cost_maintenance
                margin = revenue - cost
                gridval_margin = margin * 12 * 10  # 10 year margin

                n = self.environment.node_normalized
                cpr_price = self.environment.sales_price_cpr_unit_get(self, month)
                nrnodes = self.rows.nrnodes_total.cells[month - 1]
                gridval_capability = (
                    float(n.cpr) * float(nrnodes) * float(cpr_price) * 60
                )  # 4 year recurring rev capability

                gridval = revenue * 12 * 5

                nrtokens = self.sheet.rows.tft_farmed_cumul.cells[month - 1]
                if gridval_margin > gridval:
                    gridval = gridval_margin
                if gridval_capability > gridval:
                    gridval = gridval_capability

                tft_price_grid_val = gridval / nrtokens
                tft_price_prev = self.sheet.rows.tokenprice.cells[month - 1]
                marketcap = nrtokens * tft_price_prev
                b = self._tft_in_relation_to_grid_value / 100
                if tft_price_grid_val * b > r:
                    self.sheet.rows.tokenprice.cells[month] = tft_price_grid_val
                    r = self.sheet.rows.tokenprice.cells[month]
        else:
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
        # if month == 0:
        #     tft_total += int(self.nodesbatch_get(0).tft_farmed_before_simulation)
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

        row = self._row_add("grid_valuation_rev_usd", aggregate="FIRST", ttype="int", defval=0, empty=True, clean=True)
        row = self._row_add(
            "tft_calculated_based_rev_valuation", aggregate="FIRST", ttype="float", defval=0, empty=True, clean=True
        )

        def do(val, x, args):
            rev_over_years = self.revenue_grid_max_get(environment=environment, x=x) * 60
            tft_farmer_income_cumul = float(self.rows.tft_farmed_cumul.cells[x])
            tft_farmer_income_cumul_usd = tft_farmer_income_cumul * self.tft_price_get(x)
            self.rows.tft_calculated_based_rev_valuation.cells[x] = rev_over_years / tft_farmer_income_cumul_usd
            rev_over_years = rev_over_years
            return rev_over_years

        self.rows.grid_valuation_rev_usd.function_apply(do)

        row = self._row_add(
            "grid_valuation_margin_usd", aggregate="FIRST", ttype="int", defval=0, empty=True, clean=True
        )
        row = self._row_add(
            "tft_calculated_based_margin_valuation", aggregate="FIRST", ttype="float", defval=0, empty=True, clean=True
        )

        def do(val, x, args):
            marginoveryears = self.margin_grid_max_get(environment=environment, x=x) * 12 * 10
            tft_farmer_income_cumul = float(self.rows.tft_farmed_cumul.cells[x])
            tft_farmer_income_cumul_usd = tft_farmer_income_cumul * self.tft_price_get(x)
            self.rows.tft_calculated_based_margin_valuation.cells[x] = marginoveryears / tft_farmer_income_cumul_usd
            marginoveryears = marginoveryears
            return marginoveryears

        self.rows.grid_valuation_margin_usd.function_apply(do)

    def revenue_grid_max_get(self, x, environment=None):
        """
        is the max revenue the grid can do at that time
        """
        if not environment:
            environment = self.environment
        device = environment.node_normalized
        cpr_usd = environment.sales_price_cpr_unit_get(self, x)
        nrnodes = self.rows.nrnodes_total.cells[x]
        # 10% less than max
        rev = float(device.cpr) * float(nrnodes) * float(cpr_usd) * 0.9
        return rev

    def cost_grid_max_get(self, x, environment=None):
        """
        is the max cost of the grid (at full utilization)
        for power, rackspace & manpower (maintenance)
        """
        if not environment:
            environment = self.environment
        device = environment.node_normalized
        nrnodes = self.rows.nrnodes_total.cells[x]
        cost = float(device.cost_month) * float(nrnodes)
        return cost

    def margin_grid_max_get(self, x, environment=None):
        """
        is the max revenue the grid can do at that time
        """
        if not environment:
            environment = self.environment
        return self.revenue_grid_max_get(environment=environment, x=x) - self.cost_grid_max_get(
            environment=environment, x=x
        )

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

        fig1 = go.FigureWidget()
        fig1.add_trace(
            go.Scatter(x=x, y=self.rows.nrnodes_total.values_all[0:60], name="nrnodes_total", connectgaps=False)
        )
        fig1.add_trace(go.Scatter(x=x, y=self.rows.nrnodes_new.values_all[0:60], name="nrnodes_new", connectgaps=False))
        fig1.update_layout(title="Nr Nodes.", showlegend=True)
        if show:
            fig1.show()

        fig2 = go.FigureWidget()
        fig2.add_trace(go.Scatter(x=x, y=self.rows.tft_farmed.values_all[0:60], name="tft_farmed", connectgaps=False))
        fig2.add_trace(
            go.Scatter(x=x, y=self.rows.tft_cultivated.values_all[0:60], name="tft_cultivated", connectgaps=False)
        )
        fig2.add_trace(go.Scatter(x=x, y=self.rows.tft_sold.values_all[0:60], name="tft_sold", connectgaps=False))
        fig2.add_trace(go.Scatter(x=x, y=self.rows.tft_burned.values_all[0:60], name="tft_burned", connectgaps=False))
        fig2.update_layout(title="TFT Movement per Month", showlegend=True)
        if show:
            fig2.show()

        y = self.rows.tft_farmed_cumul.values_all[0:60]
        fig3 = go.FigureWidget()
        fig3.add_trace(go.Scatter(x=x, y=y, name="tft_farmed_cumul", connectgaps=False))
        fig3.update_layout(title="TFT Total Tokens Evolution (Farmed Total)", showlegend=True)
        if show:
            fig3.show()

        row = self.rows.grid_valuation_rev_usd
        fig4 = go.FigureWidget()
        fig4.add_trace(go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="USD", connectgaps=False))
        fig4.update_layout(title="GRID valuation based on 5Y recurring revenue capability of grid", showlegend=True)
        if show:
            fig4.show()

        row = self.rows.tft_calculated_based_rev_valuation
        fig5 = go.FigureWidget()
        fig5.add_trace(
            go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="multiple", connectgaps=False)
        )
        fig5.update_layout(
            title="tft value index based on grid revenue valuation = multiple (grid more than TFT)", showlegend=True
        )
        if show:
            fig5.show()

        row = self.rows.grid_valuation_margin_usd
        fig6 = go.FigureWidget()
        fig6.add_trace(go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="USD", connectgaps=False))
        fig6.update_layout(title="GRID valuation based on 10x yearly net profit of grid (all farmers)", showlegend=True)
        if show:
            fig6.show()

        row = self.rows.tft_calculated_based_margin_valuation
        fig7 = go.FigureWidget()
        fig7.add_trace(
            go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="multiple", connectgaps=False)
        )
        fig7.update_layout(
            title="tft value index based on grid margin valuation =multiple (grid more than TFT)", showlegend=True
        )
        if show:
            fig7.show()

        row = self.rows.tft_marketcap
        fig8 = go.FigureWidget()
        fig8.add_trace(
            go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="tft_marketcap", connectgaps=False)
        )
        fig8.update_layout(title="TFT Market Cap (nrTFT X valueTFT)", showlegend=True)
        if show:
            fig8.show()

        return (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8)

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
        #
        #
        # def __repr__(self):
        #     out = ""
        #     for key in self.sheet.rows.keys():
        #         row = self.sheet.rows[key]
        #         if row.cells[1] and row.cells[1] < 3:
        #             res = row.aggregate("Q", roundnr=2)
        #         else:
        #             res = row.aggregate("Q", roundnr=0)
        #         res = [str(i) for i in res]
        #         res2 = ", ".join(res)
        #         out += " - %-20s %s\n" % (key, res2)

    __str__ = __repr__
