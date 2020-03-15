function ping()
    return "pong"
end

-- box.schema.func.create('add_lua_script', {if_not_exists = true})
-- box.schema.user.create('guest1', {password = 'secret', if_not_exists= true})
-- box.schema.user.grant('guest1', 'execute', 'function', 'add_lua_script',{ if_not_exists= true})

msgpack=require('msgpack')
