# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify, request
from ..models import NodeRegistration, NodeNotFoundError


def GetCapacityHandler(node_id):
    try:
        node = NodeRegistration.get(node_id)
        if node.farmer.location and node.farmer.location.latitude and node.farmer.location.longitude:
            node.location = node.farmer.location
    except NodeNotFoundError:
        return jsonify(), 404

    output = node.to_mongo().to_dict()
    output["node_id"] = output.pop("_id")
    output["farmer_id"] = output.pop("farmer")

    return jsonify(output), 200, {"Content-type": "application/json"}
