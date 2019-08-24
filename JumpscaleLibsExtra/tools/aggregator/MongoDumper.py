import tools.aggregator.Dumper as Dumper
from Jumpscale import j


class MongoDumper(Dumper.BaseDumper):
    QUEUE = "queues:reality"

    def __init__(self, cidr="127.0.0.1", ports=[7777]):
        super(MongoDumper, self).__init__(cidr, ports=[ports])

    def dump(self, redis):
        while True:
            key = redis.lpop(self.QUEUE)
            if key is None:
                return
            key = key.decode()

            data = redis.get("reality:%s" % key)
            data = data.decode()

            obj = j.data.serializers.json.loads(data)

            ns, _, objtype = obj["modeltype"].rpartition(".")
            if ns == "":
                ns = "system"
            if not hasattr(j.data.models, ns):
                raise Exception('Unknown namespace "%s"' % ns)
            space = getattr(j.data.models, ns)

            if not hasattr(space, objtype):
                raise Exception('Unknown model "%s"' % objtype)
            model = getattr(space, objtype)

            instance = model.from_json(obj["json"])
            instance.save()
