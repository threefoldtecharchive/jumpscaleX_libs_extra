from Jumpscale import j
from .SimulatorBase import SimulatorBase


class NodesBatch(SimulatorBase):
    """
    a normalized node over time
    """

    _SCHEMATEXT = """
        @url = threefold.simulation.nodesbatch
        batch_nr = (I)  #0 is first month (when batch created)
        nrnodes = 0 #nr of nodes
        month_start = 0
        months_left = 60
        tft_farmed_before_simulation = 0 (F)
        node = (O) !threefold.simulation.nodesbatch.node
        
        #the params at start
        @url = threefold.simulation.nodesbatch.node
        rackspace_u = (F)
        cost_hardware = (N)
        cpr = (F)
        power = (F)
        """

    def _init(self, **kwargs):
        self._cat = "NodesBatch"
        self.simulator = kwargs["simulator"]
        self.batch_nr = self.month_start
        environment = self.simulator.environment
        self.node.cost_hardware = environment.cost / environment.nr_devices
        self.node.rackspace_u = environment.rackspace_u / environment.nr_devices
        self.node.power = environment.power / environment.nr_devices

        improve = self.simulator.sheet.rows["cpr_improve"].cells[self.month_start] / 100
        self.node.cpr = environment.cpr / environment.nr_devices * (1 + improve)

        self.nrcols = self.month_start + self.months_left
        self.sheet = j.data.worksheets.sheet_new("batch_%s" % self.batch_nr, nrcols=120)

        self.sheet.addRow("tft_farmed", aggregate="AVG")
        self.sheet.addRow("tft_cultivated", aggregate="AVG")  # sold capacity
        self.sheet.addRow("tft_sold", aggregate="AVG")  # sold tft to cover power & rackspace costs
        self.sheet.addRow("tft_burned", aggregate="AVG")

        self.sheet.addRow("cost_rackspace", aggregate="AVG")
        self.sheet.addRow("cost_power", aggregate="AVG")
        self.sheet.addRow("cost_hardware", aggregate="AVG")
        self.sheet.addRow("cost_maintenance", aggregate="AVG")
        self.sheet.addRow("rackspace_u", aggregate="AVG")
        self.sheet.addRow("power", aggregate="AVG")

    def _set(self, rowname, month, val):
        sheet = self.sheet.rows[rowname]
        sheet.cells[month] = val

    def calc(self):
        for month in range(self.month_start, self.month_start + self.months_left):

            tft_farmed = self.simulator.token_creator.tft_farm(month, self)
            tft_cultivated = self.simulator.token_creator.tft_cultivate(month, self)
            tft_burned = self.simulator.token_creator.tft_burn(month, self)
            self._set("tft_farmed", month, tft_farmed)
            self._set("tft_cultivated", month, tft_cultivated)
            self._set("tft_burned", month, tft_burned)

            rackspace_u = self.node.rackspace_u * self.nrnodes
            self._set("rackspace_u", month, rackspace_u)
            cost_rackspace = rackspace_u * self.simulator.cost_rack_unit_get(month)
            self._set("cost_rackspace", month, cost_rackspace)

            utilization = self.simulator.utilization_get(month)
            if utilization < 0.8:
                utilization = utilization * 1.2  # take buffer
            power = self.node.power * self.nrnodes * utilization
            self._set("power", month, power)
            cost_power = power / 1000 * 24 * 30 * self.simulator.cost_power_kwh_get(month)
            self._set("cost_power", month, cost_power)

            cost_hardware = self.node.cost_hardware * self.nrnodes / 60
            self._set("cost_hardware", month, cost_hardware)

            cost_maintenance = cost_hardware * 0.2  # means we spend 20% on cost of HW on maintenance/people
            self._set("cost_maintenance", month, cost_maintenance)

            tftprice_now = self.simulator.tft_price_get(month)
            tft_sold = (float(cost_power) + float(cost_rackspace) + float(cost_maintenance)) / float(tftprice_now)
            self._set("tft_sold", month, tft_sold)

        print(self)

        row = (
            self.sheet.rows["tft_farmed"]
            + self.sheet.rows["tft_cultivated"]
            - self.sheet.rows["tft_burned"]
            - self.sheet.rows["tft_sold"]
        )
        row.name = "tft_movement"
        self.sheet.rows["tft_movement"] = row

        self.sheet.rows["tft_cumul"] = row.accumulate("tft_accumulation")

        # calculate how much in $ has been created/famed
        def tft_total_calc(val, month, args):
            nb = args["nb"]
            tftprice = nb.simulator.tft_price_get(month)
            return val * tftprice

        row = self.sheet.rows["tft_cumul"].copy(name="tft_cumul_value_usd", ttype="int")
        row.function_apply(tft_total_calc, {"nb": self})
        self.sheet.rows["tft_cumul_value_usd"] = row
        row = self.sheet.rows["tft_movement"].copy(name="tft_movement_value_usd", ttype="int")
        self.sheet.rows["tft_movement_value_usd"] = row
        row.function_apply(tft_total_calc, {"nb": self})

        # calculate ROI in relation to initial HW
        def roi_calc(val, month, args):
            nb = args["nb"]
            cost_total = float(self.node.cost_hardware * self.nrnodes)
            r = float(val) / cost_total * 100
            if r < 0:
                j.shell()
                w
            return round(r, 0)

        row = self.sheet.rows["tft_cumul_value_usd"].copy(name="roi", ttype="int")
        row.function_apply(roi_calc, {"nb": self})
        self.sheet.rows["roi"] = row

        j.shell()
        w

    # def roi_farming_hwonly(self, tft_price=None):
    #     if not tft_price:
    #         tft_price = j.tools.tfsimulation.current.tft_price_get()
    #     farming_income = self.tft_farmed_total * tft_price
    #     return farming_income / self.cost_hardware_total
    #
    # def roi_farming(self, tft_price=None):
    #     if not tft_price:
    #         tft_price = j.tools.tfsimulation.current.tft_price_get()
    #     farming_income = self.tft_farmed_total * tft_price
    #     return farming_income / float(self.cost_total)
    #
    # @property
    # def roi_farming_end(self):
    #     return self.roi_farming()

    def __repr__(self):
        print(SimulatorBase.__repr__(self))
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

        return out
