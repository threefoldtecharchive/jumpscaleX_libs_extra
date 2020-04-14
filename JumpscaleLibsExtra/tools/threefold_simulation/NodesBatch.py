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
        cpr = 0.0 (F)
        cpr_improve = 0.0 (F)
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
        self._row_add("cost_total")
        self._row_add("rackspace_u")
        self._row_add("power")
        # self._row_add("mbit_sec_used")

        self._row_add("tft_movement_usd")
        self._row_add("tft_farmer_income_cumul_usd")
        self._row_add("roi")

        self._row_add("rev_compute")
        self._row_add("rev_storage")
        self._row_add("rev_network")
        self._row_add("rev_total")
        self._row_add("rev_compute_max")
        self._row_add("rev_storage_max")
        self._row_add("rev_network_max")
        self._row_add("rev_total_max")

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

        self._init_ = False

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
        if name not in self.sheet.rows:
            row = self.sheet.addRow(name, aggregate=aggregate, ttype=ttype, nrcols=120)
            row.window_month_start = self.month_start
            row.window_month_period = self.months_left
        else:
            row = self.sheet.rows[name]
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

    def _init2(self):
        if not self._init_:
            improve = self.simulation.cpr_improve_get(self.month_start)
            assert improve >= 0
            assert improve < 0.5
            self.cpr = self.node_normalized.production.cpr * self.nrnodes * (1 + improve)
            self.cpr_improve = self.simulation.cpr_improve_get(self.month_start)
            self._init_ = True

    @property
    def tft_farmed_total(self):
        total = 0
        for x in self.sheet.rows.tft_farmed.cells:
            if x:
                total += float(x)

        return int(total)

    def revenue_get(self, month):
        cu_rev_max, su_rev_max, nu_rev_max, cu_rev, su_rev, nu_rev, tot_rev_max, tot_rev = self._rev_get(month)
        return tot_rev

    def _rev_get(self, month):

        price_decline = self.simulation.sales_price_decline_get(month)  # 0-1

        cu = self.node_normalized.production.cu * self.nrnodes * (1 + self.cpr_improve)
        su = self.node_normalized.production.su * self.nrnodes * (1 + self.cpr_improve)
        # no improvement on nu because we kept it same
        nu = self.node_normalized.production.nu_used_month * self.nrnodes

        cu_price = self.simulation.sales_price_cu / (1 + price_decline)
        su_price = self.simulation.sales_price_su / (1 + price_decline)
        # for nu no price decline because we also did not let the cost go down
        nu_price = self.simulation.sales_price_nu

        cu_rev_max = cu_price * cu
        su_rev_max = su_price * su
        nu_rev_max = nu_price * nu

        utilization = self.simulation.utilization_get(month)

        cu_rev = cu_rev_max * utilization
        su_rev = su_rev_max * utilization
        nu_rev = nu_rev_max * utilization

        tot_rev_max = cu_rev_max + su_rev_max + nu_rev_max
        tot_rev = cu_rev + su_rev + nu_rev

        return cu_rev_max, su_rev_max, nu_rev_max, cu_rev, su_rev, nu_rev, tot_rev_max, tot_rev

    def _calc(self, month):

        self._init2()

        if month < self.month_start:
            return

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
            cost_power = self.node_normalized.total.cost_power_month * self.nrnodes * utilization
            self._set("cost_power", month, cost_power)

            cost_hardware = self.node_normalized.total.cost_hardware_month * self.nrnodes
            self._set("cost_hardware", month, cost_hardware)

            cost_maintenance = cost_hardware * self.environment.params.cost_maintenance_percent_of_hw / 100
            self._set("cost_maintenance", month, cost_maintenance)

            cost_network = self.node_normalized.production.cost_nu_month * self.nrnodes * utilization

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

            cu_rev_max, su_rev_max, nu_rev_max, cu_rev, su_rev, nu_rev, tot_rev_max, tot_rev = self._rev_get(month)

            self._set("rev_compute", month, cu_rev)
            self._set("rev_storage", month, su_rev)
            self._set("rev_network", month, nu_rev)
            self._set("rev_total", month, tot_rev)
            self._set("rev_compute_max", month, cu_rev_max)
            self._set("rev_storage_max", month, su_rev_max)
            self._set("rev_network_max", month, nu_rev_max)
            self._set("rev_total_max", month, tot_rev_max)

            usd_cultivation = tft_cultivated * tftprice_now

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

        t = (
            self.rows.cost_network
            + self.rows.cost_hardware
            + self.rows.cost_maintenance
            + self.rows.cost_rackspace
            + self.rows.cost_power
        )

        self.rows.cost_total.cells = t.cells

        self.simulated_months.append(month)

        # if month == 5 and self.environment.name != "amd":
        #     print(self)
        #     j.shell()
        #     w

        return tft_farmer_income

    def cloud_cost_get(self, x):
        """
        is the max cost of the grid (at full utilization)
        for power, rackspace & hardware (written off over 5 years)
        """
        node = self.node_normalized
        cost = float(node.total.cost_total_month) * float(self.nrnodes)
        return cost

    def cloud_valuation_get(self, x):
        """
        the value of the nodesbatch at that month based on selected cloud index calculation method
        """
        rev = self.rows.rev_total_max.cells[x]
        config = j.tools.tfgrid_simulator.simulator_config.cloudvaluation

        if config.indextype == "revenue":
            rev = int(rev * config.revenue_months)
            return rev
        else:
            cost = self.cloud_cost_get(x)
            margin = rev - cost
            margin = int(margin * config.margin_months)
            return margin

    def markdown_profit_loss(self, month):
        fi = j.core.text.format_item
        tft_cultivated_usd = self.rows.tft_cultivated_usd.cells[month]

        rev_compute = self.rows.rev_compute.cells[month]
        rev_storage = self.rows.rev_storage.cells[month]
        rev_network = self.rows.rev_network.cells[month]
        rev_compute_max = self.rows.rev_compute_max.cells[month]
        rev_storage_max = self.rows.rev_storage_max.cells[month]
        rev_network_max = self.rows.rev_network_max.cells[month]
        rev_total = rev_compute + rev_storage + rev_network
        rev_total_max = rev_compute_max + rev_storage_max + rev_network_max

        cost_rackspace = self.rows.cost_rackspace.cells[month]
        cost_maintenance = self.rows.cost_maintenance.cells[month]
        cost_hardware = self.rows.cost_hardware.cells[month]
        cost_network = self.rows.cost_network.cells[month]
        cost_power = self.rows.cost_power.cells[month]
        cost_total = self.rows.cost_total.cells[month]

        price_decline = self.simulation.sales_price_decline_get(month)  # 0-1
        utilization = self.simulation.utilization_get(month)

        cu = self.node_normalized.production.cu * self.nrnodes * (1 + self.cpr_improve)
        su = self.node_normalized.production.su * self.nrnodes * (1 + self.cpr_improve)
        # no improvement on nu because we kept it same
        nu = self.node_normalized.production.nu_used_month * self.nrnodes

        cu_price = self.simulation.sales_price_cu / (1 + price_decline)
        su_price = self.simulation.sales_price_su / (1 + price_decline)
        # for nu no price decline because we also did not let the cost go down
        nu_price = self.simulation.sales_price_nu

        if self.simulation.config.cloudvaluation.indextype == "REVENUE":
            nrmonths = self.simulation.config.cloudvaluation.revenue_months
        else:
            nrmonths = self.simulation.config.cloudvaluation.margin_months

        C = f"""

        ## P&L report for month {month}

        ### nodesbatch

        - added to grid in month : {self.month_start}
        - nrnodes                : {self.nrnodes}
        - investment hardware    : {fi(self.cost_hardware)}

        ### cloud units

        - #cu                   : {fi(cu)}
        - #su                   : {fi(su)}
        - #nu                   : {fi(nu)}

        ### simulation params in this month

        - utilization           : {fi(utilization)}
        - price decline         : {fi(price_decline)}
        - cu price              : {fi(cu_price)}
        - su price              : {fi(su_price)}
        - nu price              : {fi(nu_price)}

        ### revenues with utilization in account

        - rev cu                : {fi(rev_compute)}
        - rev su                : {fi(rev_storage)}
        - rev nu                : {fi(rev_network)}
        - rev total             : {fi(rev_total)}

        ### revenues if all resources used

        - rev cu                : {fi(rev_compute_max)}
        - rev su                : {fi(rev_storage_max)}
        - rev nu                : {fi(rev_network_max)}
        - rev total             : {fi(rev_total_max)}


        ### costs

        - cost hardware         : {fi(cost_hardware)}
        - cost power            : {fi(cost_power)}
        - cost maintenance      : {fi(cost_maintenance)}
        - cost rackspace        : {fi(cost_rackspace)}
        - cost network          : {fi(cost_network)}
        - cost total            : {fi(cost_total)}

        ### profit this month

        - margin                : {fi(rev_total-self.cloud_cost_get(month))}
        - margin ma             : {fi(rev_total_max-cost_total)}

        ### valuation parameters

        - price_cu              : {self.simulation.config.cloudvaluation.price_cu}
        - price_su              : {self.simulation.config.cloudvaluation.price_su}
        - price_nu              : {self.simulation.config.cloudvaluation.price_nu}

        ### valuation report

        - valuation based on {nrmonths} months of {self.simulation.config.cloudvaluation.indextype}
        - valuation is          : {fi(self.cloud_valuation_get(month))}

        
        """
        return j.core.tools.text_strip(C)

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
