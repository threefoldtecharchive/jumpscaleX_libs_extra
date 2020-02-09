local function exists(key)
    local count = box.space.$name:count(key)
    return count ~= 0
end

box.schema.func.create('exists', {if_not_exists = true})
box.schema.user.grant('$login', 'execute', 'function', 'exists',{ if_not_exists= true})
