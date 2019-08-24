local node = KEYS[1]
local message = ARGV[1]
local tags = ARGV[2]
local level = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local logkey = "queues:logs"

local v = {}

v["node"] = node
v["message"] = message
v["tags"] = tags
v["level"] = level
v["epoch"] = now

-- keep logs queue under 5000 line
redis.call("RPUSH", logkey, cjson.encode(v))
redis.call("LTRIM", logkey, -5000, -1)

return "OK"

