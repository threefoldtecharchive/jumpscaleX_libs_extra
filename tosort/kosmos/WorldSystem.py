from Jumpscale import j


from .BASE_CLASSES.CoordinatorBase import CoordinatorBase
from .BASE_CLASSES.ServiceBase import ServiceBase
import gevent
from gevent import monkey
import time
from gevent import event, sleep


SCHEMA_SERVICE_STATE = """
@url = world.service.state
state = "new,init,active,error" (S)  #needs to become enumeration, so no mistakes can be made, now string
actions_active = "" (LO) !world.service.state.action
action_last = 0 (I)
"""

SCHEMA_SERVICE_ACTION = """

@url = world.service.action
name = ""
args = ""
kwargs = ""
result = ""
actionid = 0 (I)            #only when used in a ZDB, for historical purposes
time_ask = 0 (D)            #when was it asked to start
time_start = 0 (D)          #if 0 then not started then still needs to execute
time_end = 0 (D)            #if end date then was ok
blocked = False (B)         #blocked means stop trying to execute, cannot continue
error = False (B)           #if error, encountered error, as ling as timeout_error not reached keep on trying
timeout_exec = 0 (I)        #max time to try and execute, in sec
timeout_error = 0 (I)       #max time to try to execute even in error state
error_msg = "" (S) 
logs = "" (LO) !world.service.action.log


@url = world.service.action.log
msg = ""
time = 0 (D)
cat = "" 
level = 0 (I)

"""


class WorldSystem(JSFactoryBase):

    __jslocation__ = "j.world.system"
    _ServiceBase = ServiceBase
    _CoordinatorBase = CoordinatorBase

    def __init__(self):

        JSFactoryBase.__init__(self)
        self._bcdb = j.data.bcdb.get("world")
        self._schema_service_state = j.data.schema.get_from_text(SCHEMA_SERVICE_STATE)
        self._schema_service_action = self._bcdb.model_get(schema=SCHEMA_SERVICE_ACTION)

    def test(self):
        """
        js_shell 'j.world.system.test()'
        """

        bcdb = self._bcdb
        bcdb.reset()

        hv = j.world.hypervisor

        # servicepool is a chosen name for the group of services, is optional
        # when id None which is default, then will be a new one or will check if there is an instance with the name for the servicepool
        # if id not None, it will check if it exists, name should not be given then, or at least the same

        vb = hv.ServiceVirtualBox(id=None, key="myhypervisor", servicepool="tf_gent")

        assert vb.data.description == ""
        print(vb.data)

        vb.data.description = "test"
        vb.data_save()

        vb2 = hv.ServiceVirtualBox(id=None, key="myhypervisor", servicepool="tf_gent")
        assert vb2.id == vb.id  # should have same id
        assert vb2.key == vb.key  # should have same key

        vb3 = hv.ServiceVirtualBox(id=vb2.id)

        assert vb3.key == vb.key

        # TODO: need to move logic with keys to BCDB, on wrong location now
        # TODO: need to implement reload index when index not there or broken

        state = vb3.state

        action = vb3.task1(descr="mytask_test")

        j.shell()
