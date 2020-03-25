from Jumpscale import j


def bom_calc(bom, environment):

    raise RuntimeError("to be implemented")
    assert len(bom.components) == 0

    bom.components.new(
        name="s1",
        description="HPE Aopollo 4510 INTEL 4 U, 60 HD's fit inside, 10 gbit dual",
        cost=7100,
        rackspace_u=4,
        cru=0,
        sru=0,
        hru=0,
        mru=0,
        su_perc=90,
        cu_perc=10,
        power=150,
    )

    bom.components.new(name="margin", description="margin per node for threefold and its partners", power=0, cost=500)

    bom.components.new(
        name="hd12", description="HPE Helium 12TB (6-8 watt)", cost=734, hru=12000, power=10, su_perc=100
    )
    bom.components.new(
        name="intel1",
        description="INTEL Xeon Silver 4208 @ 2.10GHz (16 logical cores)",
        cost=872,
        cru=16,
        power=100,
        cu_perc=100,
        passmark=12047,
    )

    bom.components.new(name="ssd1", description="1.92 TB HPE SSD", cost=1022, sru=1920, power=10, su_perc=100)
    bom.components.new(name="mem32_ecc", description="mem 32", cost=320, mru=32, power=8, cu_perc=100)

    bom.components.new(
        name="ng2",
        description="48 ports 10 gbit + 4 ports 10 gbit sfp: fs.com + cables",
        cost=4500,
        power=100,
        rackspace_u=1,
    )

    # create the template for dc1
    d = bom.devices.new(name="server")
    d.components.new(name="s1", nr=1)
    d.components.new(name="intel1", nr=2)
    d.components.new(name="hd12", nr=56)
    d.components.new(name="mem32_ecc", nr=8)
    d.components.new(name="ssd1", nr=3)

    d = bom.devices.new(name="switch")
    d.components.new(name="ng2", nr=1)

    environment.devices.clear()

    # see the bill of material sheet to define the devices
    # edge device is our std node (in this simulation about 4.5k USD investment per node)
    server = bom.device_get("server", environment=environment)
    # the switch added to the node
    switch = bom.device_get("switch", environment=environment)

    # an environment to simulate the overhead per node (eg. 1 switch per node)
    environment.device_node_add("server", server, 20)
    environment.device_overhead_add("switch", switch, 2)

    return bom, environment
