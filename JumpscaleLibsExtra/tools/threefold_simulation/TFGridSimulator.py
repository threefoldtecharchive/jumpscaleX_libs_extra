from Jumpscale import j

from .BillOfMaterial import *
from .NodesBatch import *
from .SimulatorBase import SimulatorBase


class TokenCreator:
    pass


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
        self.rows = self.sheet.rows
        self.nodebatches = []  # 0 is the first batch, which stands for month 1
        self.bom = BillOfMaterial()
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
        nb = NodesBatch(simulation=self, nrnodes=nrnodes, month_start=month)
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
        if name in self.sheet.rows:
            self.sheet.rows.pop(name)
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

    def nodesbatch_calc(self, month=5, nrnodes_new=100):
        self._prepare()
        nb = NodesBatch(simulation=self, nrnodes=nrnodes_new, month_start=month)
        nb.calc()
        return nb

    def _prepare(self):
        self._interpolate("cost_rack_unit", "0:%s" % self.environment.cost_rack_unit)
        self._interpolate("cost_power_kwh", "0:%s" % self.environment.cost_power_kwh)

    def calc(self, nrnodes_new=None):

        self._prepare()

        if not nrnodes_new:
            nodes_sold = "0:5,6:150,12:1000,13:0"
        row_nrnodes_new = self._interpolate("nrnodes_new", nrnodes_new)
        row_nrnodes_total = self.sheet.addRow("nrnodes", nrfloat=0, aggregate="FIRST")

        row_tft_farmed = self.sheet.addRow("tft_farmed", aggregate="AVG", defval=0, ttype="float", empty=True)
        row_tft_cultivated = self.sheet.addRow("tft_cultivated", aggregate="AVG", defval=0, ttype="float", empty=True)
        # sold tft to cover power & rackspace costs
        row_tft_sold = self.sheet.addRow("tft_sold", aggregate="AVG", defval=0, ttype="float", empty=True)
        row_tft_burned = self.sheet.addRow("tft_burned", aggregate="AVG", defval=0, ttype="float", empty=True)

        row_cost_rackspace = self.sheet.addRow("cost_rackspace", aggregate="AVG", defval=0, ttype="int", empty=True)
        row_cost_power = self.sheet.addRow("cost_power", aggregate="AVG", defval=0, ttype="int", empty=True)
        row_cost_hardware = self.sheet.addRow("cost_hardware", aggregate="AVG", defval=0, ttype="int", empty=True)
        row_cost_maintenance = self.sheet.addRow("cost_maintenance", aggregate="AVG", defval=0, ttype="int", empty=True)
        row_rackspace_u = self.sheet.addRow("rackspace_u", aggregate="AVG", defval=0, ttype="float", empty=True)
        row_power_kw = self.sheet.addRow("power_kw", aggregate="AVG", defval=0, ttype="float", empty=True)

        row_investment = self.sheet.addRow("investment", aggregate="FIRST", defval=0, ttype="int", empty=True)
        row_revenue = self.sheet.addRow("revenue", aggregate="AVG", defval=0, ttype="int", empty=True)

        # row_cpr_available = self.sheet.addRow("cpr_available", aggregate="FIRST")

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

        def floatt(val):
            if val == None:
                return 0.0
            return float(val)

        for month in range(0, 60):
            # now walk over all batches which came live since day 0
            for month_batch in range(0, month + 1):
                nb = self.nodebatches[month_batch]
                row_rackspace_u.cells[month] += floatt(nb.sheet.rows["rackspace_u"].cells[month])
                row_power_kw.cells[month] += floatt(nb.sheet.rows["power"].cells[month]) / 1000
                row_tft_farmed.cells[month] += floatt(nb.sheet.rows["tft_farmed"].cells[month])
                row_tft_cultivated.cells[month] += floatt(nb.sheet.rows["tft_cultivated"].cells[month])
                row_tft_sold.cells[month] += floatt(nb.sheet.rows["tft_sold"].cells[month])
                row_tft_burned.cells[month] += floatt(nb.sheet.rows["tft_burned"].cells[month])

                row_cost_rackspace.cells[month] += floatt(nb.sheet.rows["cost_rackspace"].cells[month])
                row_cost_power.cells[month] += floatt(nb.sheet.rows["cost_power"].cells[month])
                row_cost_hardware.cells[month] += floatt(nb.sheet.rows["cost_hardware"].cells[month])
                row_cost_maintenance.cells[month] += floatt(nb.sheet.rows["cost_maintenance"].cells[month])

                row_investment.cells[month] += floatt(nb.cost_hardware)

            row_revenue.cells[month] = self.tft_price_get(month) * row_tft_cultivated.cells[month]

        row = (
            self.sheet.rows["tft_farmed"]
            + self.sheet.rows["tft_cultivated"]
            - self.sheet.rows["tft_burned"]
            - self.sheet.rows["tft_sold"]
        )
        row.name = "tft_total"
        self.sheet.rows["tft_total"] = row
        # go for million tft to make easy to visualize
        self.sheet.rows["tft_total"].cells = [i for i in self.sheet.rows["tft_total"].cells]

        self.sheet.rows["tft_cumul"] = row.accumulate("tft_cumul")

        # calculate how much in $ has been created/famed
        def tft_total_calc(val, month, args):
            tftprice = self.tft_price_get(month)
            return val * tftprice / 1000

        row = self.sheet.copy("tft_movement_value_kusd", self.sheet.rows["tft_total"], ttype="int", aggregate="LAST")
        row.function_apply(tft_total_calc)

        row2 = self.sheet.copy("tft_cumul_value_kusd", self.sheet.rows["tft_cumul"], ttype="int", aggregate="LAST")
        row2.function_apply(tft_total_calc)

        def extrapolate(val, month, args):
            return val * 60 / 1000000

        row_revenue_extrapolated = self.sheet.copy(
            "revenue_extrapolated", self.sheet.rows["revenue"], ttype="int", aggregate="LAST"
        )
        row_revenue_extrapolated.function_apply(extrapolate)
        # j.shell()

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
