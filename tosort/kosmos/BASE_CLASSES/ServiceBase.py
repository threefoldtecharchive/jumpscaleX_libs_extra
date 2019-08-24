from Jumpscale import j


from gevent import queue
from gevent import spawn
from gevent.event import Event

# import inspect

skip_for_debug = False


def action(func):
    def wrapper_action(*args, **kwargs):
        self = args[0]
        args = args[1:]
        self._log_debug(str(func))
        if self._running is None:
            self.service_manage()
        name = func.__name__
        if skip_for_debug or "noqueue" in kwargs:
            if "noqueue" in kwargs:
                kwargs.pop("noqueue")
            res = func(*args, **kwargs)
            return res
        else:
            event = Event()
            action = self._action_new(name=name, args=args, kwargs=kwargs)
            self.action_queue.put((func, args, kwargs, event, action.id))
            event.wait(1000.0)  # will wait for processing
            res = j.data.serializers.msgpack.loads(action.result)
            self._log_debug("METHOD EXECUTED OK")
            return action

    return wrapper_action


class ServiceBase(j.baseclasses.object):

    _MODEL = None

    def __init__(self, id=None, key=None, servicepool=None):

        j.baseclasses.object.__init__(self)

        if self.__class__._MODEL is None:
            self.__class__._MODEL = j.world.system._bcdb.model_get(schema=self.__class__._SCHEMA_TXT)

        self.actions = {}
        self._state = None
        self._state_last_save_hash = None  # to see when there is change
        self._data = None
        self._id = id
        self._key = None
        self._running = None
        self.action_queue = queue.Queue()

        if id is None and (key is not None or servicepool is not None):
            if servicepool is not None and key is None:
                self.error_bug_raise("servicepool cannot be None when key is also None, key needs to be specified")
            # need to instantiate, because data given which needs to be remembered
            if servicepool is not None:
                key = "%s__%s" % (servicepool, key)
            else:
                if key.find("__") != -1:
                    self.error_bug_raise("__ should not be in keyname")

            self._key = key

        self.data  # will fetch the key

        self._redis_key_state = self.key.encode() + b":state"
        self._redis_key_actions_now = b"actions:last"

        self._running = None

    def _action_new(self, name, args, kwargs):

        args2 = j.data.serializers.msgpack.dumps(args)
        kwargs2 = j.data.serializers.msgpack.dumps(kwargs)
        data = j.world.system._schema_service_action.new()
        data.args = args
        data.kwargs2 = kwargs2
        data.name = name
        data.time_ask = j.data.time.epoch
        # data.actionid = j.clients.credis_core.incr(self._redis_key_actions_now)
        # hkey,key=self._action_key(data.actionid)
        # j.clients.credis_core.hset(hkey,key,data._data)

        self.actions[data.id] = data

        return data

    def _action_key(self, action_id):
        key = "a:%s" % (int(action_id / 1000))
        return (key.encode(), str(action_id).encode())

    def _action_get(self, action_id):
        hkey, key = self._action_key(action_id)
        r = j.clients.credis_core.hget(hkey, key)
        if r is None:
            raise j.exceptions.Base("cannot find action with id:%s" % action_id)
        res = j.world.system._schema_service_action.schema.new(data=r)
        return res

    @property
    def key(self):
        if self._key is None:
            if self._id is None:
                return None
            self.data
        return self._key

    @property
    def _model(self):
        return self.__class__._MODEL

    @property
    def id(self):
        if self._data is not None:
            self._id = self._data.id
        elif self._id is None and self.key is not None:
            self._id = self._MODEL.get_id_from_key(self.key)
        return self._id

    @property
    def data(self):
        if self._data is None:
            if self.id is None:
                self._data = self._MODEL.new()
                self._data.key = self._key
            else:
                self._data = self._MODEL.get(obj_id=self.id)
                self._key = self._data.key

            if self._data is None:
                j.shell()

        return self._data

    @property
    def state(self):

        if self._state is None:
            r = j.clients.credis_core.get(self._redis_key_state)
            if r is None:
                self._state = j.world.system._schema_service_state.new()
            else:

                j.shell()

        return self._state

    def data_save(self):
        self.data.save()

    def service_unmanage(self):

        j.shell()

    def service_manage(self):
        """
        get the service to basically run in memory, means checking the monitoring, make the model reality...
        :return:
        """
        if self._running is None:
            self.q_in = queue.Queue()
            self.q_out = queue.Queue()
            self.task_id_current = 0
            self.greenlet_task = spawn(self._main)

            # for method in inspect.getmembers(self, predicate=inspect.ismethod):
            #     j.shell()
            #     w
            #     mkey = method[0]
            #     print("iterate over method:%s"%mkey)
            #
            #     if mkey.startswith("monitor"):
            #         if mkey in ["monitor_running"]:
            #             continue
            #         print("found monitor: %s"%mkey)
            #         method = getattr(self,mkey)
            #         self.monitors[mkey[8:]] = spawn(method)
            #     else:
            #         if mkey.startswith("action_"):
            #             self._stateobj_get(mkey) #make sure the action object exists

    def _main(self):
        self._log_info("%s:mainloop started" % self)
        # make sure communication is only 1 way
        # TODO: put metadata
        while True:
            func, args, kwargs, event, action_id = self.action_queue.get()
            a = self.actions[action_id]
            self._log_info("action execute:\n%s" % a)
            a.time_start = j.data.time.epoch
            res = func(self, *args, **kwargs)
            print("main res:%s" % res)
            a.result = j.data.serializers.msgpack.dumps(res)
            a.save()
            event.set()

    def _stateobj_get(self, key):
        for item in self.data.stateobj.actions:
            if item.key == key:
                return item
        a = self.data.stateobj.actions.new()
        a.key = key

    def _coordinator_action_ask(self, key):
        arg = None
        cmd = [key, arg]
        self.q_in.put(cmd)
        rc, res = self.q_out.get()
        return rc, res

    @property
    def _instance(self):
        return self.data.instance

    #
    #
    # class ServiceBase(ActorBase):
    #
    #     def __init__(self,coordinator,key,instance,data):
    #         data.key = key
    #         data.instance = instance
    #         self.__key = None
    #         ActorBase.__init__(self, coordinator=coordinator, data=data)
    #         self.init()
    #
    #     def init(self):
    #         pass
    #
    #
    #     @property
    #     def _key(self):
    #         if self.__key == None:
    #             self.__key ="%s_%s"%(j.core.text.strip_to_ascii_dense(self.key),j.core.text.strip_to_ascii_dense(self.instance))
    #         return self.__key
    #
    #
    def __str__(self):
        out = "service:%s (%s)\n\n" % (self.key, self.id)
        out += str(self.data)
        out += "\n"
        return out

    __repr__ = __str__
