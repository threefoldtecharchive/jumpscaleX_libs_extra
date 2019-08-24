from Jumpscale import j
import time
import os
import collections
import hashlib


Stats = collections.namedtuple(
    "Stats", "h_nr m_nr h_avg m_epoch m_total h_total m_avg m_last epoch " + "m_max val h_max key tags h_epoch"
)

Log = collections.namedtuple("Log", "level message node epoch tags")
JSBASE = j.baseclasses.object


class AggregatorClient(j.baseclasses.object):
    def __init__(self, redis, nodename):
        self.redis = redis
        self._sha = dict()

        JSBASE.__init__(self)
        path = os.path.dirname(__file__)
        luapaths = j.sal.fs.listFilesInDir(path, recursive=False, filter="*.lua", followSymlinks=True)
        for luapath in luapaths:
            basename = j.sal.fs.getBaseName(luapath).replace(".lua", "")
            lua = j.sal.fs.readFile(luapath)
            self._sha[basename] = self.redis.script_load(lua)

        self.nodename = nodename

    def measure(self, key, tags, value, timestamp=None):
        """
        @param key is well chosen location in a tree structure e.g. key="%s.%s"%(self.nodename,dev) e.g. myserver.eth0
           key needs to be unique
        @param tags node:kds dim:iops location:elgouna  : this allows aggregation in influxdb level
        @param timestamp stats timestamp, default to `now`
        """
        return self._measure(key, tags, value, type="A", timestamp=timestamp)

    def measureDiff(self, key, tags, value, timestamp=None):
        return self._measure(key, tags, value, type="D", timestamp=timestamp)

    def _measure(self, key, tags, value, type, timestamp=None):
        """
        in redis:

        local key=KEYS[1]
        local value = tonumber(ARGV[1])
        local now = tonumber(ARGV[2])
        local type=ARGV[3]
        local tags=ARGV[4]
        local node=ARGV[5]

        """
        if timestamp is None:
            timestamp = int(time.time())  # seconds
        res = self.redis.evalsha(self._sha["stat"], 1, key, value, str(timestamp), type, tags, self.nodename)

        return res

    def log(self, message, tags="", level=5, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time() * 1000)  # in millisecond

        self.redis.evalsha(self._sha["logs"], 1, self.nodename, message, tags, str(level), str(timestamp))

    def errorcondition(
        self,
        message,
        messagepub="",
        level=5,
        type="UNKNOWN",
        tags="",
        code="",
        funcname="",
        funcfilepath="",
        backtrace="",
        timestamp=None,
    ):
        """
        @param type: "BUG", "PERF", "OPS", "UNKNOWN"), default="UNKNOWN"

        usage of tags (tags can be used in all flexibility to ad meaning to an errorondition)
        e.g. nid: gid: aid: pid: jid: mjid: appname:
            nid = IntField()
            gid = IntField()
            aid = IntField(default=0)
            pid = IntField(default=0)
            jid = StringField(default='')  #TODO: *2 is this right, string???
            masterjid = IntField(default=0)  = mjid
            appname = StringField(default="")
            category = StringField(default="")


        core elements
            level = IntField(default=1, required=True)
            type = StringField(choices=("BUG", "PERF", "OPS", "UNKNOWN"), default="UNKNOWN", required=True)
            state = StringField(choices=("NEW", "ALERT", "CLOSED"), default="NEW", required=True)
            errormessage = StringField(default="")
            errormessagePub = StringField(default="")  # StringField()
            tags = StringField(default="")
            code = StringField()
            funcname = StringField(default="")
            funcfilepath = StringField(default="")
            backtrace = StringField()
            lasttime = IntField(default=j.data.time.getTimeEpoch())
            closetime = IntField(default=0)
            occurrences = IntField(default=0)
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        md5 = hashlib.md5()
        # key = md5(message + messagepub + code + funcname + funcfilepath)
        for p in (message, messagepub, code, funcname, funcfilepath):
            md5.update(p.encode())

        key = md5.hexdigest()
        res = self.redis.evalsha(
            self._sha["eco"],
            1,
            key,
            message,
            messagepub,
            str(level),
            type,
            tags,
            code,
            funcname,
            funcfilepath,
            backtrace,
            str(timestamp),
        )

    def statGet(self, key):
        """
        key is e.g. sda1.iops
        """
        data = self.redis.get("stats:%s:%s" % (self.nodename, key))
        if data is None:
            return {"val": None}

        return Stats(**j.data.serializers.json.loads(data))

    @property
    def stats(self):
        """
        iterator to go over stat objects
        """
        cursor = 0
        match = "stats:%s:*" % self.nodename
        while True:
            cursor, keys = self.redis.scan(cursor, match)
            for key in keys:
                yield Stats(**j.data.serializers.json.loads(self.redis.get(key)))

            if cursor == 0:
                break

    def logGet(self):
        """
        POPs oldest log object from queue & return as dict
        """
        data = self.redis.lpop("queues:logs")
        if data is None:
            return None

        Log(**j.data.serializers.json.loads(data))

    @property
    def logs(self):
        """
        Iterates over log objects (oldest first). Doesn't pop from the list
        """
        logs = self.redis.lrange("queues:logs", 0, 5000)
        for log in logs:
            yield Log(**j.data.serializers.json.loads(log))

    def ecoGet(self, key=None, removeFromQueue=True):
        """
        get errorcondition object from queue & return as dict
        if key not specified then get oldest ECO object & remove from queue if removeFromQueue is set
        if key set, do not remove from queue
        """
        if not key:
            if removeFromQueue:
                key = self.redis.lpop("queues:eco")
            else:
                key = self.redis.lindex("queues:eco", 0)

        if isinstance(key, bytes):
            key = key.decode()

        if key is None:
            return None

        data = self.redis.get("eco:%s" % key)
        if data is None:
            # shouldn't happen
            return None

        return j.data.serializers.json.loads(data)

    @property
    def ecos(self):
        """
        iterator (and POPs) to go over errorcondition objects (oldest first)
        """
        ecos = self.redis.lrange("queues:eco", 0, 1000)
        for eco in ecos:
            yield self.ecoGet(eco, removeFromQueue=False)

    def reality(self, key, json, modeltype, tags="", timestamp=None):
        """
        anything found on local node worth mentioning to central env e.g. disk information, network information
        each piece of info gets a well chosen key e.g. disk.sda1

        an easy way to structure the objects well is to use our model layer see:

        objects worth filling in:
        - j.data.models_system.Node()
        - j.data.models_system.Machine()
        - j.data.models_system.Nic()
        - j.data.models_system.Process()
        - j.data.models_system.VDisk()
        - disk=j.data.models_system.Disk()

        to then get the json do:
            disk.to_json()

        @param modeltype defines which model has been used e.g. "system.VDisk" (case sensitive) this allows the dumper to get the right model & insert in the right way in mongodb

        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        # 1 means there is 1 key, others are args
        return self.redis.evalsha(self._sha["reality"], 1, key, json, self.nodename, tags, modeltype, str(timestamp))

    def realityGet(self, key="", removeFromQueue=True):
        """
        if key not specified then get oldest object & remove from queue if removeFromQueue is set
        if key set, do not remove from queue
        """

        if not key:
            if removeFromQueue:
                key = self.redis.lpop("queues:reality")
            else:
                key = self.redis.lindex("queues:reality", 0)

        if isinstance(key, bytes):
            key = key.decode()

        if key is None:
            return None

        data = self.redis.get("reality:%s" % key)
        if data is None:
            # shouldn't happen
            return None

        return j.data.serializers.json.loads(data)

    @property
    def realities(self):
        """
        iterator to go over reality objects (oldest first)
        """
        realities = self.redis.lrange("queues:reality", 0, 1000)
        for reality in realities:
            self._log_debug(reality)
            yield self.realityGet(reality, removeFromQueue=False)
