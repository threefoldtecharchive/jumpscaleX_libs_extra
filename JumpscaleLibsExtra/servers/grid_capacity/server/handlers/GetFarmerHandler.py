# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify, request
from ..models import FarmerRegistration, FarmerNotFoundError


def GetFarmerHandler(iyo_organization):
    try:
        farmer = FarmerRegistration.get(iyo_organization)
    except FarmerNotFoundError:
        return jsonify(), 404

    return farmer.to_json(use_db_field=False), 200, {"Content-type": "application/json"}
