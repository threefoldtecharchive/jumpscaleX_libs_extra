from Jumpscale import j
import gevent

from gevent import queue
from gevent import spawn
import inspect


JSBASE = j.baseclasses.object


class ActorBase(JSBASE):
    def __init__(self, community, data):
        JSBASE.__init__(self)
        self.community = community
        self.data = data
        self.q_in = queue.Queue()
        self.q_out = queue.Queue()
        self.task_id_current = 0
        self.greenlet_task = spawn(self._main)
        self.monitors = {}

        # walks over monitor methods & gets them started as greenlet
        for method in inspect.getmembers(self, predicate=inspect.ismethod):
            mname = method[0]
            print("iterate over method:%s" % mname)

            if mname.startswith("monitor"):
                if mname in ["monitor_running"]:
                    continue
                print("found monitor: %s" % mname)
                method = getattr(self, mname)
                self.monitors[mname[8:]] = spawn(method)
            else:
                if mname.startswith("action_"):
                    self._stateobj_get(mname)  # make sure the action object exists

        spawn(self._main)

    def _main(self):
        self._log_info("%s:mainloop started" % self)
        # make sure communication is only 1 way
        # TODO: put metadata
        while True:
            action, data = self.q_in.get()
            self._log_info("%s:action:%s:%s" % (self, action, data))
            method = getattr(self, action)
            res = method(data)
            print("main res:%s" % res)
            self.q_out.put([0, res])

    def _stateobj_get(self, name):
        for item in self.data.stateobj.actions:
            if item.name == name:
                return item
        a = self.data.stateobj.actions.new()
        a.name = name

    def _coordinator_action_ask(self, name):
        arg = None
        cmd = [name, arg]
        self.q_in.put(cmd)
        rc, res = self.q_out.get()
        return rc, res

    # def monitor_running(self):
    #     return self.greenlet_monitor.dead==False

    # def action_running(self,name):
    #     from IPython import embed;embed(colors='Linux')
    #     k

    def data_set(self, data):
        """
        set the data from the service
        :param data:
        :return:
        """
        if "stateobj" in data:
            raise j.exceptions.Base("cannot update stateobj, needs to happe from within service/coordinator")
        if "stateobj" in data:
            raise j.exceptions.Base("cannot update state, needs to happe from within service/coordinator")
        self.data.__dict__.update(data)

    def data_get(self):
        """
        :return jumspcale complex type which is the config of this service or coordinator:
        """
        return self.data

    def data_register(self):
        """
        will register the data in persistent storage
        :return:
        """
        print("SAVE")

    def __str__(self):
        return "coordinator:%s" % self._name

    __repr__ = __str__
