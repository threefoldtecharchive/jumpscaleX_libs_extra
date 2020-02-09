local function get_json(key)
    local res = get(key)
    if res == nil then
        return nil
    else
        return model_capnp_$name.$Name.parse(res[3])
    end
end

box.schema.func.create('get_json', {if_not_exists = true})
box.schema.user.grant('$login', 'execute', 'function', 'get_json',{ if_not_exists= true})
