box.cfg()


box.schema.space.create('user',{if_not_exists= true, engine="memtx"})

box.space.user:create_index('primary',{ parts = {1, 'unsigned'}, if_not_exists= true})
--create 2nd index for e.g. name
box.space.user:create_index('secondary', {type = 'tree', parts = {2, 'string'}, if_not_exists= true})

box.schema.user.create('user', {password = 'secret', if_not_exists= true})

function model_user_get(name,id)
    id = id or 0
    if id == 0 then
        res= box.space.user.index.secondary:get(name)
    else
        res= box.space.user:get(id)
    end
    if res==nil then
        return nil
    else
        return res
    end
end

box.schema.func.create('model_user_get', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_get',{ if_not_exists= true})

function model_user_get_json(name,id)
    res0= model_user_get(name,id)
    if res0 == nil then
        return nil
    else
        return model_capnp_user.User.parse(res0[3])
    end
end

box.schema.func.create('model_user_get_json', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_get_json',{ if_not_exists= true})

function model_user_set(data)
    obj=model_capnp_user.User.parse(data) --deserialze capnp
    name=obj["name"]
    res0= model_user_get(name)
    if res0==nil then
        res = box.space.user:auto_increment({obj['name'],data}) -- indexes the name
        id=res[1]
    else
        id=res0[1]
    end
    obj["id"]=id
    data=model_capnp_user.User.serialize(obj)
    box.space.user:put{id,obj['name'],data}
    return id
end

box.schema.func.create('model_user_set', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function','model_user_set',{ if_not_exists= true})

function model_user_del(name,id)
    id,name,bdata= model_user_get(name,id)
    if not bdata==nil then
        box.user.user:delete(id)
    end
end
box.schema.func.create('model_user_del', {if_not_exists = true})
box.schema.user.grant('user', 'execute', 'function', 'model_user_del',{ if_not_exists= true})




obj={
    description="a description",
    name="aname2"
}



package.path = '/sandbox/code/github/threefoldtech/jumpscaleX/Jumpscale/clients/tarantool/systemscripts/?.lua;' .. package.path
package.path = '/tmp/lua/?.lua;' .. package.path

-- model_capnp_user=require("model_capnp_user")

-- bdata=model_capnp_user.User.serialize(obj)
-- print(model_capnp_user.User.parse(bdata)["name"])

-- print(model_user_set(bdata))

-- print( model_user_find("S"))

-- print (model_user_set(0,bdata))
