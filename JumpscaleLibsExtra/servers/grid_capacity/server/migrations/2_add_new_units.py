from Jumpscale import j
from servers.grid_capacity.server.models import Farmer, Location, Capacity, Resources

# connect to mongodb
j.clients.mongoengine.get("capacity", interactive=False)

resource = Resources().to_mongo()
col = Capacity._get_collection()


col.update_many({"cru": {"$exists": True}}, {"$unset": {"cru": 1}})
col.update_many({"hru": {"$exists": True}}, {"$unset": {"hru": 1}})
col.update_many({"mru": {"$exists": True}}, {"$unset": {"mru": 1}})
col.update_many({"sru": {"$exists": True}}, {"$unset": {"sru": 1}})


col.update_many({"total_resources": {"$exists": False}}, {"$set": {"total_resources": resource}}, upsert=True)
col.update_many({"reserved_resources": {"$exists": False}}, {"$set": {"reserved_resources": resource}}, upsert=True)
col.update_many({"used_resources": {"$exists": False}}, {"$set": {"used_resources": resource}}, upsert=True)
