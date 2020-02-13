from Jumpscale import j


class Simulation(j.baseclasses.object_config):
    """
    Bill of material
    device templates
    components
    """

    _SCHEMATEXT = """
        @url = threefold.simulation.bom
        name** = ""
        components = (LO) !threefold.simulation.component
        devices = (LO) !threefold.simulation.device.template

        @url = threefold.simulation.device.template
        name = ""
        components = (LO) !threefold.simulation.device.template.component

        @url = threefold.simulation.device.template.component
        name = ""
        nr = (F)

        @url = threefold.simulation.component
        name** = ""
        description = ""
        cost = (N)
        power = (I)
        rackspace_u = (F)
        cru = (F)
        sru = (F)
        hru = (F)
        mru = (F)
        su_perc = (P)
        cu_perc = (P)
        link = ""
        passmark = 0 (I)
        """

    def component_get(self, name):
        for item in self.components:
            if item.name == name:
                return item
        raise j.exceptions.Input("cannot find component name:%s" % name)

    def device_template_get(self, name):
        """
        get device template
        :param name:
        :return:
        """
        for item in self.devices:
            if item.name == name:
                return item
        raise j.exceptions.Input("cannot find device template with name:%s" % name)

    def device_get(self, name, device_template_name=None, description="", environment=None):
        """
        get device
        :param name:
        :return:
        """
        if not device_template_name:
            device_template_name = name
        d = Device(name=name, description=description, device_template_name=device_template_name)
        d.load(self, environment=environment)
        return d

    def environment_get(self, name, description=None):
        s = Environment(name=name, description=description)
        return s


class Component(j.baseclasses.object):
    def _init(self, **kwargs):
        self.nr = kwargs["nr"]
        self.component = kwargs["component"]


class Device(j.baseclasses.object_config):
    """
    a device which can be used to build a cloud with
    """

    _SCHEMATEXT = """
        @url = threefold.simulation.device
        name** = ""
        description = ""
        device_template_name =
        cost = (N)
        power = (I)
        rackspace_u = (F)
        cru = (F)
        sru = (F)
        hru = (F)
        mru = (F)
        su = (F)
        cu = (F)
        cu_passmark = 0 (I)
        su_perc = (P)
        cu_perc = (P)
        cpr = (I)  #cloud production rate
        cost_su_capex = (N)
        cost_cu_capex = (N)
        cost_power = (N)
        cost_rack = (N)
        cost_month = (N)
        cost_cu_month = (N)
        cost_su_month = (N)

        """

    def _init(self, **kwargs):
        self.device_template_name = kwargs["device_template_name"]
        self.components = j.baseclasses.dict()

    def load(self, simulation, environment=None):
        templ = simulation.device_template_get(self.device_template_name)
        self.cost = 0
        self.power = 0
        self.rackspace_u = 0
        self.cru = 0
        self.sru = 0
        self.hru = 0
        self.mru = 0
        self.su_perc = 0
        self.cu_perc = 0
        self.su = 0
        self.cu = 0
        self.cu_passmark = 0.0
        su_weight = 0.0
        cu_weight = 0.0
        passmark = 0
        for component in templ.components:
            c = simulation.component_get(name=component.name)
            c2 = Component(nr=component.nr, component=c)
            self.cost += c.cost * c2.nr
            self.power += c.power * c2.nr
            self.rackspace_u += c.rackspace_u * c2.nr
            self.cru += c.cru * c2.nr
            self.sru += c.sru * c2.nr
            self.hru += c.hru * c2.nr
            self.mru += c.mru * c2.nr
            passmark += c.passmark * c2.nr
            # not right: needs to be weighted one way or the other
            su_weight += c.su_perc * c2.nr * float(c.cost)
            cu_weight += c.cu_perc * c2.nr * float(c.cost)
            self.components[component.name] = c2
        self.su = self.hru / 1000 / 1.2 + self.sru / 100 / 1.2
        self.cu = min((self.mru - 1) / 4, self.cru * 4)
        self.cu_passmark = passmark / self.cu
        if su_weight or cu_weight:
            self.cu_perc = cu_weight / (su_weight + cu_weight)
            self.su_perc = su_weight / (su_weight + cu_weight)
            self.cost_su_capex = self.cost / self.su * self.su_perc
            self.cost_cu_capex = self.cost / self.cu * self.cu_perc
        if environment:
            self.cost_power = self.power * 24 * 30 / 1000 * float(environment._data.cost_power_kwh)
            self.cost_rack = self.rackspace_u * float(environment._data.cost_rack_unit)
        self.cost_month = self.cost_power + self.cost_rack + self.cost / 60
        if self.cu:
            self.cost_cu_month = self.cost_month / self.cu * self.cu_perc
        if self.su:
            self.cost_su_month = self.cost_month / self.su * self.su_perc
        self.cpr = self.cu * 1.5 + self.su


