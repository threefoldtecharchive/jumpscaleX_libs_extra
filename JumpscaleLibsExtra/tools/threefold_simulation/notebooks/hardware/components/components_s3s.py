def bom_populate(bom):
    
    bom.components.new(
        name="s1",
        description="SN1 Chassis sm tower, gigabyte motherboard, eur pricing",
        cost=414,
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
        description="SN2, SN3 Chassis sm tower, gigabyte motherboard, eur pricing",
        cost=445,
        rackspace_u=0,
        cru=0,
        sru=0,
        hru=0,
        mru=0,
        su_perc=50,
        cu_perc=50,
        power=150,
    )

    bom.components.new(name="margin", description="margin per node for threefold and its partners", power=0, cost=500)

    bom.components.new(
        name="hd12", description="Seagate 3.5'' 12TB SATA 6Gb/s 7.2K RPM 256MB 512e/4kn Helium", cost=276, hru=12000, power=10, su_perc=100
    )
    
    bom.components.new(
        name="amd1",
        description="AMD Ryzen 3 2200G 3,5Gz 4-Cores Socket AM4 + Cooler (4 logical cores)",
        cost=95,
        cru=4,
        power=80,
        cu_perc=100,
        passmark=6797,
    )
    
    bom.components.new(
        name="amd2",
        description="AMD Ryzen 7 2700 3,2Gz 8-Cores Socket AM4 + Cooler (16 logical cores)",
        cost=296,
        cru=16,
        power=80,
        cu_perc=100,
        passmark=17601,
    )
    

    bom.components.new(name="ssd1", description="Intel D1 P4101 256GB NVMe PCIe 3.0 x4 M.2 22x80mm  0.5DWPD", cost=82, sru=256, power=10, su_perc=100)
    
    bom.components.new(name="ssd2", description="Intel D1 P4101 1TB NVMe PCIe 3.0 x4 M.2 22x80mm 0.5DWPD", cost=292, sru=1000, power=10, cu_perc=100)
    
    bom.components.new(name="mem32_ecc", description="Samsung 32GB DDR4-2666 NON-ECC UNB 1Rx4", cost=110, mru=32, power=8, cu_perc=100)
    
    bom.components.new(
        name="ng2",
        description="48 ports 10 gbit + 4 ports 10 gbit sfp: fs.com + cables",
        cost=1,
        power=100,
        rackspace_u=1,
    )

    # create the template sn1
    d = bom.devices.new(name="sn1")
    d.components.new(name="s1", nr=1)
    d.components.new(name="amd1", nr=1)
    d.components.new(name="hd12", nr=0)
    d.components.new(name="mem32_ecc", nr=1)
    d.components.new(name="ssd1", nr=1)

    # create the template sn2
    d = bom.devices.new(name="sn2")
    d.components.new(name="s2", nr=1)
    d.components.new(name="amd2", nr=1)
    d.components.new(name="hd12", nr=0)
    d.components.new(name="mem32_ecc", nr=2)
    d.components.new(name="ssd2", nr=1)
    
    # create the template sn2hdd
    d = bom.devices.new(name="sn2hdd")
    d.components.new(name="s2", nr=1)
    d.components.new(name="amd2", nr=1)
    d.components.new(name="hd12", nr=1)
    d.components.new(name="mem32_ecc", nr=2)
    d.components.new(name="ssd2", nr=1)
     
    # create the template sn3
    d = bom.devices.new(name="sn3")
    d.components.new(name="s2", nr=1)
    d.components.new(name="amd2", nr=1)
    d.components.new(name="hd12", nr=2)
    d.components.new(name="mem32_ecc", nr=2)
    d.components.new(name="ssd2", nr=1)
    
    # create the template sn4
    d = bom.devices.new(name="sn4")
    d.components.new(name="s2", nr=1)
    d.components.new(name="amd2", nr=1)
    d.components.new(name="hd12", nr=3)
    d.components.new(name="mem32_ecc", nr=2)
    d.components.new(name="ssd2", nr=1)
    
    # create the template sn5
    d = bom.devices.new(name="sn5")
    d.components.new(name="s2", nr=1)
    d.components.new(name="amd2", nr=1)
    d.components.new(name="hd12", nr=4)
    d.components.new(name="mem32_ecc", nr=2)
    d.components.new(name="ssd2", nr=1)


    d = bom.devices.new(name="switch_48")
    d.components.new(name="ng2", nr=1)
    
    return bom
