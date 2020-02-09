
function $funcname(key)
    res = box.space.$name:get{key}
    return res
    -- if type(key) == 'number' then
    --     return box.space.$name:get(key)
    -- end
    -- return box.space.$name.index.secondary:get(key)
end

box.schema.func.create('get', {if_not_exists = true})
box.schema.user.grant('$login', 'execute', 'function', 'get',{ if_not_exists= true})
