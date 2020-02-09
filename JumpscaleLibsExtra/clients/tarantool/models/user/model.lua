
box.schema.space.create('user',{if_not_exists= true, engine="memtx"})

box.space.user:create_index('primary',{ type = 'tree', parts = {1, 'string'}, if_not_exists= true})

--create 2nd index for e.g. name
-- box.space.user:create_index('secondary', {type = 'tree', parts = {2, 'string'}, if_not_exists= true})

box.schema.user.create('user', {password = 'secret', if_not_exists= true})




function model_user_get(key)
    res = box.space.user:get{key}
    return res
    -- if type(key) == 'number' then
    --     return box.space.user:get(key)
    -- end
    -- return box.space.user.index.secondary:get(key)
end

box.schema.func.create('model_user_get', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_get',{ if_not_exists= true})



function model_user_get_json(key)
    local res = model_user_get(key)
    if res == nil then
        return nil
    else
        return model_capnp_user.User.parse(res[3])
    end
end

box.schema.func.create('model_user_get_json', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_get_json',{ if_not_exists= true})



function model_user_set(key,data)
    -- local obj = model_capnp_user.User.parse(data) --deserialze capnp
    -- local name = obj["name"]
    -- res0 = model_user_get(name)
    -- if res0 == nil then
    --     res = box.space.user:auto_increment({obj['name'],data}) -- indexes the name
    --     id = res[1]
    -- else
    --     id = res0[1]
    -- end

    -- if key==0 then
    --     res = box.space.user:auto_increment({data})
    --     key = res[1]
    -- end
    -- obj["id"] = key
    -- data = model_capnp_user.User.serialize(obj) --reserialze with id inside

    box.space.user:put{key, data}
    return key
end

box.schema.func.create('model_user_set', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function','model_user_set',{ if_not_exists= true})



function model_user_delete(key)
    box.space.user:delete(key)
end
box.schema.func.create('model_user_delete', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_delete',{ if_not_exists= true})



function model_user_find(query)
    local obj = model_capnp_user.User.parse(data) --deserialze capnp
    res={}
    return res
end

box.schema.func.create('model_user_find', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_find',{ if_not_exists= true})



function model_user_exists(key)
    local count = box.space.user:count(key)
    return count ~= 0
end

box.schema.func.create('model_user_exists', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_exists',{ if_not_exists= true})



function model_user_destroy()
    box.space.user:truncate()
end
box.schema.func.create('model_user_destroy', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_destroy',{ if_not_exists= true})



function model_user_list()
    local space = box.space['user']
    local keys = {}
    for _, v in space:pairs() do
        table.insert(keys, v[1])
    end

    return keys
end

box.schema.func.create('model_user_list', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_list',{ if_not_exists= true})
