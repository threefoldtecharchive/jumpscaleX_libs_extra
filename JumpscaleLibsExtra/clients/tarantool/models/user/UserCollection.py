from Jumpscale import j
import os
import capnp
import base64

ModelBaseCollection = j.data.capnp.getModelBaseClassCollection()
ModelBase = j.data.capnp.getModelBaseClass()
# from JumpscaleLibs.clients.tarantool.KVSInterface import KVSTarantool


class UserModel(ModelBase):
    """
    """

    def __init__(self):
        ModelBase.__init__(self)

    def index(self):
        # no need to put indexes because will be done by capnp
        pass

    def save(self):
        self.reSerialize()
        self._pre_save()
        buff = self.dbobj.to_bytes()
        key = self.key
        # key=msgpack.dumps(self.key)
        # key=base64.b64encode(self.key.encode())
        return self.collection.client.call("model_user_set", (key, buff))

    def delete(self):
        key = self.key
        # key=base64.b64encode(self.key.encode())
        return self.collection.client.call("model_user_del", (key))


class UserCollection(ModelBaseCollection):
    """
    This class represent a collection of Users
    It's used to list/find/create new Instance of User Model object
    """

    def __init__(self):
        category = "user"
        namespace = ""

        # instanciate the KVS interface on top of tarantool
        # cl = j.clients.tarantool.client_get()  # will get the tarantool from the config file, the main connection
        # db = KVSTarantool(cl, category)
        # mpath = j.sal.fs.getDirName(os.path.abspath(__file__)) + "/model.capnp"
        # SchemaCapnp = j.data.capnp.getSchemaFromPath(mpath, name='User')

        self.client = (
            j.clients.tarantool.client_get()
        )  # will get the tarantool from the config file, the main connection
        mpath = j.sal.fs.getDirName(os.path.abspath(__file__)) + "/model.capnp"
        SchemaCapnp = j.data.capnp.getSchemaFromPath(mpath, name="User")
        super().__init__(
            SchemaCapnp,
            category=category,
            namespace=namespace,
            modelBaseClass=UserModel,
            db=self.client,
            indexDb=self.client,
        )
        self.client.db.encoding = None

    def new(self):
        return UserModel(collection=self, new=True)

    def get(self, key):
        resp = self.client.call("model_user_get", key)
        if len(resp.data) <= 1 and len(resp.data[0]) > 2:
            raise j.exceptions.NotFound("value for %s not found" % key)
        value = resp.data[0][1]
        return UserModel(key=key, collection=self, new=False, data=value)

    # BELOW IS ALL EXAMPLE CODE WHICH NEEDS TO BE REPLACED

    def list(self):
        resp = self.client.call("model_user_list")
        return [item.decode() for item in resp[0]]

    # def list(self, actor="", service="", action="", state="", serviceKey="", fromEpoch=0, toEpoch=9999999999999,tags=[]):
    #     raise j.exceptions.NotImplemented()
    #     return res

    # def find(self, actor="", service="", action="", state="", serviceKey="", fromEpoch=0, toEpoch=9999999999999, tags=[]):
    #     raise j.exceptions.NotImplemented()
    #     res = []
    #     for key in self.list(actor, service, action, state, serviceKey, fromEpoch, toEpoch, tags):
    #         if self.get(key):
    #             res.append(self.get(key))
    #     return res
