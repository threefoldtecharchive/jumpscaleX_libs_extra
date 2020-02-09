from Jumpscale import j
import tarantool
from .TarantoolDB import TarantoolDB

# import itertools


# import sys
# sys.path.append(".")
# from tarantool_queue import *

import tarantool

JSBASE = j.baseclasses.object


class TarantoolQueue(j.baseclasses.object):
    def __init__(self, tarantoolclient, name, ttl=0, delay=0):
        """The default connection parameters are: host='localhost', port=9999, db=0"""
        JSBASE.__init__(self)
        self.client = tarantoolclient
        self.db = self.client.db
        self.name = name
        if ttl != 0:
            raise j.exceptions.Base("not implemented")
        else:
            try:
                self.db.eval('queue.create_tube("%s","fifottl")' % name)
            except Exception as e:
                if "already exists" not in str(e):
                    raise j.exceptions.Base(e)

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item, ttl=None, delay=0):
        """Put item into the queue."""
        args = {}
        if ttl is not None:
            args["ttl"] = ttl
            args["delay"] = delay

        self.db.call("queue.tube.%s:put" % self.name, item, args)
        # else:
        #     #TODO: does not work yet? don't know how to pass
        #     self.db.call("queue.tube.%s:put"%self.name,item)

    def get(self, timeout=1000, autoAcknowledge=True):
        """
        Remove and return an item from the queue.
        if necessary until an item is available.
        """
        res = self.db.call("queue.tube.%s:take" % self.name, timeout)
        if autoAcknowledge and len(res) > 0:
            res = self.db.call("queue.tube.%s:ack" % self.name, res[0])
        return res

    def fetch(self, block=True, timeout=None):
        """ Like get but without remove"""
        if block:
            item = self.__db.brpoplpush(self.key, self.key, timeout)
        else:
            item = self.__db.lindex(self.key, 0)
        return item

    def set_expire(self, time):
        self.__db.expire(self.key, time)

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)
