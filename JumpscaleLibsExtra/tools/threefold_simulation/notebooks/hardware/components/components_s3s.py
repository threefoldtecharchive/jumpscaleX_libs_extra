def bom_populate(bom):
    
    bom.components.new(
        name="s1",
        description="Stingy Bee Small all in one box eur pricing",
        cost=499,
        rackspace_u=0,
        cru=0,
        sru=256,
        hru=0,
        mru=8,
        su_perc=50,
        cu_perc=50,
        power=120,
    )
    
    bom.components.new(
        name="s2",
        description="AR chassis, eur pricing",
        cost=539,
        rackspace_u=0,
        cru=0,
        sru=0,
        hru=0,
        mru=0,
        su_perc=50,
        cu_perc=50,
        power=120,
    )
    
    bom.components.new(
        name="s3",
        description="Fractal case, Asrock M-ITX, eur pricing",
        cost=841,
        rackspace_u=0,
        cru=0,
        sru=0,
        hru=0,
        mru=0,
        su_perc=50,
        cu_perc=50,
        power=120,
    )
   
    bom.components.new(name="margin", description="margin per node for threefold and its partners", power=0, cost=500)

    bom.components.new(name="hd4", description="Seagate 3.5'' 4TB SATA Barracuda", cost=95, hru=4000, power=10, su_perc=100)
    
    bom.components.new(name="hd2", description="Seagate 2.5'' 2TB SATA Barracuda", cost=80, hru=2000, power=10, su_perc=100)
    
    bom.components.new(
        name="amd1",
        description="AMD Ryzen 5 3400GE 3,4Gz 6-Cores Socket AM4 + Cooler (8 logical cores)",
        cost=145,
        cru=8,
        power=80,
        cu_perc=100,
        passmark=9407,
    )
    
    bom.components.new(
        name="amd2",
        description="AMD Ryzen 5 3600 3,4Gz 6-Cores Socket AM4 + Cooler (12 logical cores)",
        cost=180,
        cru=12,
        power=80,
        cu_perc=100,
        passmark=17790,
    )
    
    bom.components.new(
        name="intel1",
        description="Intel Core i5-5257U 2,7 GHz (4 logical cores)",
        cost=0,
        cru=4,
        power=80,
        cu_perc=100,
        passmark=3269,
    )
        
    
    bom.components.new(name="ssd1", description="Intenso 512GB SSD 2.5", cost=70, sru=512, power=10, cu_perc=100)
    
    bom.components.new(name="mem32_ecc", description="Samsung 2 x 16 DDR4", cost=150, mru=32, power=8, cu_perc=100)
    
    bom.components.new(name="mem64_ecc", description="Corsair 2 x 32 DDR4", cost=220, mru=64, power=8, cu_perc=100)
    
    bom.components.new(
        name="ng2",
        description="48 ports 10 gbit + 4 ports 10 gbit sfp: fs.com + cables",
        cost=1,
        power=100,
        rackspace_u=1,
    )

    # create the template small
    d = bom.devices.new(name="small")
    d.components.new(name="s1", nr=1)
    d.components.new(name="intel1", nr=1)
    d.components.new(name="hd2", nr=1)
    #d.components.new(name="mem32_ecc", nr=1)
    #d.components.new(name="ssd1", nr=1)

    # create the template medium
    d = bom.devices.new(name="medium")
    d.components.new(name="s2", nr=1)
    d.components.new(name="amd1", nr=1)
    d.components.new(name="hd4", nr=1)
    d.components.new(name="mem32_ecc", nr=1)
    d.components.new(name="ssd1", nr=1)
    
    # create the template large
    d = bom.devices.new(name="large")
    d.components.new(name="s3", nr=1)
    d.components.new(name="amd2", nr=1)
    d.components.new(name="hd4", nr=2)
    d.components.new(name="mem64_ecc", nr=1)
    d.components.new(name="ssd1", nr=1)
     
    d = bom.devices.new(name="switch_48")
    d.components.new(name="ng2", nr=1)
    
    return bom
