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
        self.environment = kwargs["environment"]

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

    # def device_get(self, name, device_template_name=None, description=""):
    #     """
    #     get device
    #     :param name:
    #     :return:
    #     """
    #     if not device_template_name:
    #         device_template_name = name
    #     d = Device(name=name, description=description, device_template_name=device_template_name)
    #     return d


    def markdown_get(self,path):
        json_txt=self._data._json
        j.sal.fs.writeFile(f"{path}/bom.json", json_txt)
        data = self._data._ddict
        j.tools.jinja2.template_render(path=f"{self._dirpath}/templates/bom.md",dest=f"{path}/bom.md",data=self._data,trim_blocks=True)


class Component(j.baseclasses.object):
    def _init(self, **kwargs):
        self.nr = kwargs["nr"]
        self.component = kwargs["component"]

    def __str__(self):
        return f"{self.nr} * {self.component}"

    __repr__ = __str__


class DeviceEnvBase(SimulatorBase):

    _SCHEMATEXT = """
        @url = threefold.simulation.device_or_environment
        name = ""
        description = ""
        device_template_name = ""

        production = (O) !threefold.simulation.bom.production
        total = (O) !threefold.simulation.bom.total
        costunits = (O) !threefold.simulation.bom.costunits
        layout = (O) !threefold.simulation.bom.layout     
        params = (O) !threefold.simulation.bom.params           
        

        #aggregation for nodes only (the ones who deliver cloud units)
        @url = threefold.simulation.bom.production        
        cpr = 0 (I)  #cloud production rate        
        cru = 0 (I)
        sru = 0 (I)
        hru = 0 (I)
        mru = 0 (I)
        su = 0 (F)
        cu = 0 (F)
        nu_used_month = 0 (I)
        cu_perc = 0 (P)
        su_perc = 0 (P)
        cu_passmark = 0 (I)
        #special one is the multiplication of GB transfered with the cost of 1 NU
        cost_nu_month = 0 (N)

        #aggregation over all devices in env (nodes + overhead)
        @url = threefold.simulation.bom.total
        cost_hardware = 0 (N)
        power = 0 (I)
        power_kwh_month = 0 (I)
        rackspace_u = 0 (F)
        cost_hardware_month = 0 (N)
        cost_rack_month = 0 (N)
        cost_power_month = 0 (N)        
        cost_maintenance_month = 0 (N)
        cost_total_month = 0 (N)

        #no aggregation for device same as for environment
        @url = threefold.simulation.bom.costunits
        cost_cu_month = 0 (F)
        cost_su_month = 0 (F)
        cost_nu_month = 0 (F)        
        cost_su_capex = 0 (F)
        cost_cu_capex = 0 (F)

        #make distinction between overhead and production nodes        
        @url = threefold.simulation.bom.layout
        nr_devices_overhead = 0 (I)
        nr_devices_production = 0 (I)
        devices_production = [] (LS)
        devices_overhead = [] (LS)
        
        @url = threefold.simulation.bom.params
        cost_power_kwh = 0.15 (N)
        cost_rack_unit = 12 (N)
        cost_mbitsec_month = 2 (N)
        cost_maintenance_percent_of_hw = 10 (I)
        months_writeoff = 60 (I)         

        """

    @property
    def _property_names(self):
        """

        production, total, costunits, params = self._property_names

        """
        production = [p.name for p in self._data.production._schema.properties]
        total = [p.name for p in self._data.total._schema.properties]
        costunits = [p.name for p in self._data.costunits._schema.properties]
        params = [p.name for p in self._data.params._schema.properties]
        return (production, total, costunits, params)

    def clear(self):

        production_names, total_names, costunits_names, param_names = self._property_names

        for propname in production_names:
            setattr(self.production, propname, 0.0)
        for propname in total_names:
            setattr(self.total, propname, 0.0)
        for propname in costunits_names:
            setattr(self.costunits, propname, 0.0)

    def markdown_get(self,path,name=None):
        json_txt=self._data._json
        if not name:
            name=self.name
        if name.startswith("device_"):
            name=name[7:]
        j.sal.fs.writeFile(f"{path}/device_{name}.json", json_txt)
        data = self._data._ddict
        j.tools.jinja2.template_render(path=f"{self._dirpath}/templates/device.md",dest=f"{path}/device_{name}.md",data=self._data,trim_blocks=True)


    @property
    def nodes_all_count(self):
        return self.layout.nr_devices_overhead + self.layout.nr_devices_production

    @property
    def nodes_production_count(self):
        return self.layout.nr_devices_production


