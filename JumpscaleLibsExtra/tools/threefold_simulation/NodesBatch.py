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
        """

    def _init(self, **kwargs):

        self._cat = "NodesBatch"
        self.simulation = kwargs["simulation"]
        self.environment = kwargs["environment"]

        self.__init()

        self._row_add("tft_farmed")
        self._row_add("tft_farmed_usd")
        self._row_add("tft_cultivated")  # sold capacity
        self._row_add("tft_cultivated_usd")  # sold capacity
        self._row_add("tft_sold")  # sold tft to cover power & rackspace costs
        self._row_add("tft_burned")
        self._row_add("tft_farmer_income")
        self._row_add("tft_farmer_income_cumul")

        self._row_add("difficulty_level")
        self._row_add("tft_price")

        self._row_add("cost_rackspace")
        self._row_add("cost_power")
        self._row_add("cost_hardware")
        self._row_add("cost_maintenance")
        self._row_add("cost_network")
        self._row_add("rackspace_u")
        self._row_add("power")
        self._row_add("mbit_sec_used")

        self._row_add("tft_movement_usd")
        self._row_add("tft_farmer_income_cumul_usd")
        self._row_add("roi")

        self._period = "B"  # can be Y, Q

    def __init(self):

        self.sheet = j.data.worksheets.sheet_new("batch_%s" % self.batch_nr, nrcols=120)

        self.rows = self.sheet.rows

        self.batch_nr = self.month_start

        self.simulated_months = []

        # n = self.environment.node_normalized
        # self.node_normalized.rackspace_u = n.rackspace_u
        # self.node_normalized.cost_hardware = n.cost
        # self.node_normalized.power = n.power

        # improve = self.simulation.sheet.rows["cpr_improve"].cells[self.month_start] / 100
        # assert self.environment.nr_devices
        # self.node_normalized.cpr = self.environment.cpr / self.environment.nr_devices * (1 + improve)

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
        """

        """
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

    @property
    def tft_farmed_total(self):
        total = 0
        for x in self.sheet.rows.tft_farmed.cells:
            if x:
                total += float(x)

        return int(total)

    def calc_detail(self):

        for i in range(self.month_start, self.month_start + self.months_left):
            self._calc(i, detail=True)

    def _calc(self, month, detail=False):

        if month < self.month_start:
            return

        if details:

            self._row_add("cost_rackspace")
            self._row_add("cost_power")
            self._row_add("cost_hardware")
            self._row_add("cost_maintenance")
            self._row_add("cost_network")

        floatt = self.simulation._float
        tftprice_now = self.simulation.tft_price_get(month)

        # all but
        if month < self.month_start + self.months_left + 1:

            # if already calculated no need to do
            if month in self.simulated_months:
                raise j.exceptions.Input("should not calculate month:%s again" % month)

            rackspace_u = self.node_normalized.total.rackspace_u * self.nrnodes
            self._set("rackspace_u", month, rackspace_u)
            cost_rackspace = rackspace_u * self.simulation.cost_rack_unit_get(month)
            self._set("cost_rackspace", month, cost_rackspace)

            utilization = self.simulation.utilization_get(month)
            if utilization < 0.8:
                utilization = utilization * 1.2  # take buffer
            if utilization < 0.2:
                utilization = 0.2

            power = self.node_normalized.total.power * self.nrnodes * utilization
            self._set("power", month, power)
            cost_power = self.node_normalized.total.cost_power_month_usd * self.nrnodes * utilization
            self._set("cost_power", month, cost_power)

            cost_hardware = self.node_normalized.total.cost_hardware_month * self.nrnodes
            self._set("cost_hardware", month, cost_hardware)

            cost_maintenance = cost_hardware * self.environment.params.cost_maintenance_percent_of_hw / 100
            self._set("cost_maintenance", month, cost_maintenance)

            cost_network = self.node_normalized.production.cost_nu_month * self.nrnodes

            self._set("cost_network", month, cost_network)

            tft_farmed = self.simulation.token_creator.tft_farm(month, self)
            if month == 0:
                tft_farmed += self.tft_farmed_before_simulation

            tft_cultivated = int(self.simulation.token_creator.tft_cultivate(month, self))
            tft_burned = int(self.simulation.token_creator.tft_burn(month, self))
            self._set("tft_farmed", month, tft_farmed)
            self._set("tft_farmed_usd", month, tft_farmed * tftprice_now)
            self._set("tft_cultivated", month, tft_cultivated)
            self._set("tft_cultivated_usd", month, tft_cultivated * tftprice_now)
            self._set("tft_burned", month, -tft_burned)
            tft_sold = (float(cost_power) + float(cost_rackspace) + float(cost_maintenance)) / float(tftprice_now)
            self._set("tft_sold", month, -tft_sold)
            tft_farmer_income = tft_farmed + tft_cultivated - tft_sold
            self._set("tft_farmer_income", month, tft_farmer_income)

            self._set("tft_movement_usd", month, tftprice_now * floatt(tft_farmer_income))

            self._set("difficulty_level", month, self.simulation.token_creator.difficulty_level_get(month))
            self._set("tft_price", month, tftprice_now)

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

        cost_total_hardware_investment = float(self.node_normalized.total.cost_hardware * self.nrnodes)
        roi = float(tft_farmer_income_cumul_usd) / float(cost_total_hardware_investment)
        self._set("roi", month, roi)

        self.simulated_months.append(month)

        # if month == 5 and self.environment.name != "amd":
        #     print(self)
        #     j.shell()
        #     w

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
        return self.sheet.rows["roi"].cells[self.month_start + self.months_left - 1]

    @property
    def cost_hardware(self):
        return self.node_normalized.total.cost_hardware * self.nrnodes

    @property
    def cost_hardware_month(self):
        return self.node_normalized.total.cost_hardware_month * self.nrnodes

    @property
    def cpr(self):
        return self.node_normalized.production.cpr * self.nrnodes

    @property
    def node_normalized(self):
        return self.environment.node_normalized

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
        out = str(SimulatorBase.__repr__(self))
        out += "\n"
        out += self.sheet.text_formatted(period=self._period, aggregate_type=None, exclude=None)
        return out

    __str__ = __repr__
