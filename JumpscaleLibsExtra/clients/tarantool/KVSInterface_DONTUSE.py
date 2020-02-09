import base64

from Jumpscale import j

JSBASE = j.baseclasses.object


class KVSTarantool(j.baseclasses.object):
    """
    This class implement a simple key value store on top of tarantool
    It proxy calls to stored procedure in tarantool server
    """

    def __init__(self, db, space):
        JSBASE.__init__(self)
        self._db = db
        self.space = space
        self.inMem = False

    def _build_call(self, method):
        return "model_%s.%s" % (self.space, method)

    def _call(self, method, *args):
        return self._db.call(self._build_call(method), (*args))

    def set(self, key, value):
        # taarantool doesn't support binary value, this is not true (despiegk)
        if isinstance(value, bytes):
            value = base64.b64encode(value)
        self._call("set", (key, value))

    def index(self, index):
        pass

    def list(self):
        resp = self._call("list")
        return resp.data[0]

    def get(self, key):
        resp = self._call("get", key)
        if len(resp.data) <= 1 and len(resp.data[0]) > 2:
            raise j.exceptions.NotFound("value for %s not found" % key)
        # taarantool doesn't support binary value
        value = resp.data[0][1]
        if isinstance(value, (str, bytes)):
            value = base64.b64decode(value)
        return value

    def exists(self, key):
        resp = self._call("exists", key)
        return resp.data[0][0]

    def delete(self, key):
        self._call("delete", key)

    def find(self, query):
        return self._call("find", query)

    def destroy(self):
        self._call("destroy")
