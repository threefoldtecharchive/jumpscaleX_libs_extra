# Bill of Material

## devices
{% for d in data.devices %}

### device: **{{d.name}}**

List of components as used in the device:

| name | amount | 
|------|------|
{% for c in d.components %}
| {{c.name}} | {{c.nr}} | 
{% endfor %}
{% endfor %}

## Components

Is the overview of the list of components used to make up a device.

| name | description | cost | power | rackspace | cru | sru | hru | mru | link | passmark |
|------|------|------|-------|-----------|-----|-----|-----|-----|------|----------|
{% for c in data.components %}
| {{c.name}} | {{c.description}} | {{c.cost}} | {{c.power}} | {{c.rackspace_u}} | {{c.cru}} | {{c.sru}}  | {{c.hru}} | {{c.mru}}  | {{c.link}}  | {{c.passmark}} |
{% endfor %}

for explanation about cru,sru, ... see [resource units](wiki:resource_units)

