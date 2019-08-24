# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import os
from flask import request, redirect, jsonify, flash
from ..flask_itsyouonline import requires_auth

import json as JSON
import jsonschema
from jsonschema import Draft4Validator
from ..models import Farmer, Location
from .reverse_geocode import reverse_geocode


dir_path = os.path.dirname(os.path.realpath(__file__))
Farmer_schema = JSON.load(open(dir_path + "/schema/Farmer_schema.json"))
Farmer_schema_resolver = jsonschema.RefResolver("file://" + dir_path + "/schema/", Farmer_schema)
Farmer_schema_validator = Draft4Validator(Farmer_schema, resolver=Farmer_schema_resolver)


@requires_auth(org_from_request=True)
def UpdateFarmerHandler():
    iyo_organization = request.args["organization"]
    farmer = Farmer.objects.filter(iyo_organization=iyo_organization).first()
    if not farmer:
        return jsonify(code=404, message="itsyou.online organization: {} not found.".format(iyo_organization)), 404

    new_farm_name = request.args.get("name")
    if new_farm_name:
        farmer.name = new_farm_name
    farm_address = request.args.get("farmAddress")
    if farm_address:
        lng = lat = 0
        try:
            lat, lng = [float(x.strip()) for x in farm_address.split(",")]
        except ValueError:
            return jsonify(code=400, message="incorrect farm address {}".format(farm_address)), 400

        continent, country, city = reverse_geocode(lat, lng)
        if not (continent and country and city):
            return (
                jsonify(code=400, message="couldn't reverse location on (latitude {}, longitude {})".format(lat, lng)),
                400,
            )

        farmer.location = Location()
        farmer.location.country = country
        farmer.location.continent = continent
        farmer.location.city = city
        farmer.location.longitude = lng
        farmer.location.latitude = lat
    flash("Farmer {} updated successfully".format(iyo_organization), "success")
    farmer.save()

    return redirect("/farmers")
