
box.schema.space.create('mymodelname',{if_not_exists= true, engine="$dbtype"})

box.space.mymodelname:create_index('primary',{ type = 'tree', parts = {1, 'string'}, if_not_exists= true})

--create 2nd index for e.g. name
-- box.space.mymodelname:create_index('secondary', {type = 'tree', parts = {2, 'string'}, if_not_exists= true})

box.schema.user.create('$login', {password = '$passwd', if_not_exists= true})
