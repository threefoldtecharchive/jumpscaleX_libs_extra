def bom_populate(bom):
    
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
    bom.components.new(name="ssd2", description="2 TB Samsung Evo", cost=740, sru=2000, power=5, su_perc=100)
    
    bom.components.new(name="mem16_ecc", description="mem 16", cost=300, mru=16, power=8, cu_perc=100)    
    bom.components.new(name="mem32_ecc", description="mem 32", cost=600, mru=32, power=8, cu_perc=100)    

    bom.components.new(
        name="ng2",
        description="48 ports 10 gbit + 4 ports 10 gbit sfp: fs.com + cables",
        cost=4500,
        power=100,
        rackspace_u=1,
    )

    # create the template for dc1
    d = bom.devices.new(name="storage_server")
    d.components.new(name="s1", nr=1)
    d.components.new(name="intel1", nr=1)
    d.components.new(name="hd12", nr=18)
    d.components.new(name="mem32_ecc", nr=2)
    d.components.new(name="ssd1", nr=1)

    
    # create the templates for the devices
    d = bom.devices.new(name="archive_compute_frontend")
    d.components.new(name="s1", nr=1)
    d.components.new(name="intel1", nr=1)
    d.components.new(name="hd12", nr=0)
    d.components.new(name="mem16_ecc", nr=4)
    d.components.new(name="ssd1", nr=12)

    d = bom.devices.new(name="switch_48")
    d.components.new(name="ng2", nr=1)
    
    return bom