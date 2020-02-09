from collections import OrderedDict
from Jumpscale import j

JSBASE = j.baseclasses.object


def getText(text):
    return str(object=text)


def getInt(nr):
    return int(nr)


class ModelBaseCollection(j.baseclasses.object):
    """
    This class represent a collection
    It's used to list/find/create new Instance of Model objects

    """

    def __init__(self, schema, category, namespace=None, modelBaseClass=None, db=None, indexDb=None):
        """
        @param schema: object created by the capnp librairies after it load a .capnp file.
        example :
            import capnp
            # load the .capnp file
            import model_capnp as ModelCapnp
            # pass this to the constructor.
            ModelCapnp.MyStruct
        @param category str: category of the model. need to be the same as the category of the single model class
        @param namespace: namespace used to store these object in key-value store
        @param modelBaseClass: important to pass the class not the object. Class used to create instance of this category.
                               Need to inherits from ModelBase.ModelBase
        @param db: connection object to the key-value store
        @param indexDb: connection object to the key-value store used for indexing
        """

        self.category = category
        self.namespace = namespace if namespace else category
        self._capnp_schema = schema

        self.propnames = [item for item in self._capnp_schema.schema.fields.keys()]

        self._listConstructors = {}

        for field in self._capnp_schema.schema.fields_list:
            try:
                str(field.schema)
            except BaseException:
                continue

            if "List" in str(field.schema):
                slottype = str(field.proto.slot.type).split("(")[-1]
                if slottype.startswith("text"):
                    # is text
                    self._listConstructors[field.proto.name] = getText
                elif slottype.startswith("uint"):
                    # is text
                    self._listConstructors[field.proto.name] = getInt
                else:
                    subTypeName = str(field.schema.elementType).split(":")[-1][:-1].split(".")[-1]
                    # subTypeName = str(field.schema.elementType).split(".")[-1].split(">")[0]
                    try:
                        self._listConstructors[field.proto.name] = eval(
                            "self._capnp_schema.%s.new_message" % subTypeName
                        )
                    except BaseException:
                        continue

                self.__dict__["list_%s_constructor" % field.proto.name] = self._listConstructors[field.proto.name]

        self._db = db if db else j.data.kvs.getMemoryStore(name=self.namespace, namespace=self.namespace)
        # for now we do index same as database
        self._index = indexDb if indexDb else self._db

        self.modelBaseClass = modelBaseClass if modelBaseClass else ModelBase

        self._init()
        JSBASE.__init__(self)

    def _init(self, **kwargs):
        pass

    @property
    def indexDB(self):
        return self._index

    def _arraysFromArgsToString(self, names, args):
        """
        will translate arrays or non arrays to string in format
            '$name1','$name2'

        @param names tells us which items from the args which needs to be processed

        items to process in args are:
            can be "a,b,c"
            can be "'a','b','c'"
            can be ["a","b","c"]
            can be "a"

        @param args is dict with arguments to check
        """
        for name in names:
            if name in args:
                if j.data.types.string.check(args[name]) and "," in args[name]:
                    args[name] = [item.strip().strip("'").strip() for item in args[name].split(",")]
                elif not j.data.types.list.check(args[name]):
                    args[name] = [args[name]]
                args[name] = ",".join(["'%s'" % item for item in args[name]])
        return args

    @property
    def objType(self):
        return self._capnp_schema.schema.node.displayName

    def new(self, key=""):
        model = self.modelBaseClass(key=key, new=True, collection=self)
        return model

    def exists(self, key):
        return self._db.exists(key)

    def get(self, key, autoCreate=False):
        if self._db.inMem:
            if key in self._db.db:
                model = self._db.db[key]
            else:
                if autoCreate:
                    return self.new(key=key)
                else:
                    raise j.exceptions.Input(message="Could not find key:%s for model:%s" % (key, self.category))
        else:

            model = self.modelBaseClass(key=key, new=autoCreate, collection=self)
        return model

    def list(self, **kwargs):
        """
        List all keys of a index
        """
        res = []

        return res

    def find(self, **kwargs):
        """
        finds all entries matching kwargs

        e.g.
        email="reem@threefold.tech", name="reem"
        """
        res = []
        for key in self.list(**kwargs):
            res.append(self.get(key))
        return res

    def destroy(self):
        self._db.destroy()
        self._index.destroy()

    def lookupGet(self, name, key):
        return self._index.lookupGet(name, key)

    def lookupSet(self, name, key, fkey):
        """
        @param fkey is foreign key
        """
        return self._index.lookupSet(name, key, fkey)

    def lookupDestroy(self, name):
        return self._index.lookupDestroy(name)
