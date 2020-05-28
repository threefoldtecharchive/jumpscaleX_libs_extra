## TF Grid Valuation Report.

![](https://wiki.threefold.io/img/cap2layer.png)


{% if simulator.config.tft_pricing_type=="AUTO" %}

- You have chosen in your simulator to let the TFT price be defined by ```value of the grid / nr of TFT in the network``` 
- The grid grows in value depending the margin or revenue generated.
- Just like any other business valuation can be calculated based on a nr of parameters 
    - e.g. multiple on revenue or margin.
- current simulation: 
    - valuation based on {{a.valuation.month_multiple/12|round(0)}} years of net {{simulator.config.cloudvaluation.indextype}}
    - calculated valuation of the grid in 5 year: {{a.valuation.valuation_hr}} (m means Million USD).

### Token Price 

![]({{simulator.graph_token_price_png(path=a.path)}} ':size=800x600')

> disclaimer: the TFT is not an investment instrument.<BR>
> Please note this is just a simulation, by no means a prediction of the TFT price.

{% else %}

### Token Price 

You have chosen a fixed price for the token growth, we let the tokenprice go up in a linear way which is not going to correspond to reality.

![]({{simulator.graph_token_price_png(path=a.path)}} ':size=800x600')

> disclaimer: the TFT is not an investment instrument.
> Please note this is not prediction of the TFT price, you have chosen this value.

{% endif %}

### Valuation Of Grid Calculation

!!!include:wiki:simulator_grid_valuation

| valuation mechanism | valuation in USD |
| --- | --- |
{% for v in a.valuations %}
| {{ v.valuation_descr }} | {{ v.valuation_hr }} |
{% endfor %}

![]({{simulator.graph_valuation_png(path=a.path,rev=True)}} ':size=800x600')      

Simulation here is based on yearly revenue on the grid, different multiples applied based on years.

![]({{simulator.graph_valuation_png(path=a.path,rev=False)}} ':size=800x600')

Simulation here is based on yearly net margin on the grid, different multiples applied based on years.

### TFT price index

If the token price would be ```value of the grid / nr of TFT in the network``` then we can calculate an estimate TFT price index.
Disclaimer, this is by no means a suggestion that the TFT will go to this price, its just a logical index which could indicate a value for the TFT.
Realize this is just a simulation, and no indication of any future price.

| valuation mechanism | TFT Price Index USD |
| --- | --- |
{% for v in a.valuations %}
| {{ v.valuation_descr }} | {{ v.tft_price_index }} |
{% endfor %}


### example detailed calculation for month {{a.month}}

In case the TFT price is auto then it gets calculated with the params as defined below.

#### revenues with utilization in account

- The revenue is calculated on TFT at the price in USD at point when the TFT has been received.
- In other words TFT token price growth will give more return for the farmer but is not visible below.

| | USD |
| --- | ---: |
| rev cu                |  {{a.rev_compute}} | 
| rev su                |  {{a.rev_storage}} | 
| rev nu                |  {{a.rev_network}} | 
| rev total             |  {{a.rev_total}} | 

#### revenues if all resources used 

Is for full grid per month at month {{a.month}}

| | USD |
| --- | ---: |
| rev cu                |  {{a.rev_compute_max}} | 
| rev su                |  {{a.rev_storage_max}} | 
| rev nu                |  {{a.rev_network_max}} | 
| rev total             |  {{a.rev_total_max}} | 

#### costs over the full grid per month at month {{a.month}}

| | USD |
| --- | ---: |
| cost hardware         |  {{a.cost_hardware}} | 
| cost power            |  {{a.cost_power}} | 
| cost maintenance      |  {{a.cost_maintenance}} | 
| cost rackspace        |  {{a.cost_rackspace}} | 
| cost network          |  {{a.cost_network}} | 
| cost total            |  {{a.cost_total}} | 




