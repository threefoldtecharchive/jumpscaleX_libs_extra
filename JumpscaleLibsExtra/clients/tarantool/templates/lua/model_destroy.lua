local function destroy()
    box.space.$name:truncate()
end
box.schema.func.create('destroy', {if_not_exists = true})
box.schema.user.grant('$login', 'execute', 'function', 'destroy',{ if_not_exists= true})
