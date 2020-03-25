from Jumpscale import j


def bom_calc(bom, environment):

    assert len(bom.components) == 0

    bom.components.new(
        name="s1",
        description="SuperMicro Chassis 4U, 36 HD's fit inside, 10 gbit dual",
        cost=2335,
        rackspace_u=4,
        cru=0,
        sru=0,
        hru=0,
        mru=0,
        su_perc=90,
        cu_perc=10,
        power=60,
    )

    bom.components.new(name="margin", description="margin per node for threefold and its partners", power=0, cost=500)

    bom.components.new(
        name="hd12", description="Seagate Baracuda 12TB (6-8 watt)", cost=350, hru=12000, power=10, su_perc=100
    )
    bom.components.new(
        name="intel1",
        description="Intel Xeon Broadwell-EP R3 8CE5-2609 V4 1.7GHz (8 logical cores)",
        cost=310,
        cru=8,
        power=135,
        cu_perc=100,
        passmark=5385,
    )

    bom.components.new(name="ssd1", description="1 TB Samsung Evo", cost=305, sru=1000, power=5, su_perc=100)
    bom.components.new(name="mem16_ecc", description="mem 16", cost=300, mru=16, power=8, cu_perc=100)

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
    d.components.new(name="intel1", nr=1)
    d.components.new(name="hd12", nr=18)
    d.components.new(name="mem32_ecc", nr=2)
    d.components.new(name="ssd1", nr=1)

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