class Environment(j.baseclasses.object_config):
    """
    x nr of devices in 1 environment
    """

    _SCHEMATEXT = """
        @url = threefold.simulation.environment
        name** = ""
        description = ""
        cost_power_kwh = 0.15 (N)
        cost_rack_unit = 12 (N)
        cost = (N)
        power = (I)
        rackspace_u = (F)
        cru = (F)
        sru = (F)
        hru = (F)
        mru = (F)
        su = (F)
        cu = (F)
        cu_passmark = (I)
        su_perc = (P)
        cu_perc = (P)
        cpr = (I)  #cloud production rate
        cost_su_capex = (N)
        cost_cu_capex = (N)
        cost_power = (N)
        cost_rack = (N)
        cost_month = (N)
        cost_cu_month = (N)
        cost_su_month = (N)
        bandwidth_mbit = (F)
        cost_bandwidth = (N)
        nr_devices = 0
        sales_price_cu = (N)
        sales_price_su = (N)
        sales_price_nu = (N)
        sales_price_total = (N)
        sales_price_cpr_unit = (N)
        """

    def _init(self, **kwargs):
        self.devices = j.baseclasses.dict()
        self.nr_devices = 0

    def device_add(self, name, device, nr):
        self.devices[name] = (nr, device)
        if device.su > 0 or device.cu > 0:
            self.nr_devices += nr
        self._calculate()

    def _calculate(self):
        self.cost = 0
        self.power = 0
        self.rackspace_u = 0
        self.cru = 0
        self.sru = 0
        self.hru = 0
        self.mru = 0
        self.su_perc = 0
        self.cu_perc = 0
        self.su = 0
        self.cu = 0
        su_weight = 0.0
        cu_weight = 0.0
        self.cu_passmark = 0.0
        p_nr = 0
        for nr, device in self.devices.values():
            self.cost += device.cost * nr
            self.power += device.power * nr
            self.rackspace_u += device.rackspace_u * nr
            self.cru += device.cru * nr
            self.sru += device.sru * nr
            self.hru += device.hru * nr
            self.mru += device.mru * nr
            self.su += device.su * nr
            self.cu += device.cu * nr
            # not right: needs to be weighted one way or the other
            su_weight += device.su_perc * nr * float(device.cost)
            cu_weight += device.cu_perc * nr * float(device.cost)
            self.cu_passmark += device.cu_passmark * nr
            if device.cu_passmark:
                p_nr += nr
        self.cu_passmark = self.cu_passmark / p_nr

        if su_weight or cu_weight:
            self.cu_perc = cu_weight / (su_weight + cu_weight)
            self.su_perc = su_weight / (su_weight + cu_weight)
        self.cost_su_capex = self.cost / self.su * self.su_perc
        self.cost_cu_capex = self.cost / self.cu * self.cu_perc
        self.cost_power = self.power * 24 * 30 / 1000 * float(self._data.cost_power_kwh)
        self.cost_rack = self.rackspace_u * float(self._data.cost_rack_unit)
        self.cost_month = self.cost_power + self.cost_rack + self.cost / 60
        self.cost_cu_month = self.cost_month / self.cu * self.cu_perc
        self.cost_su_month = self.cost_month / self.su * self.su_perc
        self.cpr = self.cu * 1.5 + self.su

        self.sales_price_total = self.sales_price_cu * self.cu + self.sales_price_su * self.su
        self.sales_price_cpr_unit = self.sales_price_total / self.cpr


