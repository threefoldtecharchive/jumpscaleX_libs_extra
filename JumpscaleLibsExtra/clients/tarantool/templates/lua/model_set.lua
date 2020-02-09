function $funcname(key,data)
    -- local obj = model_capnp_$name.$Name.parse(data) --deserialze capnp
    -- local name = obj["name"]
    -- res0 = model_$name_get(name)
    -- if res0 == nil then
    --     res = box.space.$name:auto_increment({obj['name'],data}) -- indexes the name
    --     id = res[1]
    -- else
    --     id = res0[1]
    -- end

    -- if key==0 then
    --     res = box.space.$name:auto_increment({data})
    --     key = res[1]
    -- end
    -- obj["id"] = key
    -- data = model_capnp_$name.$Name.serialize(obj) --reserialze with id inside

    box.space.$name:put{key, data}
    return key
end

box.schema.func.create('set', {if_not_exists = true})
box.schema.user.grant('$login', 'execute', 'function','set',{ if_not_exists= true})
