from Jumpscale import j

from .BillOfMaterial import *
from .NodesBatch import *
from .SimulatorBase import SimulatorBase


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

    def _init(self, **kwargs):
        self._model_ = False


class TFGridSimulator(SimulatorBase):

    _SCHEMATEXT = """
        @url = threefold.simulation.config
        self.cpr_sum = 0.0 (F)
        self.tft_sum = 0.0 (F)
        """

    def _init(self, **kwargs):
        self._model_ = False
        self.sheet = j.data.worksheets.sheet_new("simulation")
        self.nodebatches = []  # 0 is the first batch, which stands for month 1
        self.bom = BillOfMaterial()
        self.environment = Environment(name="default")

    def nodesbatch_start_set(self, nrnodes=1500, months_left=36, tft_farmed_before_simulation=0):
        nb = NodesBatch(
            nrnodes=nrnodes,
            month_start=0,
            months_left=months_left,
            tft_farmed_before_simulation=tft_farmed_before_simulation,
        )
        if len(self.nodebatches) == 0:
            self.nodebatches.append(None)
        self.nodebatches[0] = nb

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

    def nodes_batch_template_get(self, environment):
        nb = NodesBatch()
        nb.cost = environment.cost / environment.nr_devices
        nb.power = environment.power / environment.nr_devices
        nb.rackspace_u = environment.rackspace_u / environment.nr_devices
        nb.cost_power_month = environment.cost_power / environment.nr_devices
        nb.cost_rackspace_month = environment.cost_rack / environment.nr_devices
        nb.cpr = environment.cpr / environment.nr_devices
        return nb

    def growth_perc_get(self, month):
        return self.sheet.rows["growth_percent"].cells[month] / 100

    def tft_price_get(self, month=None):
        if not month:
            month = self.sheet.nrcols - 1
        return self.sheet.rows["tokenprice"].cells[month]

    def difficulty_level_get(self, month):
        return self.sheet.rows["difficulty_level"].cells[month]

    def nodes_batch_get(self, month):
        return self._nodebatches[month]

    def tft_create(self, month_now, month_batch):
        """
        @param month_now is the month to calculate the added tft for
        @param month_batch is when the node batch was originally added
        """
        nodes_batch = self.nodes_batch_get(month_batch)
        tftprice_now = self.tft_price_get(month_now)
        nodes_batch_investment = nodes_batch.cost * nodes_batch.count

        # FARMING ARGUMENTS ARE CREATED HERE, THIS IS THE MAIN CALCULATION
        tft_new = nodes_batch_investment / tftprice_now / self.difficulty_level_get(month_now) / 10

        return tft_new

    def tft_burn(self, month_now, month_batch):
        nodes_batch = self.nodes_batch_get(month_batch)
        # tftprice =
        return 0
        j.shell()

    def calc(self):
        row = self.sheet.addRow("nrnodes_new", nrfloat=0, aggregate="FIRST")
        row2 = self.sheet.addRow("nrnodes", nrfloat=0, aggregate="FIRST")
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

        for x in range(0, self.sheet.nrcols):
            self.sheet.addRow("tokensbatch_%s_farmed_tft" % x, aggregate="SUM")
            self.sheet.addRow("tokensbatch_%s_farmed_predicted_roi" % x, aggregate="AVG")

        # are the parameters for a batch of nodes to be added
        nodes_batch_template = self.nodes_batch_template_get(environment)

        for month_now in range(0, self.sheet.nrcols):
            if month_now > 0:
                nr_new = self.growth_perc_get(month_now) * row2.cells[month_now - 1]
                row2.cells[month_now] = int(row2.cells[month_now - 1] + nr_new)
                self._nodes_batch_add(month_now, nodes_batch_template, nr_new)
                row.cells[month_now] = nr_new
            else:
                row.cells[month_now] = nr_start_nodes
                row2.cells[month_now] = nr_start_nodes
                self._nodes_batch_add(
                    0,
                    nodes_batch_template,
                    nr_start_nodes,
                    months_max=months_remaining_start_nodes,
                    tft_farmed_before_simulation=tft_farmed_before_simulation,
                )

            r = self.result_get(month_now)
            row_rev.cells[month_now] = r.revenue / 1000
            row_cost.cells[month_now] = r.cost / 1000
            row_investment.cells[month_now] = r.investments_done / 1000
            row_power.cells[month_now] = r.power_usage_kw / 1000
            row_racks.cells[month_now] = r.rackspace_usage_u / 44
            row_cpr_available.cells[month_now] = r.cpr_available

        self.calculate_farmed_predicted_roi()

    def calculate_farmed_predicted_roi(self):
        """
        calculate the roi of already farmed TFT as future to be calculated ROI
        """

        # walk over the note batches
        for month_batch in range(0, self.sheet.nrcols):
            nodes_batch = self.nodes_batch_get(month_batch)
            tft_farmed = 0

            row_farmed_tft = self.sheet.rows["tokensbatch_%s_farmed_tft" % month_batch]

            # walk over all relevant months & add the tokens, just to calculate how many tokens will be farmed in this pool
            nr_months_farmed = 0
            for month in range(0, self.sheet.nrcols):
                if row_farmed_tft.cells[month]:
                    tft_farmed += float(row_farmed_tft.cells[month])
                    nr_months_farmed += 1

            if nodes_batch.tft_farmed_before_simulation:
                # this is only for the starting batch
                tft_farmed += nodes_batch.tft_farmed_before_simulation
            elif nr_months_farmed < 60:
                tft_farmed += (60 - nr_months_farmed) * float(row_farmed_tft.cells[-1])
                # take the last one, is not 100% correct should be extrapolated
                # not enough months farmed

            nodes_batch.tft_farmed_total = tft_farmed
            print(nodes_batch)

            for month_now in range(0, self.sheet.nrcols):
                tftprice_now = self.tft_price_get(month_now)
                tft_farmed_value = tft_farmed * tftprice_now

        # row_roi = self.sheet.rows["tokensbatch_%s_farmed_predicted_roi" % month_batch]
        # if not row_roi.cells[month_now]:
        #     row_roi.cells[month_now] = 0
        #
        # tftprice_now = self.tft_price_get(month_now)
        #
        # if month_now == 1:
        #     j.debug()

    def _nodes_batch_add(self, month, nodes_batch_template, nr_nodes, months_max=60, tft_farmed_before_simulation=None):
        while len(self._nodebatches) < month + 1:
            self._nodebatches.append(NodesBatch())
        n = self._nodebatches[month]
        # update date from template
        n._data._data_update(nodes_batch_template._data._ddict)
        n.count = nr_nodes
        n.month = month
        n.name = "month_%s" % month
        n.months_max = months_max
        improve = self.sheet.rows["cpr_improve"].cells[month] / 100
        n.cpr = n.cpr * (1 + improve)
        n.tft_farmed_total = 0
        n.tft_farmed_before_simulation = tft_farmed_before_simulation

    def result_get(self, month, utilization=None):
        """

        :param month: 0 is month 1
        :param occupation: in percent
        :return:
        """
        if not utilization:
            utilization = self.sheet.rows["utilization"].cells[month]
        utilization = j.data.types.percent.clean(utilization)
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
