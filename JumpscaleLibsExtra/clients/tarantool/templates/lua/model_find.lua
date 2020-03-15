
local function find(query)
    local res = {}
    local items = box.space.$name:select()
    for _, encoded_item in pairs(items) do
        -- --deserialze capnp
        local item = decode(encoded_item[2])
        -- add the item into the result table if all the query is mathing the item
        local add = true
        for k,v in pairs(query) do
            if item[k] ~= nil and item[k] ~= query[k] then
                add = false
                break
            end
            if add == true then
                table.insert(res, item)
            end
        end
    end
    return res
end

-- this decode some capnp-base64 encoded object into a lua table
local function decode(encoded)
    local digest = require("digest")
    local decoded = digest.base64_decode(encoded)
    local obj = model_capnp_$name.$Name.parse(decoded)
    return obj
end

box.schema.func.create('find', {if_not_exists = true})
box.schema.user.grant('$login', 'execute', 'function', 'find',{ if_not_exists= true})
