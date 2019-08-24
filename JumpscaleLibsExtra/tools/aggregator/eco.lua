--message, messagepub, str(level), type, tags, code, funcname, funcfilepath, backtrace, str(time)
-- key, message, messagepub, str(level), type,
--                                 tags, code, funcname, funcfilepath, backtrace, str(timestamp)
local key = KEYS[1]
local message = ARGV[1]
local messagepub = ARGV[2]
local level = tonumber(ARGV[3])
local type = ARGV[4]
local tags = ARGV[5]
local code = ARGV[6]
local funcname = ARGV[7]
local funcfilename = ARGV[8]
local backtrace = ARGV[9]
local newtime = tonumber(ARGV[10])
local gid = tonumber(ARGV[11])
local nid = tonumber(ARGV[12])

--There is no hashing library built in lua, and redis doesn't allow importing external libraries.
--so the key=md5(message + messagepub + code + funcname + funcfilepath) is calculated by the caller.

local rediskey = string.format("eco:%s", key)
local value = redis.call("get", rediskey)
local eco
local flushtime = 0

if value then
    eco = cjson.decode(value)
    eco.occurrences = eco.occurrences + 1
    flushtime = eco._flushtime
else
    eco = {}
    eco.key = key
    eco.errormessage = message
    eco.errormessagepub = messagepub
    eco.code = code
    eco.funcname = funcname
    eco.funcfilename = funcfilename
    eco.closetime = 0
    eco.occurrences = 1
end

--overwrite even the ones coming from DB
eco.lasttime = newtime
eco.backtrace = backtrace
eco.level = level
eco.type = type
eco.tags = tags
eco.gid = gid
eco.nid = nid

local function save(key, eco)
    -- set before we push to the queue to make sure object is already uptodate
    local value = cjson.encode(eco)
    redis.call("set", key, value)
    redis.call("expire", key, 24*60*60)
end

-- time in milliseond
if flushtime < (newtime - 300000) then
    eco._flushtime = newtime
    save(rediskey, eco)
    --new eco or has been more than 5 min since last orccuance
    redis.call("RPUSH", "queues:eco", key)
    --only keep last 1000 ecos
    redis.call("LTRIM", "queues:eco", -1000, -1)
else
    save(rediskey, eco)
end

return cjson.encode(eco)