class Device(DeviceEnvBase):
    """
    a device which can be used to build a cloud with
    """

    def _init(self, bom=None, environment=None, template=None, normalized=False, **kwargs):
        self._cat = "device"
        if not normalized:
            template = bom.device_template_get(template)
            self.device_template_name = template.name
        else:
            self.device_template_name = "normalized"
        self.components = j.baseclasses.dict()
        self._calculated = False
        if not normalized:
            self._calc(bom=bom, environment=environment)

    def nu_calc(self, environment):
        """
        calculate the cost of 1 network unit
        """
        # how many GB per month can one mbit transfer if used 50% of time
        nrGB_month = 1 * 0.5 * (3600 * 24 * 30) / (1024 * 8)
        self.costunits.cost_nu_month = environment.params.cost_mbitsec_month / nrGB_month
        config = j.tools.tfgrid_simulator.simulator_config.network
        self.production.nu_used_month = (
            config.nu_multiplier_from_cu * self.production.cu + config.nu_multiplier_from_su * self.production.su
        )
        # self.cost_nu_month = nrnu * self.cost_nu

    def _calc(self, bom, environment=None):
        assert self._calculated == False
        templ = bom.device_template_get(self.device_template_name)
        self.clear()
        passmark = 0.0
        su_weight = 0.0
        cu_weight = 0.0
        for component in templ.components:
            c = bom.component_get(name=component.name)
            c2 = Component(nr=component.nr, component=c)
            self.total.cost_hardware += float(c.cost) * c2.nr
            self.total.power += float(c.power) * c2.nr
            self.total.rackspace_u += c.rackspace_u * c2.nr
            self.production.cru += c.cru * c2.nr
            self.production.sru += c.sru * c2.nr
            self.production.hru += c.hru * c2.nr
            self.production.mru += c.mru * c2.nr
            passmark += c.passmark * c2.nr
            # not right: needs to be weighted one way or the other
            su_weight += float(c.cost * c2.nr * c.su_perc)
            cu_weight += float(c.cost * c2.nr * c.cu_perc)
            self.components[component.name] = c2

        #these are suggested farming rules for end 2020, aim is that the cost of acquiring reflects generation of SU
        #aug 2020, a SSD is roughly 5x more expensive as a HDD, hence sru / 200 in stead of original / 100
        #we don't change in farming (minting) code because this can only be suggested once a year
        #to have it already in simulator is the most prudent thing to do
        self.production.su = self.production.hru / 1000 / 1.2 + self.production.sru / 100 / 2 / 1.2
        self.production.cu = min((self.production.mru - 1) / 4, self.production.cru * 2)
        self.production.cu_passmark = passmark / self.production.cu
        if su_weight or cu_weight:
            self.production.cu_perc = cu_weight / (su_weight + cu_weight)
            self.production.su_perc = su_weight / (su_weight + cu_weight)
            self.costunits.cost_cu_capex = self.total.cost_hardware / self.production.cu * self.production.cu_perc
            self.costunits.cost_su_capex = self.total.cost_hardware / self.production.su * self.production.su_perc

        if environment:
            self.nu_calc(environment)
            self.total.power_kwh_month = self.total.power * 24 * 30 / 1000
            self.total.cost_power_month = self.total.power_kwh_month * float(environment._data.params.cost_power_kwh)

            self.total.cost_rack_month = self.total.rackspace_u * float(environment._data.params.cost_rack_unit)

            self.total.cost_hardware_month = self.total.cost_hardware / environment._data.params.months_writeoff
            self.total.cost_maintenance_month = (
                self.total.cost_hardware_month * environment._data.params.cost_maintenance_percent_of_hw / 100
            )
            self.total.cost_total_month = (
                self.total.cost_power_month
                + self.total.cost_rack_month
                + self.total.cost_hardware_month
                + self.total.cost_maintenance_month
            )
            if self.production.cu:
                self.costunits.cost_cu_month = (
                    self.total.cost_total_month / self.production.cu * self.production.cu_perc
                )
            if self.production.su:
                self.costunits.cost_su_month = (
                    self.total.cost_total_month / self.production.su * self.production.su_perc
                )
            self.production.cost_nu_month = float(self.costunits.cost_nu_month) * self.production.nu_used_month

        self.production.cpr = self.production.cu * 1.5 + self.production.su

        self.params = environment.params

        self._calculated = True


