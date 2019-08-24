import tools.aggregator.Dumper as Dumper
from Jumpscale import j


class ECODumper(Dumper.BaseDumper):
    QUEUE = "queues:eco"

    def __init__(self, cidr="127.0.0.1", ports=[7777]):
        super(ECODumper, self).__init__(cidr, ports=ports)

    def dump(self, redis):
        """

        eco = {}
        eco.key = key
        eco.message = message
        eco.messagepub = messagepub
        eco.code = code
        eco.funcname = funcname
        eco.funcfilepath = funcfilepath
        eco.closetime = 0
        eco.occurrences = 1
        eco.lasttime = newtime
        eco.backtrace = backtrace
        eco.level = level
        eco.type = type
        eco.tags = tags

        :param redis:
        :return:
        """
        while True:
            key = redis.lpop(self.QUEUE)
            if key is None:
                return
            key = key.decode()

            data = redis.get("eco:%s" % key)
            data = data.decode()

            obj = j.data.serializers.json.loads(data)

            eco = j.data.models_system.Errorcondition()
            eco.guid = obj["key"]
            for key in (
                "errormessage",
                "errormessagepub",
                "code",
                "funcname",
                "funcfilename",
                "closetime",
                "occurrences",
                "lasttime",
                "backtrace",
                "level",
                "type",
                "tags",
                "gid",
                "nid",
            ):
                setattr(eco, key, obj.get(key))

            eco.save()
