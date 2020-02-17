local function delete(key)
    box.space.$name:delete(key)
end
box.schema.func.create('delete', {if_not_exists = true})
box.schema.user.grant('$login', 'execute', 'function', 'delete',{ if_not_exists= true})
