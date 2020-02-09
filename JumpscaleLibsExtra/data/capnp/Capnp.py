import sys
from Jumpscale import j
from collections import OrderedDict

# import capnp

from .ModelBaseCollection import ModelBaseCollection
from .ModelBaseData import ModelBaseData
from .ModelBase import ModelBase


class Tools(j.baseclasses.object):
    def listInDictCreation(self, listInDict, name, manipulateDef=None):
        """
        check name exist in the dict
        then check its a dict, if yes walk over it and make sure they become strings or use the manipulateDef function
        string 'a,b,c' gets translated to list
        @param manipulateDef if None then will make it a string, could be e.g. int if you want to have all elements to be converted to int
        """
        if name in listInDict:
            if j.data.types.list.check(listInDict[name]):
                if manipulateDef is None:
                    listInDict[name] = [str(item).strip() for item in listInDict[name]]
                else:
                    listInDict[name] = [manipulateDef(item) for item in listInDict[name]]
            else:
                if manipulateDef is None:
                    if "," in str(listInDict[name]):
                        listInDict[name] = [item.strip() for item in listInDict[name].split(",") if item.strip() != ""]
                    else:
                        listInDict[name] = [str(listInDict[name])]
                else:
                    listInDict[name] = [manipulateDef(listInDict[name])]
        return listInDict


