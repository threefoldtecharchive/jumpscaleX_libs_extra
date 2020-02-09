local function list()
    local space = box.space['$name']
    local keys = {}
    for _, v in space:pairs() do
        table.insert(keys, v[1])
    end

    return keys
end

box.schema.func.create('list', {if_not_exists = true})
box.schema.user.grant('$login', 'execute', 'function', 'list',{ if_not_exists= true})
