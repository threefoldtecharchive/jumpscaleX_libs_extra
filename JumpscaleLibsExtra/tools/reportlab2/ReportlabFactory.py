from Jumpscale import j

JSBASE = j.baseclasses.object


class ReportlabFactory(j.baseclasses.object):
    __jslocation__ = "j.tools.reportlab2"

    def get_doc(self, page_size):
        """ gets a RL document"""
        pass
