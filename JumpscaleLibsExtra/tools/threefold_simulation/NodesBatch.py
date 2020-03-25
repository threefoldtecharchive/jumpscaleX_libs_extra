from Jumpscale import j
from .SimulatorBase import SimulatorBase


class NodesBatch(SimulatorBase):
    """
    nodes are brought life per month in batches, its our way how to simulate the growth of the network
    a notes batch is X nr of nodes in a group
    the batch_nr is the month in which the batch came live,
    starts with 0 and ends to end of simulation
    its one per month

    we don't start with an empty sheet,
    there are tft's farmed before this simulation that is represented in : tft_farmed_before_simulation

    the first batch are the existing nodes (month 0) and has less months_left then every new batch

    """

    _SCHEMATEXT = """
        @url = threefold.simulation.nodesbatch
        name= ""
        batch_nr = (I)  #0 is first month (when batch created)
        nrnodes = 0 #nr of nodes
        month_start = 0
        months_left = 60
        tft_farmed_before_simulation = 0 (F)
        node = (O) !threefold.simulation.nodesbatch.node
        simulated_months = (L)
        
        #the params at start
        @url = threefold.simulation.nodesbatch.node
        rackspace_u = (F)
        cost_hardware = (N)
        cpr = (F)
        power = (F)
        """

    def _init(self, **kwargs):

        self._cat = "NodesBatch"
        self.simulation = kwargs["simulation"]
        self.environment = kwargs["environment"]

        self.__init()

        self._row_add("tft_farmed")
        self._row_add("tft_cultivated")  # sold capacity
        self._row_add("tft_sold")  # sold tft to cover power & rackspace costs
        self._row_add("tft_burned")
        self._row_add("tft_farmer_income")
        self._row_add("tft_farmer_income_cumul")

        self._row_add("cost_rackspace")
        self._row_add("cost_power")
        self._row_add("cost_hardware")
        self._row_add("cost_maintenance")
        self._row_add("rackspace_u")
        self._row_add("power")

        self._row_add("tft_movement_usd")
        self._row_add("tft_farmer_income_cumul_usd")
        self._row_add("roi")

    def __init(self):

        self.sheet = j.data.worksheets.sheet_new("batch_%s" % self.batch_nr, nrcols=120)

        self.rows = self.sheet.rows

        self.batch_nr = self.month_start

        n = self.environment.node_normalized
        self.node.rackspace_u = n.rackspace_u
        self.node.cost_hardware = n.cost
        self.node.cpr = n.cpr
        self.node.power = n.power

        improve = self.simulation.sheet.rows["cpr_improve"].cells[self.month_start] / 100
        self.node.cpr = self.environment.cpr / self.environment.nr_devices * (1 + improve)

        self.nrcols = self.month_start + self.months_left

    def export_(self):
        r = {}
        r["sheet"] = self.sheet.export_()
        r["data"] = self._data._ddict
        return r

    def import_(self, ddict):
        self._data_update(ddict["data"])
        self.__init()
        self.sheet.import_(ddict["sheet"])
        self.sheet.clean()

    def _row_add(self, name, aggregate="FIRST", ttype=None):
        row = self.sheet.addRow(name, aggregate=aggregate, ttype=ttype, nrcols=120)
        row.window_month_start = self.month_start
        row.window_month_period = self.months_left
        return row

    def _row_set(self, name, row):
        row.name = name
        row.window_month_start = self.month_start
        row.window_month_period = self.months_left
        self.sheet.rows[name] = row
        return row

    def _row_copy(self, name, rowsource, aggregate="FIRST", ttype="float"):
        row = self.sheet.copy(name, rowsource, aggregate=aggregate, ttype=ttype)
        row.window_month_start = self.month_start
        row.window_month_period = self.months_left
        return row

    def _set(self, rowname, month, val):
        sheet = self.sheet.rows[rowname]
        sheet.cells[month] = val
        self._log_debug("batch:%s month:%s %s:%s" % (self.batch_nr, month, rowname, val))

    def calc(self):
        for i in range(self.month_start, self.month_start + self.months_left):
            self._calc(i)

    def _calc(self, month):

        if month < self.month_start:
            return

        floatt = self.simulation._float
        tftprice_now = self.simulation.tft_price_get(month)

        # all but
        if month < self.month_start + self.months_left + 1:

            # if already calculated no need to do
            if month in self.simulated_months:
                raise j.exceptions.Input("should not calculate month:%s again" % month)

            rackspace_u = self.node.rackspace_u * self.nrnodes
            self._set("rackspace_u", month, rackspace_u)
            cost_rackspace = rackspace_u * self.simulation.cost_rack_unit_get(month)
            self._set("cost_rackspace", month, cost_rackspace)

            utilization = self.simulation.utilization_get(month)
            if utilization < 0.8:
                utilization = utilization * 1.2  # take buffer
            power = self.node.power * self.nrnodes * utilization
            self._set("power", month, power)
            cost_power = power / 1000 * 24 * 30 * self.simulation.cost_power_kwh_get(month)
            self._set("cost_power", month, cost_power)

            cost_hardware = self.node.cost_hardware * self.nrnodes / 60
            self._set("cost_hardware", month, cost_hardware)

            cost_maintenance = cost_hardware * 0.2  # means we spend 20% on cost of HW on maintenance/people
            self._set("cost_maintenance", month, cost_maintenance)

            tft_farmed = self.simulation.token_creator.tft_farm(month, self)
            if month == 0:
                tft_farmed += self.tft_farmed_before_simulation

            tft_cultivated = int(self.simulation.token_creator.tft_cultivate(month, self))
            tft_burned = int(self.simulation.token_creator.tft_burn(month, self))
            self._set("tft_farmed", month, tft_farmed)
            self._set("tft_cultivated", month, tft_cultivated)
            self._set("tft_burned", month, -tft_burned)
            tft_sold = (float(cost_power) + float(cost_rackspace) + float(cost_maintenance)) / float(tftprice_now)
            self._set("tft_sold", month, -tft_sold)
            tft_farmer_income = tft_farmed + tft_cultivated - tft_sold
            self._set("tft_farmer_income", month, tft_farmer_income)

            self._set("tft_movement_usd", month, tftprice_now * floatt(tft_farmer_income))
        else:
            tft_farmer_income = 0

        if month == 0:
            tft_farmer_income_cumul_previous = 0
        else:
            tft_farmer_income_cumul_previous = floatt(self.rows.tft_farmer_income_cumul.cells[month - 1])
        tft_farmer_income_cumul = tft_farmer_income_cumul_previous + floatt(tft_farmer_income)
        self._set("tft_farmer_income_cumul", month, tft_farmer_income_cumul)

        tft_farmer_income_cumul_usd = tftprice_now * tft_farmer_income_cumul
        self._set("tft_farmer_income_cumul_usd", month, tft_farmer_income_cumul_usd)

        cost_total_hardware_investment = float(self.node.cost_hardware * self.nrnodes)
        roi = float(tft_farmer_income_cumul_usd) / float(cost_total_hardware_investment)
        self._set("roi", month, roi)

        self.simulated_months.append(month)

        return tft_farmer_income

    @property
    def roi_months(self):
        if "roi" not in self.sheet.rows:
            return None
        x = 0
        for val in self.sheet.rows["roi"].cells:
            x += 1
            if self.simulation._float(val) > 1:
                return x - self.month_start
        return None

    @property
    def roi_end(self):
        if not self.sheet.rows["roi"].cells[-1]:
            self.sheet.rows["roi"].interpolate()
        return self.sheet.rows["roi"].cells[-1]

    @property
    def cost_hardware(self):
        return self.node.cost_hardware * self.nrnodes

    def markdown(self):
        out = SimulatorBase.__repr__(self)
        for key in ["roi_months", "roi_end", "tft_farmer_income_cumul_usd", "cost_hardware"]:
            res = getattr(self, key)
            out += " - %-20s %s\n" % (key, res)
        return out

    def graph_tft(self, cumul=False, single=False):
        import plotly.graph_objects as go

        names = ["farmed", "cultivated", "sold", "burned", "farmer_income"]
        if cumul:
            names.append("cumul")

        start = self.month_start
        end = self.month_start + self.months_left

        fig = go.FigureWidget()
        for name in names:
            # values = eval(f"self.rows.tft_{name}.values")
            row = getattr(self.rows, f"tft_{name}")
            values = row.values_all[start:end]
            x = [i for i in range(start, end)]
            if single:
                values = [i / self.nrnodes for i in values]
            fig.add_trace(go.Scatter(x=x, y=values, name=name))
        if not single:
            nrnodes = self.nrnodes
        else:
            nrnodes = 1
        fig.update_layout(
            title="Tokens movement per month (batch:%s,nrnodes:%s)." % (self.batch_nr, nrnodes), showlegend=True
        )

        return fig

    def _tft_usd(self, name, single=False):
        row = getattr(self.rows, f"tft_{name}")
        res = []
        if single:
            nrnodes = self.nrnodes
        else:
            nrnodes = 1
        for month in range(row.window_month_start, row.window_month_start + row.window_month_period):
            tft_price = self.simulation.tft_price_get(month)
            if row.cells[month] == None:
                row.clean()
            res.append(float(row.cells[month] / nrnodes * tft_price))
        return row, res

    def _values_usd_get(self, cumul=False, names=None, single=False):
        if not names:
            names = ["farmed", "cultivated", "sold", "burned", "farmer_income"]
            if cumul:
                names.append("farmer_income_cumul")
        res = []
        for name in names:
            row, values = self._tft_usd(name, single=single)
            x = [i + row.window_month_start - 1 for i in range(1, len(values) + 1)]
            res.append((x, name, values, row))
        return res

    def graph_usd(self, cumul=False, single=False):
        import plotly.graph_objects as go

        fig = go.FigureWidget()
        for x, name, values, row in self._values_usd_get(cumul=cumul, single=single):
            fig.add_trace(go.Scatter(x=x, y=values, name=name, connectgaps=False))
        if single:
            nrnodes = 1
        else:
            nrnodes = self.nrnodes
        fig.update_layout(
            title="USD movement per month (batch:%s,nrnodes:%s)." % (self.batch_nr, nrnodes), showlegend=True
        )

        return fig

    def __repr__(self):
        print(SimulatorBase.__repr__(self))
        out = ""
        for key in self.sheet.rows.keys():
            row = self.sheet.rows[key]
            if row.cells[1] and float(row.cells[1]) < 3:
                res = row.aggregate("Q", roundnr=2)
            else:
                res = row.aggregate("Q", roundnr=0)
            res = [str(i) for i in res]
            res2 = ", ".join(res)
            out += " - %-20s %s\n" % (key, res2)

        for key in ["roi_months"]:
            res = getattr(self, key)
            out += " - %-20s %s\n" % (key, res)

        return out
