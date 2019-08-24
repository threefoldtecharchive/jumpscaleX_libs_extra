from Jumpscale import j
from servers.grid_capacity.server.models import Farmer, Location

# connect to mongodb
j.clients.mongoengine.get("capacity", interactive=False)

loc = Location()
loc.to_mongo()
col = Farmer._get_collection()
res = col.update_many({"location": {"$exists": False}}, {"$set": {"location": loc.to_mongo()}}, upsert=True)
print("updated %d documents" % res.modified_count)
