from Jumpscale import j

from .SimulatorBase import SimulatorBase


class BillOfMaterial(SimulatorBase):
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

    def _init(self, **kwargs):
        self._cat = "bom"

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


class Device(SimulatorBase):
    """
    a device which can be used to build a cloud with
    """

    _SCHEMATEXT = """
        @url = threefold.simulation.device
        name = ""
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
        self._cat = "device"
        if not self.device_template_name:
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
            su_weight += float(c.cost * c2.nr * c.su_perc)
            cu_weight += float(c.cost * c2.nr * c.cu_perc)
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


class Environment(SimulatorBase):
    """
    x nr of devices in 1 environment
    """

    _SCHEMATEXT = """
        @url = threefold.simulation.environment
        name = ""
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
        # bandwidth_mbit = (F)
        # cost_bandwidth = (N)
        nr_devices = 0
        nr_nodes = 0
        sales_price_cu = (N)
        sales_price_su = (N)
        sales_price_nu = (N)
        sales_price_total = (N)
        sales_price_cpr_unit = (N)
        """

    def _init(self, **kwargs):
        self._cat = "environment"
        self.devices = j.baseclasses.dict()
        self._device_types = {}
        self._device_normalized = None
        self.nr_devices = 0
        self._state = "init"

    def _device_add(self, name, device, nr):
        if name in self.devices:
            raise j.exceptions.Input("device with name:%s already added" % name)
        self.devices[name] = (nr, device)
        if device.su > 0 or device.cu > 0:
            self.nr_devices += nr
        self._calculate()

    def device_node_add(self, name, device, nr):
        self._device_add(name, device, nr)
        self._device_types[name] = "n"
        self.nr_nodes += nr

    def device_overhead_add(self, name, device, nr):
        self._device_add(name, device, nr)
        self._device_types[name] = "o"

    def _device_normalized_get(self):
        nr2 = 0
        devicefound = None
        for nr, device in self.devices.values():
            if self._device_types[device.name] == "n":
                nr2 += 1
                devicefound = device
        if nr2 == 1:
            return devicefound
        raise j.exceptions.Input("today only support 1 type of node device in environment")

    @property
    def device_normalized(self):
        if not self._device_normalized:
            device = self._device_normalized_get()
            device_n = Device(jsxobject=device._data)
            device_n.cost_cu_month = self.cost_cu_month
            device_n.cost_su_month = self.cost_su_month
            device_n.rackspace_u = self.rackspace_u / self.nr_nodes
            device_n.cu_passmark = self.cu_passmark / self.nr_nodes
            device_n.cost_rack = self.cost_rack / self.nr_nodes
            device_n.cost_power = self.cost_power / self.nr_nodes
            device_n.cost_month = self.cost_month / self.nr_nodes
            device_n.cpr = self.cpr / self.nr_nodes
            device_n.cost_su_capex = self.cost_su_capex
            device_n.cost_cu_capex = self.cost_cu_capex

            device_n.cost = self.cost / self.nr_nodes
            device_n.power = self.power / self.nr_nodes
            device_n.cru = self.cru / self.nr_nodes
            device_n.sru = self.sru / self.nr_nodes
            device_n.hru = self.hru / self.nr_nodes
            device_n.mru = self.mru / self.nr_nodes

            device_n.su = self.su / self.nr_nodes
            device_n.cu = self.cu / self.nr_nodes
            device_n.cu_passmark = self.cu_passmark / self.nr_nodes
            self._device_normalized = device
        return self._device_normalized

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