class Environment(DeviceEnvBase):
    """
    x nr of devices in 1 environment
    """

    # def __init__(self, **kwargs):
    #     Device.__init__(self, **kwargs)

    def _init(self, **kwargs):
        self._cat = "environment"
        self.devices = j.baseclasses.dict()
        self._state = "init"

        assert self.name
        self.bom = BillOfMaterial(self.name, environment=self)
        exec(f"from hardware.{self.name} import bom_calc", globals())
        bom_calc(environment=self)
        assert self.params.cost_power_kwh > 0
        assert self.params.months_writeoff > 20
        assert self.layout.nr_devices_production > 0
        self._calcdone = False

    def device_node_add(self, name, template=None, nr=None):
        assert template
        assert isinstance(template, str)
        assert nr
        assert nr > 0
        if name in self.devices:
            raise j.exceptions.Input("device with name:%s already added" % name)
        device = Device(name=name, template=template, bom=self.bom, environment=self)
        device.layout.nr_devices_production = nr
        self.layout.nr_devices_production += nr
        self.devices[name] = device
        self.layout.devices_production.append(f"{device.name}*{nr}")

    def device_overhead_add(self, name, template=None, nr=None):
        assert template
        assert isinstance(template, str)
        assert nr
        assert nr > 0
        if name in self.devices:
            raise j.exceptions.Input("device with name:%s already added" % name)
        device = Device(name=name, template=template, bom=self.bom, environment=self)
        device.layout.nr_devices_overhead = nr
        self.layout.nr_devices_overhead += nr
        self.devices[name] = device
        self.layout.devices_overhead.append(f"{device.name}*{nr}")

    @property
    def nodes_production(self):
        devicesfound = []
        for device in self.devices.values():
            if device.layout.nr_devices_production > 0:
                assert device.layout.nr_devices_overhead == 0
                devicesfound.append(device)
        if len(devicesfound) == 0:
            raise j.exceptions.Input("did not find a device in he environment, cannot calculate node normalized")
        else:
            return devicesfound

    @property
    def nr_nodes(self):
        return len(self.layout.nr_devices_production)

    @property
    def nodes_overhead(self):
        devicesfound = []
        for device in self.devices.values():
            if device.layout.nr_devices_overhead > 0:
                assert device.layout.nr_devices_production == 0
                devicesfound.append(device)
        return devicesfound

    @property
    def nodes_all(self):
        return [d for d in self.devices.values()]

    def calc(self):

        assert self._calcdone == False

        su_weight = 0.0
        cu_weight = 0.0
        self.clear()

        production_names, total_names, costunits_names, param_names = self._property_names

        # sum for all production values
        for device in self.nodes_production:

            for propname in production_names:
                val_sum = getattr(self.production, propname)
                val = getattr(device.production, propname) * device.nodes_production_count
                val_sum += val
                setattr(self.production, propname, val_sum)

            su_weight += float(device.layout.nr_devices_production * device.production.su_perc)
            cu_weight += float(device.layout.nr_devices_production * device.production.cu_perc)

        # aggregate for all nodes
        for device in self.nodes_all:

            for propname in total_names:
                val_sum = getattr(self.total, propname)
                val = getattr(device.total, propname) * device.nodes_all_count
                val_sum += val
                setattr(self.total, propname, val_sum)

        # just copy
        for device in self.nodes_all:

            for propname in costunits_names:
                setattr(self.costunits, propname, getattr(device.costunits, propname))

        if su_weight or cu_weight:
            self.production.cu_perc = cu_weight / (su_weight + cu_weight)
            self.production.su_perc = su_weight / (su_weight + cu_weight)
            self.costunits.cost_cu_capex = self.total.cost_hardware / self.production.cu * self.production.cu_perc
            self.costunits.cost_su_capex = self.total.cost_hardware / self.production.su * self.production.su_perc
            self.costunits.cost_cu_month = self.total.cost_total_month / self.production.cu * self.production.cu_perc
            self.costunits.cost_su_month = self.total.cost_total_month / self.production.su * self.production.su_perc
            self.production.cost_nu_month = float(self.costunits.cost_nu_month) * self.production.nu_used_month

        # calculate the normalized node
        device = Device(normalized=True)
        device.name = "normalized_device_%s" % self.name.lower().replace("_", ".")
        device.clear()  # make sure its empty

        # normalize to 1 node, so device by nr of nodes for above properties
        nrnodes = self.nodes_production_count
        for propname in production_names:
            setattr(device.production, propname, getattr(self.production, propname) / nrnodes)

        for propname in total_names:
            setattr(device.total, propname, getattr(self.total, propname) / nrnodes)

        for propname in param_names:
            setattr(device.params, propname, getattr(device.params, propname))

        for propname in costunits_names:
            setattr(device.costunits, propname, getattr(self.costunits, propname))

        device.layout.nr_devices_production = 1
        device.production.cu_perc = self.production.cu_perc
        device.production.su_perc = self.production.su_perc

        self.node_normalized = device

        self._calcdone = True

    def markdown_env_detail_get(self,path):
        self.markdown_node_detail_get(path=path)
        #now report on the environment TODO:

    def markdown_node_detail_get(self,path,name=None):
        self.node_normalized.markdown_get(path=path,name="normalized")
