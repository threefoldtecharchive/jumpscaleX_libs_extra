from collections import OrderedDict
from Jumpscale import j

JSBASE = j.baseclasses.object


class ModelBase(j.baseclasses.object):
    def __init__(self, key="", new=False, collection=None):

        self._propnames = []
        self.collection = collection
        self._key = ""

        self.dbobj = None
        self.changed = False
        self._subobjects = {}

        if j.data.types.bytes.check(key):
            key = key.decode()

        # if key != "":
        #     if len(key) != 16 and len(key) != 32 and len(key) != 64:
        #         raise j.exceptions.Input("Key needs to be length 16,32,64")

        if new:
            self.dbobj = self.collection._capnp_schema.new_message()
            self._post_init()
            if key != "":
                self._key = key
        elif key != "":
            # will get from db
            if self.collection._db.exists(key):
                self.load(key=key)
                self._key = key
            else:
                raise j.exceptions.Input(message="Cannot find object:%s!%s" % (self.collection.category, key))
        else:
            raise j.exceptions.Input(
                message="key cannot be empty when no new obj is asked for.", level=1, source="", tags="", msgpub=""
            )

    @property
    def key(self):
        if self._key is None or self._key == "":
            self._key = self._generate_key()
        return self._key

    @key.setter
    def key(self, value):
        if j.data.types.bytes.check(value):
            value = value.decode()
        self._key = value

    def _post_init(self, **kwargs):
        pass

    def _pre_save(self):
        # needs to be implemented see e.g. ActorModel
        pass

    def _generate_key(self):
        # return a unique key to be used in db (std the key but can be overriden)
        return j.data.hash.md5_string(j.data.idgenerator.generateGUID())

    def index(self):
        # put indexes in db as specified
        if self.collection != None:
            self.collection._index.index({self.dbobj.name: self.key})

    def load(self, key):
        if self.collection._db.inMem:
            self.dbobj = self.collection._db.get(key)
        else:
            buff = self.collection._db.get(key)
            self.dbobj = self.collection._capnp_schema.from_bytes(buff, builder=True)

    # TODO: *2 would be nice that this works, but can't get it to work, something recursive
    # def __setattr__(self, attr, val):
    #     if attr in ["_propnames", "_subobjects", "dbobj", "_capnp_schema"]:
    #         self.__dict__[attr] = val
    #         print("SETATTRBASE:%s" % attr)
    #         # return ModelBase.__setattr__(self, attr, val)
    #
    #     print("SETATTR:%s" % attr)
    #     if attr in self._propnames:
    #         print("1%s" % attr)
    #         # TODO: is there no more clean way?
    #         dbobj = self._subobjects
    #         print(2)
    #         exec("dbobj.%s=%s" % (attr, val))
    #         print(3)
    #         #
    #     else:
    #         raise j.exceptions.Input(message="Cannot set attr:%s in %s" %
    #                                  (attr, self))

    # def __dir__(self):
    #     propnames = ["key", "index", "load", "_post_init", "_pre_save", "_generate_key", "save", "logger",
    #                  "dictFiltered", "reSerialize", "dictJson", "raiseError", "addSubItem", "_listAddRemoveItem",
    #                  "logger", "_capnp_schema", "_category", "_db", "_index", "_key", "dbobj", "changed", "_subobjects"]
    #     return propnames + self._propnames

    def reSerialize(self):
        for key in list(self._subobjects.keys()):
            prop = self.__dict__["list_%s" % key]
            dbobjprop = eval("self.dbobj.%s" % key)
            if len(dbobjprop) != 0:
                raise j.exceptions.Base("bug, dbobj prop should be empty, means we didn't reserialize properly")
            if prop is not None and len(prop) > 0:
                # init the subobj, iterate over all the items we have & insert them
                subobj = self.dbobj.init(key, len(prop))
                for x in range(0, len(prop)):
                    subobj[x] = prop[x]

            self._subobjects.pop(key)
            self.__dict__.pop("list_%s" % key)

    def save(self):
        self.reSerialize()
        self._pre_save()
        if self.collection._db.inMem:
            self.collection._db.db[self.key] = self.dbobj
        else:
            # no need to store when in mem because we are the object which does not have to be serialized
            # so this one stores when not mem
            buff = self.dbobj.to_bytes()
            if hasattr(self.dbobj, "clear_write_flag"):
                self.dbobj.clear_write_flag()
            self.collection._db.set(self.key, buff)
        self.index()

    def to_dict(self):
        self.reSerialize()
        d = self.dbobj.to_dict()
        d["key"] = self.key
        return d

    @property
    def dictFiltered(self):
        """
        remove items from obj which cannot be serialized to json or not relevant in dict
        """
        # made to be overruled
        return self.to_dict()

    @dictFiltered.setter
    def dictFiltered(self, ddict):
        """
        """
        if "key" in ddict:
            self.key = ddict[key]
        self.dbobj = self.collection._capnp_schema.new_message(**ddict)

    @property
    def dictJson(self):
        ddict2 = OrderedDict(self.dictFiltered)
        return j.data.serializers.json.dumps(ddict2, sort_keys=True, indent=True)

    def raiseError(self, msg):
        msg = "Error in dbobj:%s (%s)\n%s" % (self._category, self.key, msg)
        raise j.exceptions.Input(message=msg)

    def updateSubItem(self, name, keys, data):
        keys = keys or []
        if not isinstance(keys, list):
            keys = [keys]
        self._listAddRemoveItem(name)
        existing = self.__dict__["list_%s" % name]
        for idx, item in enumerate(existing):
            match = True
            for key in keys:
                if item.to_dict()[key] != data.to_dict()[key]:
                    match = False
            if keys and match:
                existing.pop(idx)
                break
        self.addSubItem(name, data)

    def addDistinctSubItem(self, name, data):
        self._listAddRemoveItem(name=name)
        for item in self.__dict__["list_%s" % name]:
            if item.to_dict() == data.to_dict():
                return
        self.__dict__["list_%s" % name].append(data)

    def addSubItem(self, name, data):
        """
        @param data is string or object first retrieved by self.collection.list_$name_constructor(**args)
        can also directly add them to self.list_$name.append(self.collection.list_$name_constructor(**args)) if it already exists
        """
        self._listAddRemoveItem(name=name)
        self.__dict__["list_%s" % name].append(data)

    def initSubItem(self, name):
        self._listAddRemoveItem(name=name)

    def deleteSubItem(self, name, pos):
        """
        @param pos is the position in the list
        """
        self._listAddRemoveItem(name=name)
        self.__dict__["list_%s" % name].pop(pos)
        self.reSerialize()

    def _listAddRemoveItem(self, name):
        """
        if you want to change size of a list on obj use this method
        capnp doesn't allow modification of lists, so when we want to change size of a list then we need to reSerialize
        and put content of a list in a python list of dicts
        we then re-serialize and leave the subobject empty untill we know that we are at point we need to save the object
        when we save we populate the subobject so we get a nicely created capnp message
        """
        if name in self._subobjects:
            # means we are already prepared
            return
        prop = eval("self.dbobj.%s" % name)
        if len(prop) == 0:
            self.__dict__["list_%s" % name] = []
        else:
            try:
                self.__dict__["list_%s" % name] = [item.copy() for item in prop]
            except BaseException:  # means is not an object can be e.g. a string
                self.__dict__["list_%s" % name] = [item for item in prop]

        # empty the dbobj list
        exec("self.dbobj.%s=[]" % name)

        self._subobjects[name] = True
        self.changed = True

    def __repr__(self):
        out = "key:%s\n" % self.key
        out += self.dictJson
        return out

    __str__ = __repr__
