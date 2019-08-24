# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.
import os

from flask import request, redirect
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
def RegisterFarmerHandler():
    wallet_addresses = []
    address = request.args.get("walletAddress")
    if address:
        wallet_addresses.append(address)

    farmer = Farmer(
        name=request.args["name"], iyo_organization=request.args["organization"], wallet_addresses=wallet_addresses
    )

    farmAddress = request.args.get("farmAddress")
    if farmAddress:
        lat, lng = [float(x.strip()) for x in farmAddress.split(",")]
        continent, country, city = reverse_geocode(lat, lng)

        if continent and country and city:
            farmer.location = Location()
            farmer.location.country = country
            farmer.location.continent = continent
            farmer.location.city = city
            farmer.location.longitude = lng
            farmer.location.latitude = lat

    farmer.save()
    return redirect("/farm_registered")
