def bom_populate(bom):
    assert len(bom.components) == 0

    bom.components.new(name="margin1", description="margin per node for threefold and its partners", power=0, cost=400)
    bom.components.new(name="margin2", description="margin per node for threefold and its partners", power=0, cost=900)

    bom.components.new(
        name="chassis",
        description="Chassis for Ryzen CPU (no cpu inside), 4 HD slots, 1 SSD slots, 10 gbit nic",
        cost=300,
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
        name="hd8", description="Seagate Baracuda 8TB (6-8 watt)", cost=200, hru=8000, power=10, su_perc=100
    )
    bom.components.new(
        name="hd12", description="Seagate Baracuda 12TB (6-8 watt)", cost=330, hru=12000, power=10, su_perc=100
    )

    bom.components.new(
        name="amd1",
        description="AMD Ryzen 3 3600X (12 logical cores)",
        cost=240,
        cru=12,
        power=80,
        cu_perc=100,
        passmark=18000,
    )

    bom.components.new(
        name="amd2",
        description="AMD Ryzen 7 3800X (16 logical cores)",
        cost=377,
        cru=16,
        power=105,
        cu_perc=100,
        passmark=24500,
    )

    bom.components.new(name="ssd05", description="0.5 TB SSD", cost=120, sru=500, power=5, su_perc=100)
    bom.components.new(name="ssd1", description="1 TB SSD", cost=240, sru=1000, power=5, su_perc=100)
    bom.components.new(name="mem16_ddr4", description="mem 16GB", cost=140, mru=16, power=8, cu_perc=100)
    bom.components.new(name="mem32_ddr4", description="mem 32GB", cost=220, mru=32, power=10, cu_perc=100)
    bom.components.new(name="mem64_ddr4", description="mem 64GB", cost=400, mru=64, power=16, cu_perc=100)

    bom.components.new(
        name="ng2",
        description="48 ports 10 gbit + 4 ports 10 gbit sfp: fs.com + cables",
        cost=4500,
        power=100,
        rackspace_u=1,
    )

    d = bom.devices.new(name="amd_starter")
    d.components.new(name="chassis", nr=1)
    d.components.new(name="amd1", nr=1)
    d.components.new(name="hd8", nr=1)
    d.components.new(name="mem32_ddr4", nr=1)
    d.components.new(name="ssd05", nr=1)
    d.components.new(name="margin1", nr=1)

    d = bom.devices.new(name="amd_big")
    d.components.new(name="chassis", nr=1)
    d.components.new(name="amd2", nr=1)
    d.components.new(name="hd12", nr=4)
    d.components.new(name="mem64_ddr4", nr=2)
    d.components.new(name="ssd1", nr=1)
    d.components.new(name="margin2", nr=1)

    d = bom.devices.new(name="switch")
    d.components.new(name="ng2", nr=1)

    return bom
