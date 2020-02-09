require ("lfs")
lfs.mkdir("/tmp/lua")


function add_lua_script (name,content)
    local fio = require('fio')
    local errno = require('errno')
    path = "/tmp/lua/".. name .. ".lua"
    fio.unlink(path)
    local f = fio.open(path, {'O_CREAT', 'O_WRONLY'},
        tonumber('0666', 8))
    if not f then
        error("Failed to open file: "..errno.strerror())
    end
    f:write(content);
    f:close()
end


--make sure this is never accessible by non admin user remotely !
