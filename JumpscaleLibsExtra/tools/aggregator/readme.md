## aggregator

### design criteria

- ultra fast (many thousands of objects should be processed per sec)
- language independant (this python extension serves as documentation how to use redis for this purpose & how to load the stored procedures)
- all processing logic inside redis by stored procedures
- very easy to insert data to redis from any language
- protection
    - redis can never explode, max memory utilization is defined !!! 
    - redis can be configured (not done by this tool) to be redundant (on disk, active-passive...)
- flexibility
    - this design allows for ultimate flexibility

### suggested deployment mechanism

- put redis on each node (virtual or physical)
- run them all on predefined port e.g. 7777
- they all use same passwd as protection
- per local environment deploy 2 pollers, they use nmap to find all redis'es in local network answering on 7777
    - suggest not to use config mgmt here and scan for the nodes because we want this layer to get all reality info from the grid & process it for further usage e.g. send to mongo or to influxdb in generic means
- 2 pollers can work at same time because we use the queues to get the data out, so only one get a piece of info at the same time to process

### why our own aggregation for stats

- we want the data to be clean & pre-aggregated before it goes to influxdb
- there are 2 types of measurement: absolute & differential which we believe is enough for 99% of requirements
- we keep avg & max per 5 minutes and per hour which we believe is good enough for many decisions (no need to heavily query e.g. influxdb)
- this allows applications to send stat info as frequent as they want, the aggregator will make sure we have 1 per min/hour which makes implementation easy

### link to reality info

- we want the system to collect reality information in a way its agnostic from central applications
- in jumpscale we have our j.data.models .. tools which has a lot of predefined models, its recommended to use those because that will make it easier to dump the info later e.g. in Mongodb
- we use the excelent mongoengine library for the database models

## conclusion

- a well designed grid node has no local state
- the reality info is captured locally and send in non disruptive way to the aggregator
- external tools to the node process that info
- the info is complete: logs, errorconditions, reality info and statistics
- this info gives a full view on what is going on in the grid to the central management system
- its flexible enough to make it very easy for people to process the data in different ways and to different database backend systems

