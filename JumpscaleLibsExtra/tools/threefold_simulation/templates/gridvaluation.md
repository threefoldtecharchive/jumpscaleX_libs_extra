## TF Grid Valuation Report.

![](https://wiki.threefold.io/img/cap2layer.png)

Based on the arguments chosen we can simulate how the grid valuation could be after 60 months.

### Token Price 

Simulation of tokenprice if it would be in line with the grid valuation:

- valuation based on {{a.valuation.month_multiple}} months of {{simulator.config.cloudvaluation.indextype}}
- valuation is {{a.valuation.valuation_hr}}  (m means Million USD)

Please note this is just a simulation, by no means a prediction of the TFT price.

![]({{simulator.graph_token_price_png(path=a.path)}} ':size=800x600')

Token price would be ```value of the grid / nr of TFT in the network``` 

> disclaimer: the TFT is not an investment instrument.

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


### example detailed calculation for month {month}

In case the TFT price is auto then it gets calculated with the params as defined below.

#### revenues with utilization in account

This does not take token price increase into consideration.

| | USD |
| --- | ---: |
| rev cu                |  {{a.rev_compute}} | 
| rev su                |  {{a.rev_storage}} | 
| rev nu                |  {{a.rev_network}} | 
| rev total             |  {{a.rev_total}} | 

#### revenues if all resources used

| | USD |
| --- | ---: |
| rev cu                |  {{a.rev_compute_max}} | 
| rev su                |  {{a.rev_storage_max}} | 
| rev nu                |  {{a.rev_network_max}} | 
| rev total             |  {{a.rev_total_max}} | 

#### costs

| | USD |
| --- | ---: |
| cost hardware         |  {{a.cost_hardware}} | 
| cost power            |  {{a.cost_power}} | 
| cost maintenance      |  {{a.cost_maintenance}} | 
| cost rackspace        |  {{a.cost_rackspace}} | 
| cost network          |  {{a.cost_network}} | 
| cost total            |  {{a.cost_total}} | 




