from Jumpscale import j


def bom_calc(bom, environment):

    assert len(bom.components) == 0

    bom.components.new(name="margin", description="margin per node for threefold and its partners", power=0, cost=500)

    bom.components.new(
        name="s2",
        description="Chassis for Ryzen 7 (no cpu inside), 4 HD slots, 1 SSD slots, 10 gbit nic",
        cost=450,
        rackspace_u=2,
        cru=0,
        sru=0,
        hru=0,
        mru=0,
        su_perc=0,
        cu_perc=0,
        power=30,
    )

    bom.components.new(
        name="hd12", description="Seagate Baracuda 12TB (6-8 watt)", cost=330, hru=12000, power=10, su_perc=100
    )

    bom.components.new(
        name="amd1",
        description="AMD Ryzen 7 3800X (16 logical cores)",
        cost=377,
        cru=16,
        power=105,
        cu_perc=100,
        passmark=24500,
    )

    bom.components.new(name="ssd1", description="1 TB Samsung Evo", cost=350, sru=1000, power=5, su_perc=100)
    bom.components.new(name="mem32_ecc", description="mem 32", cost=300, mru=32, power=8, cu_perc=100)
    bom.components.new(name="mem64_ddr4", description="mem 2x32", cost=400, mru=64, power=16, cu_perc=100)
    bom.components.new(
        name="ng2",
        description="48 ports 10 gbit + 4 ports 10 gbit sfp: fs.com + cables",
        cost=4500,
        power=100,
        rackspace_u=1,
    )

    d = bom.devices.new(name="server")
    d.components.new(name="s2", nr=1)
    d.components.new(name="amd1", nr=1)
    d.components.new(name="hd12", nr=5)
    # total mem = 128 GB
    d.components.new(name="mem64_ddr4", nr=2)
    d.components.new(name="ssd1", nr=1)
    d.components.new(name="margin", nr=1)

    d = bom.devices.new(name="switch")
    d.components.new(name="ng2", nr=1)

    # see the bill of material sheet to define the devices
    server = bom.device_get("server", device_template_name="server", environment=environment)
    # the switch added to the node
    switch = bom.device_get("switch", device_template_name="switch", environment=environment)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("server", server, 20)
    environment.device_overhead_add("switch", switch, 2)

    return bom, environment
