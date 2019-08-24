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
ActualUsedCapacity_schema = JSON.load(open(dir_path + "/schema/ActualUsedCapacity_schema.json"))
ActualUsedCapacity_schema_resolver = jsonschema.RefResolver(
    "file://" + dir_path + "/schema/", ActualUsedCapacity_schema
)
ActualUsedCapacity_schema_validator = Draft4Validator(
    ActualUsedCapacity_schema, resolver=ActualUsedCapacity_schema_resolver
)


def UpdateActualUsedCapacityHandler(node_id):

    inputs = request.get_json()

    try:
        iyo_organization = validate_farmer_id(inputs.pop("farmer_id"))
    except FarmerInvalid:
        return jsonify(errors="Unauthorized farmer"), 403

    try:
        ActualUsedCapacity_schema_validator.validate(inputs)
    except jsonschema.ValidationError as e:
        return jsonify(errors="bad request body"), 400

    capacity = NodeRegistration.get(node_id)
    if capacity.used_resources is None:
        capacity.used_resources = Resources()

    capacity.used_resources.cru = inputs["cru"]
    capacity.used_resources.mru = inputs["mru"]
    capacity.used_resources.hru = inputs["hru"]
    capacity.used_resources.sru = inputs["sru"]
    capacity.updated = datetime.now()
    capacity.save()

    return "", 204
