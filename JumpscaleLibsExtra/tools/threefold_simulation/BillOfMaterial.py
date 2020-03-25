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
        if not self.device_template_name and "device_template_name" in kwargs:
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
        sales_price_total = (N)
        sales_price_cpr_unit = (N)
        """

    def _init(self, **kwargs):
        self._cat = "environment"
        self.devices = j.baseclasses.dict()
        self._node_normalized = None
        self.nr_devices = 0
        self._state = "init"

    def _device_add(self, name, device, nr, ttype):
        if name in self.devices:
            raise j.exceptions.Input("device with name:%s already added" % name)
        assert ttype in ["n", "o"]
        self.devices[name] = (nr, device, ttype)
        self.nr_devices += nr
        self._calculate()

    def device_node_add(self, name, device, nr):
        self._device_add(name, device, nr, "n")
        self.nr_nodes += nr

    def device_overhead_add(self, name, device, nr):
        self._device_add(name, device, nr, "o")

    def _node_normalized_get(self):
        devicesfound = []
        for nr, device, ttype in self.devices.values():
            if ttype == "n":
                devicesfound.append((nr, device))
        if len(devicesfound) == 0:
            raise j.exceptions.Input("did not find a device in he environment, cannot calculate node normalized")
        else:
            return devicesfound

    @property
    def node_normalized(self):
        """
        add all nodes which can deal with workloads and create avg node out of it
        easier to deal with in simulation
        """
        if not self._node_normalized:
            devices = self._node_normalized_get()
            device_n = Device()
            nrnodes = 0
            propnames = [
                "cu_passmark",
                "cpr",
                "cru",
                "sru",
                "hru",
                "mru",
                "su",
                "cu",
                "cu_perc",
                "su_perc",
            ]
            propnames_env = [
                "rackspace_u",
                "cost_rack",
                "cost_power",
                "cost_month",
                "cost",
                "power",
            ]
            propnames_copy = [
                "cost_cu_month",
                "cost_su_month",
                "cost_su_capex",
                "cost_cu_capex",
            ]
            for propname in propnames + propnames_env + propnames_copy:
                setattr(device_n, propname, 0.0)

            for nr, device in devices:
                nrnodes += nr
                for propname in propnames:
                    val_sum = getattr(device_n, propname)
                    val = getattr(device, propname) * nr
                    val_sum += val
                    setattr(device_n, propname, val_sum)

            for propname in propnames:
                val_sum = getattr(device_n, propname) / nrnodes
                setattr(device_n, propname, val_sum)

            for propname in propnames_env:
                val_sum = getattr(self, propname) / nrnodes
                setattr(device_n, propname, val_sum)

            for propname in propnames_copy:
                setattr(device_n, propname, getattr(self, propname))

            self._node_normalized = device

        return self._node_normalized

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
        for nr, device, ttype in self.devices.values():
            self.cost += device.cost * nr
            self.power += device.power * nr
            self.rackspace_u += device.rackspace_u * nr
            if ttype == "n":
                self.cru += device.cru * nr
                self.sru += device.sru * nr
                self.hru += device.hru * nr
                self.mru += device.mru * nr
                self.su += device.su * nr
                self.cu += device.cu * nr
                # not 100% right: needs to be weighted one way or the other
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

    def sales_price_cpr_unit_get(self, simulation, month=0):
        cpr_sales_price_decline = simulation.cpr_sales_price_decline_get(month)
        sales_price_total = simulation.sales_price_cu * self.cu + simulation.sales_price_su * self.su
        sales_price_cpr_unit = (sales_price_total / self.cpr) / (1 + cpr_sales_price_decline)
        return sales_price_cpr_unit