class NodesBatch(j.baseclasses.object_config):
    """
    a normalized node over time
    """

    _SCHEMATEXT = """
        @url = threefold.simulation.nodes
        name** = ""
        cost = (N)
        power = (I)
        cost_power_month = (N)
        cost_rackspace_month = (N)
        rackspace_u = (F)
        cpr = (I)  #cloud production rate
        count = 0 #nr of nodes
        month = 0
        months_max = 60
        sales_price_cpr_unit = 0 (N)
        """

    def nrtokens_farmed(self, growth, month):
        pass


class Simulation(j.baseclasses.object):
    def _init(self, **kwargs):
        # self.nr_nodes_new=[]  #% growth per month
        self.sheet = j.data.worksheets.sheet_new("growth")
        self.nodes_added = []

        result_schema_text = """
        @url = threefold.simulation.result.month
        revenue = (N)
        cost = (N)
        investments_done = (N)
        power_usage_kw =  (I)
        rackspace_usage_u = (I)
        nrnodes_active  = (I)
        """
        self.result_schema = j.data.schema.get_from_text(result_schema_text)

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

    def _interpolate(self, name, args):
        args = [i.strip().split(":") for i in args.split(",") if i.strip()]
        row = self.sheet.addRow(name, nrfloat=2)
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
        nb.sales_price_cpr_unit = environment.sales_price_cpr_unit
        return nb

    def growth_perc_get(self, month):
        return self.sheet.rows["growth_percent"].cells[month] / 100

    def calc(self, nodes_batch_template, nr_start_nodes=1500, months_remaining_start_nodes=36):
        row = self.sheet.addRow("nrnodes_new", nrfloat=0)
        row2 = self.sheet.addRow("nrnodes", nrfloat=0)
        row_rev = self.sheet.addRow("revenue")
        row2.cells[0] = nr_start_nodes
        self._nodes_batch_add(0, nodes_batch_template, nr_start_nodes, months_max=months_remaining_start_nodes)
        for x in range(1, self.sheet.nrcols):
            nr_new = self.growth_perc_get(x) * row2.cells[x - 1]
            row.cells[x] = nr_new
            row2.cells[x] = int(row2.cells[x - 1] + nr_new)
            self._nodes_batch_add(x, nodes_batch_template, nr_new)
            r = self.result_get(x)
            j.shell()

    def _nodes_batch_add(self, month, nodes_batch_template, nr_nodes, months_max=60):
        while len(self.nodes_added) < month + 1:
            self.nodes_added.append(NodesBatch())
        n = self.nodes_added[month]
        # update date from template
        n._data._data_update(nodes_batch_template._data._ddict)
        n.count = nr_nodes
        n.month = month
        n.name = "month_%s" % month
        n.months_max = months_max
        improve = self.sheet.rows["cpr_improve"].cells[month] / 100
        n.cpr = n.cpr * (1 + improve)

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

        r = self.result_schema.new()
        r.revenue = 0
        r.cost = 0
        for i in range(0, month):
            na = self.nodes_added[i]
            if na.month < month and month < na.months_max + 1:
                # now the node batch counts
                r.revenue += na.sales_price_cpr_unit * cpr_sales_price_decline * na.cpr * utilization * na.count
                r.cost += (na.cost / 60 + na.cost_power_month + na.cost_rackspace_month) * na.count
                r.investments_done += na.cost * na.count
                r.power_usage_kw += na.power * na.count / 1000
                r.rackspace_usage_u += na.rackspace_u * na.count
                r.nrnodes_active += na.count

    _SCHEMATEXT = """
        @url = threefold.simulation.nodes
        name** = ""
        cost = (N)
        power = (I)
        cost_power_month = (N)
        cost_rackspace_month = (N)
        rackspace_u = (F)
        cpr = (I)  #cloud production rate
        count = 0 #nr of nodes
        month = 0
        months_max = 60
        sales_price_cpr_unit = 0 (N)
        """
