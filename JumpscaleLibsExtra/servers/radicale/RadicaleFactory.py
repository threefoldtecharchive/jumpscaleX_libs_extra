import sys
import os

from Jumpscale import j


class RadicaleFactory(j.baseclasses.object):

    __jslocation__ = "j.servers.radicale"

    @property
    def wsgi_app(self):
        sys.path.append(os.path.dirname(__file__))
        from .radicale import application

        return application
