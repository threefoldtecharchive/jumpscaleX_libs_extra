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
        cpr_sum = 0.0 (F)
        tft_sum = 0.0 (F)
        simulated = false (B)        
        """

    def _init(self, **kwargs):
        self.sheet = j.data.worksheets.sheet_new("simulation", nrcols=120)
        self.rows = self.sheet.rows
        self.nodebatches = []  # 0 is the first batch, which stands for month 1
        self.bom = BillOfMaterial(name="main")
        self.environment = Environment(name="default")
        self.token_creator = TokenCreator()

    def device_get(self, name, device_template_name=None, description="", environment=None):
        return self.bom.device_get(
            name=name, device_template_name=device_template_name, description=description, environment=environment
        )

    def nodesbatch_start_set(self, nrnodes=1500, months_left=36, tft_farmed_before_simulation=0):
        nb = self._nodesbatch_add(month=0, nrnodes=nrnodes)
        nb.tft_farmed_before_simulation = tft_farmed_before_simulation
        nb.months_left = months_left
        return nb

    def _nodesbatch_add(self, month, nrnodes):
        nb = NodesBatch(name="default", simulation=self, nrnodes=nrnodes, month_start=month)
        while len(self.nodebatches) < month + 1:
            self.nodebatches.append(None)
        self.nodebatches[month] = nb
        return self.nodebatches[month]

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
        # need to do over 12 years or the price of tokens weirdly stops
        val = (val - 0.15) * 2
        self.tokenprice_set("0:0.15,119:%s" % val)

    def tokenprice_set(self, args):
        """
        define how tokenprice goes up (in $)
        :param args:
        :return:
        """
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
        r = self.sheet.rows.tokenprice.cells[month]
        assert r > 0
        return r

    def tft_total(self, month=None):
        """
        amounts of tft in the blockchain
        total nr of tft
        """
        if month == None:
            month = self.sheet.nrcols - 1
        tft_total = int(self.rows.tft_farmed_cumul.cells[month])
        if month == 0:
            tft_total += int(self.nodesbatch_get(0).tft_farmed_before_simulation)
        return tft_total

    def _row_add(self, name, aggregate="FIRST", ttype="int", defval=0, empty=True, clean=True):
        row = self.sheet.addRow(name, aggregate=aggregate, ttype=ttype, empty=empty, nrcols=120, defval=defval)
        if clean:
            row.clean()
        return row

    def _prepare(self):
        if not "cost_rack_unit" in self.rows:
            self._interpolate("cost_rack_unit", "0:%s" % self.environment.cost_rack_unit)
            self._interpolate("cost_power_kwh", "0:%s" % self.environment.cost_power_kwh)
            self._row_add("nrnodes_total")

            self._row_add("tft_farmed")
            self._row_add("tft_farmed_cumul")
            self._row_add("tft_cultivated")
            # sold tft to cover power & rackspace costs
            self._row_add("tft_sold")
            self._row_add("tft_burned")
            self._row_add("tft_farmer_income")
            self._row_add("tft_cumul")

            self._row_add("cost_rackspace")
            self._row_add("cost_power")
            self._row_add("cost_hardware")
            self._row_add("cost_maintenance")
            self._row_add("rackspace_u", ttype="float")
            self._row_add("power_kw", ttype="float")

            self._row_add("investment", defval=0)
            self._row_add("revenue")

            self._row_add("tft_movement_value_usd")
            self._row_add("tft_cumul_value_usd")  # What is cumul = cumulative (all aggregated)
            self._row_add("tft_marketcap")

    def _float(self, val):
        if val == None:
            return 0.0
        return float(val)

    def calc(self):

        if self.simulated:
            raise j.exceptions.Input("cannot call this method twice: calc")

        self._prepare()

        # calculate growth in nr nodes
        for month_now in range(0, 120):
            if month_now > 0:
                nr_new = self.rows.nrnodes_new.cells[month_now]
                if nr_new > 0:
                    self._nodesbatch_add(month=month_now, nrnodes=nr_new)
                    self.rows.nrnodes_total.cells[month_now] = (
                        self.rows.nrnodes_total.cells[month_now - 1] + self.rows.nrnodes_new.cells[month_now]
                    )
            else:
                self.rows.nrnodes_total.cells[month_now] = self.nodebatches[0].nrnodes

        self.rows.nrnodes_new.clean()  # makes sure we get nicely formatted cells (int)
        self.rows.nrnodes_total.clean()

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
                self.rows.tft_cumul.cells[month] += self._float(nb.rows.tft_cumul.cells[month]) - self._float(
                    nb.rows.tft_burned.cells[month]
                )

                self.rows.tft_movement_value_usd.cells[month] += self._float(
                    nb.rows.tft_movement_value_usd.cells[month]
                )
                self.rows.tft_cumul_value_usd.cells[month] += self._float(nb.rows.tft_cumul_value_usd.cells[month])

                self.rows.cost_rackspace.cells[month] += self._float(nb.rows.cost_rackspace.cells[month])
                self.rows.cost_power.cells[month] += self._float(nb.rows.cost_power.cells[month])
                self.rows.cost_hardware.cells[month] += self._float(nb.rows.cost_hardware.cells[month])
                self.rows.cost_maintenance.cells[month] += self._float(nb.rows.cost_maintenance.cells[month])

                self.rows.investment.cells[month] += self._float(nb.cost_hardware)

            self.rows.tft_movement_value_usd.cells[month] = tftprice_now * self.rows.tft_farmer_income.cells[month]
            self.rows.tft_cumul_value_usd.cells[month] = tftprice_now * self.rows.tft_cumul.cells[month]
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
        self.rows.tft_cumul.clean()

        row = self._row_add("grid_valuation_rev_musd", aggregate="FIRST", ttype="int", defval=0, empty=True, clean=True)
        row = self._row_add(
            "tft_calculated_based_rev_valuation", aggregate="FIRST", ttype="float", defval=0, empty=True, clean=True
        )

        def do(val, x, args):
            rev_over_years = self.revenue_grid_max_get(x) * 60
            tft_cumul = float(self.rows.tft_farmed_cumul.cells[x])
            tft_cumul_usd = tft_cumul * self.tft_price_get(x)
            self.rows.tft_calculated_based_rev_valuation.cells[x] = rev_over_years / tft_cumul_usd
            rev_over_years = rev_over_years
            return rev_over_years

        self.rows.grid_valuation_rev_musd.function_apply(do)

        row = self._row_add(
            "grid_valuation_margin_musd", aggregate="FIRST", ttype="int", defval=0, empty=True, clean=True
        )
        row = self._row_add(
            "tft_calculated_based_margin_valuation", aggregate="FIRST", ttype="float", defval=0, empty=True, clean=True
        )

        def do(val, x, args):
            marginoveryears = self.margin_grid_max_get(x) * 12 * 10
            tft_cumul = float(self.rows.tft_farmed_cumul.cells[x])
            tft_cumul_usd = tft_cumul * self.tft_price_get(x)
            self.rows.tft_calculated_based_margin_valuation.cells[x] = marginoveryears / tft_cumul_usd
            marginoveryears = marginoveryears
            return marginoveryears

        self.rows.grid_valuation_margin_musd.function_apply(do)

    def revenue_grid_max_get(self, x):
        """
        is the max revenue the grid can do at that time
        """
        device = self.environment.device_normalized
        cpr_usd = self.cpr_sales_price_get(x)
        nrnodes = self.rows.nrnodes_total.cells[x]
        rev = float(device.cpr) * float(nrnodes) * float(cpr_usd)
        return rev

    def cost_grid_max_get(self, x):
        """
        is the max cost of the grid (at full utilization)
        for power, rackspace & manpower (maintenance)
        """
        device = self.environment.device_normalized
        nrnodes = self.rows.nrnodes_total.cells[x]
        cost = float(device.cost_month) * float(nrnodes)
        return cost

    def margin_grid_max_get(self, x):
        """
        is the max revenue the grid can do at that time
        """
        return self.revenue_grid_max_get(x) - self.cost_grid_max_get(x)

    def utilization_get(self, month):
        utilization = self.rows.utilization.cells[month] / 100
        return utilization

    def cpr_sales_price_get(self, month):
        """
        sales price per cpr per month (cloud production rate)
        """
        cpr_sales_price_decline = self.rows.cpr_sales_price_decline.cells[month]
        cpr_sales_price_decline = self._float(cpr_sales_price_decline / 100)
        sales_price_cpr_unit_month = self.environment.sales_price_cpr_unit * (1 - cpr_sales_price_decline)
        return sales_price_cpr_unit_month

    def cost_rack_unit_get(self, month):
        return self.rows.cost_rack_unit.cells[month]

    def cost_power_kwh_get(self, month):
        return self.rows.cost_power_kwh.cells[month]

    def nodesbatch_get(self, nr):
        return self.nodebatches[nr]

    def graph_nodesbatches_usd_simulation(self):
        import plotly.graph_objects as go

        fig = go.Figure()
        for i in [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            nb = self.nodesbatch_get(i)
            x, name, values, row = nb._values_usd_get(names=["cumul"], single=True)[0]
            fig.add_trace(go.Scatter(x=x, y=values, name="batch_%s" % i, connectgaps=False))
        fig.update_layout(title="USD generation per node.", showlegend=True)
        fig.show()
        return fig

    def graph_tft_simulation(self, show=True):
        import plotly.graph_objects as go

        x = [i for i in range(1, 61)]

        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(x=x, y=self.rows.nrnodes_total.values_all[0:60], name="nrnodes_total", connectgaps=False)
        )
        fig1.add_trace(go.Scatter(x=x, y=self.rows.nrnodes_new.values_all[0:60], name="nrnodes_new", connectgaps=False))
        fig1.update_layout(title="Nr Nodes.", showlegend=True)
        if show:
            fig1.show()

        fig2 = go.Figure()
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
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=x, y=y, name="tft_farmed_cumul", connectgaps=False))
        fig3.update_layout(title="TFT Total Tokens Evolution (Farmed Total)", showlegend=True)
        if show:
            fig3.show()

        row = self.rows.grid_valuation_rev_musd
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="USD", connectgaps=False))
        fig4.update_layout(title="GRID valuation based on 5Y recurring revenue capability of grid", showlegend=True)
        if show:
            fig4.show()

        row = self.rows.tft_calculated_based_rev_valuation
        fig5 = go.Figure()
        fig5.add_trace(
            go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="multiple", connectgaps=False)
        )
        fig5.update_layout(
            title="tft value index based on grid revenue valuation = multiple (grid more than TFT)", showlegend=True
        )
        if show:
            fig5.show()

        row = self.rows.grid_valuation_margin_musd
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="USD", connectgaps=False))
        fig6.update_layout(title="GRID valuation based on 10x yearly net profit of grid (all farmers)", showlegend=True)
        if show:
            fig6.show()

        row = self.rows.tft_calculated_based_margin_valuation
        fig7 = go.Figure()
        fig7.add_trace(
            go.Scatter(x=[i for i in range(20, 60)], y=row.values_all[20:60], name="multiple", connectgaps=False)
        )
        fig7.update_layout(
            title="tft value index based on grid margin valuation =multiple (grid more than TFT)", showlegend=True
        )
        if show:
            fig7.show()

        row = self.rows.tft_marketcap
        fig8 = go.Figure()
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

    def graph_token_price(self):
        import plotly.graph_objects as go

        x = [i for i in range(60)]
        cells = [i / 44 for i in self.sheet.rows.rackspace_u.cells[0:60]]
        cells = self.rows.tokenprice.cells[0:60]
        y = [round(i, 2) for i in cells]
        fig = go.Figure(data=go.Scatter(x=x, y=y))
        fig.update_layout(title="Token Price (TFT).", showlegend=False)
        fig.show()

    def __repr__(self):
        out = ""
        for key in self.sheet.rows.keys():
            row = self.sheet.rows[key]
            if row.cells[1] and row.cells[1] < 3:
                res = row.aggregate("Q", roundnr=2)
            else:
                res = row.aggregate("Q", roundnr=0)
            res = [str(i) for i in res]
            res2 = ", ".join(res)
            out += " - %-20s %s\n" % (key, res2)

        out += " - %-20s %s\n" % ("tft_sum", int(self.tft_sum))
        return out

    __str__ = __repr__
