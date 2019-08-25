from .GoogleCompute import GoogleCompute
from Jumpscale import j

JSBASE = j.baseclasses.object_config_collection


class GoogleComputeFactory(JSBASE):
    __jslocation__ = "j.clients.google_compute"
    _CHILDCLASS = GoogleCompute
