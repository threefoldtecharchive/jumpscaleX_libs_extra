from Jumpscale import j
from .RacktivityClient import RacktivityClient

JSConfigs = j.baseclasses.object_config_collection


class RacktivityFactory(JSConfigs):
    # check https://github.com/threefoldtech/jumpscaleX_libs_extra/issues/7
    _CHILDCLASS = RacktivityClient
