# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.
from flask import request, jsonify
from ..models import FarmerRegistration


def ListFarmersHandler():
    farmers = FarmerRegistration.list()
    output = []
    for farmer in farmers.all():
        f = farmer.to_mongo().to_dict()
        f["iyo_organization"] = f.pop("_id")
        output.append(f)
    return jsonify(output)