class Capnp(j.baseclasses.object):
    """
    """

    __jslocation__ = "j.data.capnp"

    def _init(self, **kwargs):
        self._schema_cache = {}
        self._capnpVarDir = j.sal.fs.joinPaths(j.dirs.VARDIR, "capnp")
        j.sal.fs.createDir(self._capnpVarDir)
        if self._capnpVarDir not in sys.path:
            sys.path.append(self._capnpVarDir)
        self.tools = Tools()

    def getModelBaseClass(self):
        return ModelBase

    def getModelBaseClassWithData(self):
        return ModelBaseWithData

    def getModelBaseClassCollection(self):
        return ModelBaseCollection

    def getModelCollection(
        self,
        schema,
        category,
        namespace=None,
        modelBaseClass=None,
        modelBaseCollectionClass=None,
        db=None,
        indexDb=None,
    ):
        """
        @param schema is capnp_schema

        example to use:
            ```
            #if we use a modelBaseClass do something like
            ModelBaseWithData = j.data.capnp.getModelBaseClass()
            class MyModelBase(ModelBaseWithData):
                def index(self):
                    # put indexes in db as specified
                    ind = "%s" % (self.dbobj.path)
                    self._index.index({ind: self.key})


            import capnp
            #there is model.capnp in $libdir/Jumpscale/tools/issuemanager
            from JumpscaleLibs.tools.issuemanager import model as ModelCapnp

            mydb=j.data.kvs.getMemoryStore(name="mymemdb")

            collection=j.data.capnp.getModelCollection(schema=ModelCapnp,
                                    category="issue",
                                    modelBaseClass=MyModelBase,
                                    db=mydb)

            ```
        """
        if modelBaseCollectionClass is None:
            modelBaseCollectionClass = ModelBaseCollection

        return modelBaseCollectionClass(
            schema=schema, category=category, namespace=namespace, db=db, indexDb=indexDb, modelBaseClass=modelBaseClass
        )

    def getId(self, schemaInText):
        r = None
        for line in schemaInText.split("\n"):
            line = line.strip()
            if line.startswith("@0x"):
                if r:
                    raise j.exceptions.Input("can only have 1 capnp_id in file", data=schemaInText)
                r = line.strip()[3:-1]
        if not r:
            raise j.exceptions.Input("did not find capnp_id in file", data=schemaInText)
        return r

    def removeFromCache(self, schemaId):
        self._schema_cache.pop(schemaId, None)

    def resetSchema(self, schemaId):
        self._schema_cache.pop(schemaId, None)
        nameOnFS = "schema_%s.capnp" % (schemaId)
        path = j.sal.fs.joinPaths(self._capnpVarDir, nameOnFS)
        if j.sal.fs.exists(path):
            j.sal.fs.remove(path)

    def _getSchemas(self, schemaInText):
        import capnp

        schemaInText = j.core.text.strip(schemaInText)
        schemaInText = schemaInText.strip() + "\n"
        schemaId = self.getId(schemaInText)
        if schemaId not in self._schema_cache:
            nameOnFS = "schema_%s.capnp" % (schemaId)
            path = j.sal.fs.joinPaths(self._capnpVarDir, nameOnFS)
            j.sal.fs.writeFile(filename=path, contents=schemaInText, append=False)
            parser = capnp.SchemaParser()
            try:
                schema = parser.load(path)
            except Exception as e:
                msg = str(e)
                raise j.exceptions.Base("%s\n\nERROR:Could not parse capnp schema:\n%s" % (schemaInText, msg))
            self._schema_cache[schemaId] = schema
        return self._schema_cache[schemaId]

    def getSchemaFromText(self, schemaInText, name="Schema"):
        # if not schemaInText.strip():
        #     schemaInText = (
        #         """
        #     @%s;
        #     struct Schema {
        #
        #     }
        #     """
        #         % j.data.idgenerator.generateCapnpID()
        #     )

        schemas = self._getSchemas(schemaInText)
        schema = eval("schemas.%s" % name)
        return schema

    def getSchemaFromPath(self, path, name):
        """
        @param path is path to schema
        """
        content = j.sal.fs.readFile(path)
        return self.getSchemaFromText(schemaInText=content, name=name)

    def _ensure_dict(self, args):
        """
        make sure the argument schema are of the type dict
        capnp doesn't handle building a message with OrderedDict properly
        """
        if isinstance(args, OrderedDict):
            args = dict(args)
            for k, v in args.items():
                args[k] = self._ensure_dict(v)
        if isinstance(args, list):
            for i, v in enumerate(args):
                args.insert(i, self._ensure_dict(v))
                args.pop(i + 1)
        return args

    def getObj(self, schemaInText, name="Schema", args={}, binaryData=None):
        """
        @PARAM schemaInText is capnp schema
        @PARAM name is the name of the obj in the schema e.g. Issue
        @PARAM args are the starting date for the obj, normally a dict
        @PARAM binaryData is this is given then its the binary data to
               create the obj from, cannot be sed together with args
               (its one or the other)
        """

        # . are removed from . to Uppercase
        args = args.copy()  # to not change the args passed in argument
        for key in list(args.keys()):
            sanitize_key = j.core.text.sanitize_key(key)
            if key != sanitize_key:
                args[sanitize_key] = args[key]
                args.pop(key)

        schema = self.getSchemaFromText(schemaInText, name=name)

        if binaryData is not None and binaryData != b"":
            obj = schema.from_bytes_packed(binaryData).as_builder()
        else:
            try:
                args = self._ensure_dict(args)
                obj = schema.new_message(**args)
            except Exception as e:
                if str(e).find("has no such member") != -1:
                    msg = "cannot create data for schema from "
                    msg += "arguments, property missing\n"
                    msg += "arguments:\n%s\n" % j.data.serializers.json.dumps(args, sort_keys=True, indent=True)
                    msg += "schema:\n%s" % schemaInText
                    ee = str(e).split("stack:")[0]
                    ee = ee.split("failed:")[1]
                    msg += "capnperror:%s" % ee
                    self._log_debug(msg)
                    raise j.exceptions.Input(message=msg)
                if str(e).find("Value type mismatch") != -1:
                    msg = "cannot create data for schema from "
                    msg += "arguments, value type mismatch.\n"
                    msg += "arguments:\n%s\n" % j.data.serializers.json.dumps(args, sort_keys=True, indent=True)
                    msg += "schema:\n%s" % schemaInText
                    ee = str(e).split("stack:")[0]
                    ee = ee.split("failed:")[1]
                    msg += "capnperror:%s" % ee
                    self._log_debug(msg)
                    raise j.exceptions.Input(message=msg)
                raise e

        return obj

    def test(self):
        """
        kosmos 'j.data.capnp.test()'
        """
        import time

        capnpschema = """
        @0x9fc1ac9f09464fc9;

        struct Issue {

          state @0 :State;
          enum State {
            new @0;
            ok @1;
            error @2;
            disabled @3;
          }

          #name of actor e.g. node.ssh (role is the first part of it)
          name @1 :Text;
          descr @2 :Text;

        }
        """

        # dummy test, not used later
        obj = self.getObj(capnpschema, name="Issue")
        obj.state = "ok"

        # now we just get the capnp schema for this object
        schema = self.getSchemaFromText(capnpschema, name="Issue")

        # mydb = j.data.kvs.getRedisStore(name="mymemdb")
        mydb = None  # is memory

        collection = self.getModelCollection(schema, category="test", modelBaseClass=None, db=mydb)
        start = time.time()
        self._log_debug("start populate 100.000 records")
        collection.logger.disabled = True
        for i in range(100000):
            obj = collection.new()
            obj.dbobj.name = "test%s" % i
            obj.save()

        self._log_debug("population done")
        end_populate = time.time()
        collection.logger.disabled = False

        self._log_debug(collection.find(name="test839"))
        end_find = time.time()
        self._log_debug("population in %.2fs" % (end_populate - start))
        self._log_debug("find in %.2fs" % (end_find - end_populate))

        # tests need to be non-interactive.  use a different function name
        # (e.g. noninteractive_test or just _test())
        # from IPython import embed
        # embed(colors='Linux')

    def testWithRedis(self):
        capnpschema = """
        @0x93c1ac9f09464fc9;
        struct Issue {
          state @0 :State;
          enum State {
            new @0;
            ok @1;
            error @2;
            disabled @3;
          }
          #name of actor e.g. node.ssh (role is the first part of it)
          name @1 :Text;
          tlist @2: List(Text);
          olist @3: List(Issue2);
          struct Issue2 {
              state @0 :State;
              enum State {
                new @0;
                ok @1;
                error @2;
                disabled @3;
              }
              text @1: Text;
          }
        }
        """
        # mydb = j.data.kvs.getRedisStore("test")
        mydb = j.data.kvs.getRedisStore(name="test", unixsocket="%s/redis.sock" % j.dirs.TMPDIR)
        schema = self.getSchemaFromText(capnpschema, name="Issue")
        collection = self.getModelCollection(schema, category="test", modelBaseClass=None, db=mydb, indexDb=mydb)
        for i in range(100):
            obj = collection.new()
            obj.dbobj.name = "test%s" % i
            obj.save()
            self._log_debug(collection.list())

        subobj = collection.list_olist_constructor(state="new", text="something")
        obj.addSubItem("olist", subobj)

        subobj = collection.list_tlist_constructor("sometext")
        obj.addSubItem(name="tlist", data=subobj)
        obj.addSubItem(name="tlist", data="sometext2")

        self._log_debug(obj)

        obj.initSubItem("tlist")
        assert len(obj.list_tlist) == 2

        obj.addSubItem(name="tlist", data="sometext3")
        assert len(obj.list_tlist) == 3

        obj.reSerialize()

    def getJSON(self, obj):
        configdata2 = obj.to_dict()
        ddict2 = OrderedDict(configdata2)
        return j.data.serializers.json.dumps(ddict2, sort_keys=True, indent=True)

    def getBinaryData(self, obj):
        return obj.to_bytes_packed()

    # def getMemoryObj(self, schema, *args, **kwargs):
    #     """
    #     creates an object similar as a capnp message but without the constraint of the capnpn on the type and list.
    #     Use this to store capnp object in memory instead of using directly capnp object, BUT BE AWARE THIS WILL TAKE MUCH MORE MEMORY
    #     It will be converted in capnp message when saved
    #     """
    #     msg = schema.new_message(**kwargs)
    #     obj = MemoryObject(msg.to_dict(verbose=True), schema=schema)
    #     return obj
