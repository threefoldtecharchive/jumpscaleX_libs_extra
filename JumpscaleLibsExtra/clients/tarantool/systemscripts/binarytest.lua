

digest=require("digest")
function binarytest (content)
    md5hex=digest.md5_hex(content)
    return md5hex
end
