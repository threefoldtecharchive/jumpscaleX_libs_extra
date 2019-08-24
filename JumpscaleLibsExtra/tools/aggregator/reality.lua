-- TODO: has never been debugged

local key = KEYS[1]
local json = ARGV[1]
local node = ARGV[2]
local tags = ARGV[3]
local modeltype = ARGV[4]
local now = tonumber(ARGV[5])

local rediskey = string.format("reality:%s", key)
local v = {}

v.key = key
v.node = node
v.json = json
v.tags = tags
v.epoch = now
v.modeltype = modeltype

local value = cjson.encode(v)
redis.call('set', rediskey, value)
redis.call("expire", rediskey, 24*60*60)

redis.call("RPUSH", "queues:reality", key)
redis.call("LTRIM", "queues:reality", -5000, -1)

return "OK"

