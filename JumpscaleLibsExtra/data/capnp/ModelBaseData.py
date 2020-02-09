from Jumpscale import j

# from collections import OrderedDict

from .ModelBase import ModelBase


class ModelBaseData(ModelBase):
    def __init__(self, key="", new=False, collection=None):
        super().__init__(key=key, new=new, collection=collection)
        self._data_schema = None
        self._data = None

    @property
    def data(self):
        if self._data is None:
            self._data = j.data.capnp.getObj(self.dbobj.dataSchema, binaryData=self.dbobj.data)
        return self._data

    @property
    def dataSchema(self):
        return j.data.capnp.getSchema(self.dbobj.dataSchema)

    @property
    def dataJSON(self):
        return j.data.capnp.getJSON(self.data)

    @property
    def dataBinary(self):
        return j.data.capnp.getBinaryData(self.data)


def getText(text):
    return str(object=text)


def getInt(nr):
    return int(nr)
