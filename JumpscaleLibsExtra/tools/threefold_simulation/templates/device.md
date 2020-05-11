# Device overview

![](https://wiki.threefold.io/img/whatisafarmer.png)

Is the normalized node (device) as used in the simulation.

{{data.description}}

- cost of the hardware (investment): {{data.total.cost_hardware.hr}} USD
- total cost per month: {{data.total.cost_total_month.hr}} USD
    - is the cost for power, rackspace, hardware, maintenance
    
## capacity of the node

### compute (memory)

- compute capacity in nr of logical cores = {{data.production.cru}}
- memory capacity in nr of GB = {{data.production.mru}}
- if expressed in cloud units: compute units (cu): {{data.production.cu|round}}
- percent production is compute: {{data.production.cu_perc*100|round(2)}}%
- the performance of 1 compute unit (CU) expressed in passmark: {{data.production.cu_passmark}}

### storage

- storage capacity in TB HD capacity =  {{data.production.hru/1000}}
- storage capacity in GB SSD capacity =  {{data.production.sru}}
- if expressed in cloud units: storage units (su): {{data.production.su|round}}
- percent production is storage:{{data.production.su_perc*100|round(2)}}%

### network
    
- simulated amount of network being consumed in GB per month: {{data.production.nu_used_month|round}} 
- cost to produce the network units per month: {{data.production.cost_nu_month.hr}} USD

### CPR

- the cloud production rate of this device (is like hashrate in BTC): {{data.production.cpr|round}} 
    
## energy usage

- node uses {{data.total.power|round}} in watt
- per month this device uses: {{data.total.power_kwh_month|round}} kwh
- per month the cost of power is: {{data.total.cost_power_month.hr}} USD 

## rackspace cost

In case the node is hosted in a datacenter.

- nr of U (units of rackspace) used in a datacenter: {{data.total.rackspace_u}}
- cost of the rackspace for this device {{data.total.cost_rack_month.hr}} USD

## maintance of the device

- cost to maintain the device per month: {{data.total.cost_maintenance_month.hr}} USD

## costunits

| name | cost | 
|------|------|
{% for key,val in data.costunits._ddict_hr.items() %}
| {{key}} | {{val}} | 
{% endfor %}

- cost of a network unit (NU) per month: {{data.production.cost_nu_month/data.production.nu_used_month}} USD


## params

| name | value | 
|------|------|
{% for key,val in data.params._ddict.items() %}
| {{key}} | {{val}} | 
{% endfor %}


