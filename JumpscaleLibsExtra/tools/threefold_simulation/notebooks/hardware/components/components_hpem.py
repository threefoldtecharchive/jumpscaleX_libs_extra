def bom_populate(bom):
    
    bom.components.new(
        name="s0",
        description="HPE ProLiant MicroServer Gen10 Plus E-2224 + Smart Array + SATA converter", 
        cost=(699.11+174.78+7.89+33.67),
        rackspace_u=1,  # Rackspace unit set to 0 to mimic the perk to the tennant that needs to be included in the modeling
        cru=0,
        sru=0,
        hru=0,
        mru=16,
        su_perc=50,
        cu_perc=50,
        power=150,
    )
    
    bom.components.new(
        name="s1",
        description="HPE ML30 INTEL, 4U Tower, 8 HD's fit inside, 1 gbit dual",
        cost=378,
        rackspace_u=0,
        cru=0,
        sru=0,
        hru=0,
        mru=0,
        su_perc=50,
        cu_perc=50,
        power=150,
    )
    
    bom.components.new(
        name="s2",
        description="HPE ML110 INTEL, 4U Tower, 8 HD's fit inside, 1 gbit dual",
        cost=454,
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
    
    bom.components.new(name="license", description="HPE iLO Advanced 1-server License with 3yr Support on iLO Licensed Features", power=0, cost=260.44
    )

    bom.components.new(
        name="hd12", description="HPE 12TB SATA 6G Midline 7.2K LFF (6-8 watt)", cost=350, hru=12000, power=10, su_perc=100
    )
    bom.components.new(
        name="hd4", description="HPE 4TB SATA 6G Midline 7.2K LFF (3.5in) RW 1yr Wty", cost=180.56, hru=4000, power=10, su_perc=100
    )
    
    bom.components.new(
        name="intel1",
        description="Intel Xeon E-2224 (3.4GHz/4-core/71W) (4 logical cores)",
        cost=296,
        cru=4,
        power=80,
        cu_perc=100,
        passmark=8202,
    )
    
    bom.components.new(
        name="intel2",
        description="Intel Xeon-Silver 4208 (2.1GHz/8-core/85W) (16 logical cores)",
        cost=576,
        cru=16,
        power=85,
        cu_perc=100,
        passmark=13867,
    )
    
    bom.components.new(
        name="intel3",
        description="Intel Xeon-Silver 4216 (2.1GHz/16-core/100W) (32 logical cores)",
        cost=1041,
        cru=16,
        power=100,
        cu_perc=100,
        passmark=20656,
    )

    bom.components.new(name="ssd240", description="240 GB HPE SSD", cost=200.33, sru=240, power=10, su_perc=100)
    bom.components.new(name="ssd1", description="960 GB HPE SSD", cost=180, sru=1920, power=10, su_perc=100)
    
    bom.components.new(name="mem16_ecc", description="mem 16", cost=144.78, mru=16, power=8, cu_perc=100)
    
    bom.components.new(name="mem32_ecc", description="mem 32", cost=220, mru=32, power=8, cu_perc=100)
    
    #bom.components.new(name="sas_contr", description="HPE Smart Array E208i-p SR Gen10 (8 Internal Lanes/No Cache)", cost=60, power=20, su_perc=100) 
    
    #bom.components.new(name="power_supply", description="350 Power Supply", cost=16, power=0, cu_perc=50, su_perc=50)
    
    #bom.components.new(name="sas_cable", description="sas cable kit", cost=33, power=0, su_perc=100)
    
    #bom.components.new(name="front_fan", description="front fan kit", cost=44, power=0, cu_perc=50, su_perc=50)

    bom.components.new(
        name="ng2",
        description="48 ports 10 gbit + 4 ports 10 gbit sfp: fs.com + cables",
        cost=1,
        power=100,
        rackspace_u=1,
    )
    
    # create the template microserver
    d = bom.devices.new(name="hpe_microserver")
    d.components.new(name="s0", nr=1)
    d.components.new(name="intel1", nr=1)
    d.components.new(name="hd4", nr=3)
    d.components.new(name="mem16_ecc", nr=1)
    d.components.new(name="ssd240", nr=1)
    d.components.new(name="license", nr=1)
    d.components.new(name="margin", nr=1)
    #d.components.new(name="sas_contr", nr=1)
    #d.components.new(name="power_supply", nr=1)
    #d.components.new(name="sas_cable", nr=1)
    #d.components.new(name="front_fan", nr=1)
    
    # create the template ml30
    d = bom.devices.new(name="hpe_compute_tower_ml30")
    d.components.new(name="s1", nr=1)
    d.components.new(name="intel1", nr=1)
    d.components.new(name="hd12", nr=2)
    d.components.new(name="mem16_ecc", nr=1)
    d.components.new(name="ssd1", nr=1)
    #d.components.new(name="sas_contr", nr=1)
    #d.components.new(name="power_supply", nr=1)
    #d.components.new(name="sas_cable", nr=1)
    #d.components.new(name="front_fan", nr=1)
  

    # create the template ml110 8core
    d = bom.devices.new(name="hpe_compute_tower_ml110_8")
    d.components.new(name="s2", nr=1)
    d.components.new(name="intel2", nr=1)
    d.components.new(name="hd12", nr=2)
    d.components.new(name="mem32_ecc", nr=2)
    d.components.new(name="ssd1", nr=1)
    #d.components.new(name="sas_contr", nr=1)
    #d.components.new(name="power_supply", nr=1)
    
    # create the template ml110 16core
    d = bom.devices.new(name="hpe_compute_tower_ml110_16")
    d.components.new(name="s2", nr=1)
    d.components.new(name="intel3", nr=1)
    d.components.new(name="hd12", nr=2)
    d.components.new(name="mem32_ecc", nr=2)
    d.components.new(name="ssd1", nr=1)
    #d.components.new(name="sas_contr", nr=1)
    #d.components.new(name="power_supply", nr=1)

    d = bom.devices.new(name="switch_48")
    d.components.new(name="ng2", nr=1)
    
    return bom
