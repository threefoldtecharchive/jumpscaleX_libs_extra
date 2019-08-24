from Jumpscale import j


class KosmosUniverse(j.baseclasses.object):
    def _init(self, **kwargs):
        pass

    def __getattr__(self, attr):
        # if self.__class__._MODEL is None:
        #     return self.__getattribute__(attr)
        if attr in self.__class__._MODEL.schema.properties_list:
            return self.data.__getattribute__(attr)
        return self.__getattribute__(attr)
        # raise j.exceptions.Base("could not find attribute:%s"%attr)

    def __dir__(self):
        r = self.__class__._MODEL.schema.properties_list
        for item in self.__dict__.keys():
            if item not in r:
                r.append(item)
        return r

    def __setattr__(self, key, value):
        if "data" in self.__dict__ and key in self.__class__._MODEL.schema.properties_list:
            # if value != self.data.__getattribute__(key):
            self._log_debug("SET:%s:%s" % (key, value))
            self.__dict__["data"].__setattr__(key, value)

        self.__dict__[key] = value

    def __str__(self):
        try:
            out = "%s\n%s\n" % (self.__class__.__name__, self.data)
        except:
            out = str(self.__class__) + "\n"
            out += j.core.text.prefix(" - ", self.data)
        return out

    __repr__ = __str__
