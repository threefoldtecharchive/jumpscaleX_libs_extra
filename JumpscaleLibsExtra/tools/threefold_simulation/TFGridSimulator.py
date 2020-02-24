from Jumpscale import j

from .BillOfMaterial import *
from .NodesBatch import *
from .SimulatorBase import SimulatorBase
from .TokenCreator import TokenCreator


class SimulationMonth(SimulatorBase):

    _SCHEMATEXT = """
        @url = threefold.simulation.result.month
        revenue = (N)
        investments_done_to_date = (N)
        power_usage_kw =  (I)
        rackspace_usage_u = (I)
        nrnodes_active  = (I)
        cpr_available = (I)

        """


class TFGridSimulator(SimulatorBase):

    _SCHEMATEXT = """
        @url = threefold.simulation
        name = ""
        cpr_sum = 0.0 (F)
        tft_sum = 0.0 (F)
        """

    def _init(self, **kwargs):
        self.sheet = j.data.worksheets.sheet_new("simulation", nrcols=120)
        self.nodebatches = []  # 0 is the first batch, which stands for month 1
        self.bom = BillOfMaterial()
        self.environment = Environment(name="default")
        self.token_creator = TokenCreator(simulator=self)

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
        nb = NodesBatch(simulator=self, nrnodes=nrnodes, month_start=month)
        while len(self.nodebatches) < month + 1:
            self.nodebatches.append(None)
        self.nodebatches[month] = nb
        return self.nodebatches[month]

    def growth_percent_set(self, growth):
        """
        define growth rate
        :param growth:
        :return:
        """
        self._interpolate("growth_percent", growth)

    def cpr_improve_set(self, args):
        """
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
        define how cpr improves
        args is month:improve_in_percent from original
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

    def _interpolate(self, name, args):
        args = [i.strip().split(":") for i in args.split(",") if i.strip()]
        row = self.sheet.addRow(name, nrfloat=2, aggregate="FIRST")
        for x, g in args:
            row.cells[int(x)] = float(g)
        if not row.cells[0]:
            row.cells[0] = 0
        row.interpolate()
        return row

    def growth_perc_get(self, month):
        return self.sheet.rows["growth_percent"].cells[month] / 100

    def tft_price_get(self, month=None):
        if month == None:
            month = self.sheet.nrcols - 1
        return self.sheet.rows["tokenprice"].cells[month]

    def calc(self, nrnodes_new=None):

        self._interpolate("cost_rack_unit", "0:%s" % self.environment.cost_rack_unit)
        self._interpolate("cost_power_kwh", "0:%s" % self.environment.cost_power_kwh)

        if not nrnodes_new:
            nodes_sold = "0:5,6:150,12:1000,13:0"
        row_nrnodes_new = self._interpolate("nrnodes_new", nrnodes_new)
        row_nrnodes_total = self.sheet.addRow("nrnodes", nrfloat=0, aggregate="FIRST")

        row_rev = self.sheet.addRow("revenue_month", aggregate="FIRST")
        row_cost = self.sheet.addRow("cost_month", aggregate="FIRST")
        row_investment = self.sheet.addRow("investment", aggregate="FIRST")
        row_power = self.sheet.addRow("powerkw", aggregate="FIRST")
        row_racks = self.sheet.addRow("nrracks", aggregate="FIRST")
        row_cpr_available = self.sheet.addRow("cpr_available", aggregate="FIRST")
        row_tft_created = self.sheet.addRow("tokens_farmed", aggregate="FIRST")
        row_tft_created = self.sheet.addRow("tokens_farmed_value", aggregate="FIRST")
        row_tft_used = self.sheet.addRow("tokens_used", aggregate="FIRST")
        row_tft_burned = self.sheet.addRow("tokens_burned", aggregate="FIRST")

        # for x in range(0, self.sheet.nrcols):
        #     self.sheet.addRow("tokensbatch_%s_farmed_tft" % x, aggregate="SUM")
        #     self.sheet.addRow("tokensbatch_%s_farmed_predicted_roi" % x, aggregate="AVG")

        for month_now in range(0, 120):
            if month_now > 0:
                if not row_nrnodes_new.cells[month_now]:  # when already set, don't calculate
                    nr_new = (1 + self.growth_perc_get(month_now)) * row_nrnodes_new.cells[month_now - 1]
                    row_nrnodes_new.cells[month_now] = nr_new
                else:
                    nr_new = row_nrnodes_new.cells[month_now]
                self._nodesbatch_add(month=month_now, nrnodes=nr_new)
                row_nrnodes_total.cells[month_now] = (
                    row_nrnodes_total.cells[month_now - 1] + row_nrnodes_new.cells[month_now]
                )
            else:
                row_nrnodes_total.cells[month_now] = row_nrnodes_new.cells[month_now]

        for month_now in range(0, 60):
            nb = self.nodebatches[month_now]
            nb.calc()

        #     r = self.result_get(month_now)
        #     row_rev.cells[month_now] = r.revenue / 1000
        #     row_cost.cells[month_now] = r.cost / 1000
        #     row_investment.cells[month_now] = r.investments_done / 1000
        #     row_power.cells[month_now] = r.power_usage_kw / 1000
        #     row_racks.cells[month_now] = r.rackspace_usage_u / 44
        #     row_cpr_available.cells[month_now] = r.cpr_available
        #
        # self.calculate_farmed_predicted_roi()

    def utilization_get(self, month):
        utilization = self.sheet.rows["utilization"].cells[month] / 100
        return utilization

    def cpr_sales_price_get(self, month):
        """
        sales price per cpr per month (cloud production rate)
        """
        cpr_sales_price_decline = self.sheet.rows["cpr_sales_price_decline"].cells[month]
        cpr_sales_price_decline = float(cpr_sales_price_decline / 100)
        sales_price_cpr_unit_month = self.environment.sales_price_cpr_unit * (1 - cpr_sales_price_decline)
        return sales_price_cpr_unit_month

    def cost_rack_unit_get(self, month):
        return self.sheet.rows["cost_rack_unit"].cells[month]

    def cost_power_kwh_get(self, month):
        return self.sheet.rows["cost_power_kwh"].cells[month]

    def result_get(self, month, utilization=None):
        """

        :param month: 0 is month 1
        :param occupation: in percent
        :return:
        """
        raise
        # if not utilization:
        cpr_sales_price_decline = self.sheet.rows["cpr_sales_price_decline"].cells[month]
        cpr_sales_price_decline = j.data.types.percent.clean(cpr_sales_price_decline)

        sales_price_cpr_unit_month = self.environment.sales_price_cpr_unit * (1 - cpr_sales_price_decline)

        r = self.result_schema.new()
        r.revenue = 0
        r.cost = 0
        r.investments_done = 0
        r.power_usage_kw = 0
        r.rackspace_usage_u = 0
        r.nrnodes_active = 0
        r.cpr_available = 0
        # j.debug()
        for month_batch in range(0, month + 1):
            nodes_batch = self.nodes_batch_get(month_batch)  # go back to when a node batch was added
            if nodes_batch.month < month + 1 and month < (nodes_batch.month + nodes_batch.months_max):
                # now the node batch counts
                r.revenue += sales_price_cpr_unit_month * nodes_batch.cpr * utilization * nodes_batch.count
                # nodes_batch.cpr goes up over time
                r.cost += (
                    nodes_batch.cost / 60 + nodes_batch.cost_power_month + nodes_batch.cost_rackspace_month
                ) * nodes_batch.count
                r.investments_done += nodes_batch.cost * nodes_batch.count
                r.power_usage_kw += nodes_batch.power * nodes_batch.count / 1000
                r.rackspace_usage_u += nodes_batch.rackspace_u * nodes_batch.count
                r.nrnodes_active += nodes_batch.count
                r.cpr_available += nodes_batch.cpr * nodes_batch.count

                r.tft_farmed = self.tft_create(month_now=month, month_batch=month_batch)
                r.tft_burned = self.tft_burn(month_now=month, month_batch=month_batch)

                tft_new = r.tft_farmed

                # deal with the tokens created
                month_now = month
                tftprice_now = self.tft_price_get(month_now)
                self.cpr_sum += float(nodes_batch.cpr * nodes_batch.count)
                self.tft_sum += float(tft_new)

                if not self.sheet.rows["tokens_farmed"].cells[month_now]:
                    self.sheet.rows["tokens_farmed"].cells[month_now] = 0
                    self.sheet.rows["tokens_farmed_value"].cells[month_now] = 0
                self.sheet.rows["tokens_farmed"].cells[month_now] += float(tft_new)
                self.sheet.rows["tokens_farmed_value"].cells[month_now] = (
                    self.sheet.rows["tokens_farmed"].cells[month_now] * tftprice_now
                )

                # calculate current value
                row = self.sheet.rows["tokensbatch_%s_farmed_tft" % month_batch]
                row.cells[month_now] = tft_new

        return r

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
