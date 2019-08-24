from Jumpscale import j
from servers.grid_capacity.server.models import Farmer, Location, Capacity, Resources

# connect to mongodb
j.clients.mongoengine.get("capacity", interactive=False)

resource = Resources().to_mongo()
col = Capacity._get_collection()

res = col.update_many({"robot_address": "not running 0-OS"}, {"$set": {"robot_address": "private"}})
print("%s entries updated robot_address" % res.modified_count)
res = col.update_many({"os_version": "not running 0-OS"}, {"$set": {"os_version": "private"}})
print("%s entries updated os_version" % res.modified_count)
