from Jumpscale import j
import os
import sys


class TFBIZMODELInstaller( j.baseclasses.object):

    __jslocation__ = "j.tools.tfbizmodel"

    def _init(self, **kwargs):
        j.application.start("tfbizmodel")

    @property
    def factory(self):
        sys.path.append(f"{os.environ['HOME']}/tfweb/production/github/threefoldtech/bizmodel/lib")
        from TFBizModelFactory import TFBizModelFactory
        f = TFBizModelFactory()
        return f

    def calc(self):
        """
        kosmos 'j.tools.tfbizmodel.calc()'
        """
        self.factory.calc()


