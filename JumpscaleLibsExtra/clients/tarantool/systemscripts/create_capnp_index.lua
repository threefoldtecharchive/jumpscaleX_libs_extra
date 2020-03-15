-- this function takes a capnp schema and create and index for each field of the schema
-- into the space prodived

function create_capnp_index(capnp_schema, space)
    local type_map = {
        void = 'nil',
        bool = 'boolena',
        int8 = 'number',
        int16 = 'number',
        int32 = 'number',
        int64 = 'number',
        float32 = 'number',
        float64 = 'number',
        text = 'string',
        data = 'table',
    }
    local fields = capnp_schema.fields
    for i,v in ipairs(fields) do
        local index_type = type_map[v.type]
        if index_type ~= nil then
            local index_name = space.name..'_'..v.name
            space:create_index(index_name, { type = 'tree', parts = {i, index_type}, if_not_exists= true})
        end
    end
end
