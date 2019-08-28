# DO NOT EDIT THIS FILE. This file will be overwritten when re-running go-raml.

from flask import Blueprint
from . import handlers


api_api = Blueprint("api_api", __name__)


@api_api.route("/api/farmers", methods=["GET"])
def ListFarmers():
    """
    List Farmers
    It is handler for GET /api/farmers
    """
    return handlers.ListFarmersHandler()


@api_api.route("/api/farmers/<iyo_organization>", methods=["GET"])
def GetFarmer(iyo_organization):
    """
    Get detail about a farmer
    It is handler for GET /api/farmers/<iyo_organization>
    """
    return handlers.GetFarmerHandler(iyo_organization)


@api_api.route("/api/nodes", methods=["GET"])
def ListCapacity():
    """
    List all the nodes capacity
    It is handler for GET /api/nodes
    """
    return handlers.ListCapacityHandler()


@api_api.route("/api/nodes", methods=["POST"])
def RegisterCapacity():
    """
    Register a node capacity
    It is handler for POST /api/nodes
    """
    return handlers.RegisterCapacityHandler()


@api_api.route("/api/nodes/<node_id>", methods=["GET"])
def GetCapacity(node_id):
    """
    Get detail about capacity of a node
    It is handler for GET /api/nodes/<node_id>
    """
    return handlers.GetCapacityHandler(node_id)


@api_api.route("/api/nodes/<node_id>/reserved", methods=["PUT"])
def UpdateReservedCapacity(node_id):
    """
    Mark some capacity on a node to be reserved
    It is handler for PUT /api/nodes/<node_id>/reserved
    """
    return handlers.UpdateReservedCapacityHandler(node_id)


@api_api.route("/api/nodes/<node_id>/actual", methods=["PUT"])
def UpdateActualUsedCapacity(node_id):
    """
    Set the actual usage of the capacity of a node
    It is handler for PUT /api/nodes/<node_id>/actual
    """
    return handlers.UpdateActualUsedCapacityHandler(node_id)


@api_api.route("/api/farmer_create", methods=["GET"])
def RegisterFarmer():
    """
    Register a farmer
    It is handler for GET /api/farmer_create
    """
    return handlers.RegisterFarmerHandler()


@api_api.route("/api/farmer_update", methods=["GET"])
def UpdateFarmer():
    """
    Update a farmer
    It is handler for GET /api/farmer_update
    """
    return handlers.UpdateFarmerHandler()