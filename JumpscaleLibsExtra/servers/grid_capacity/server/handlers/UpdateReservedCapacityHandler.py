# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.
import json as JSON
import os
from datetime import datetime

import jsonschema
from jsonschema import Draft4Validator

from flask import jsonify, request

from ..models import NodeRegistration, Resources
from .jwt import FarmerInvalid, validate_farmer_id


dir_path = os.path.dirname(os.path.realpath(__file__))
ReservedCapacity_schema = JSON.load(open(dir_path + "/schema/ReservedCapacity_schema.json"))
ReservedCapacity_schema_resolver = jsonschema.RefResolver("file://" + dir_path + "/schema/", ReservedCapacity_schema)
ReservedCapacity_schema_validator = Draft4Validator(ReservedCapacity_schema, resolver=ReservedCapacity_schema_resolver)


def UpdateReservedCapacityHandler(node_id):

    inputs = request.get_json()

    try:
        ReservedCapacity_schema_validator.validate(inputs)
    except jsonschema.ValidationError as e:
        return jsonify(errors="bad request body"), 400

    capacity = NodeRegistration.get(node_id)
    if capacity.reserved_resources is None:
        capacity.reserved_resources = Resources()

    capacity.reserved_resources.cru = inputs["cru"]
    capacity.reserved_resources.mru = inputs["mru"]
    capacity.reserved_resources.hru = inputs["hru"]
    capacity.reserved_resources.sru = inputs["sru"]
    capacity.updated = datetime.now()
    capacity.save()

    return "", 204
