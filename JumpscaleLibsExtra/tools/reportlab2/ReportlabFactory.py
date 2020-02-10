from Jumpscale import j
from .RLDoc import RLDoc

JSBASE = j.baseclasses.object


class ReportlabFactory(j.baseclasses.object):
    __jslocation__ = "j.tools.reportlab2"

    def get_doc(self, file_name):
        """ gets a RL document"""
        return RLDoc(file_name)

    def test(self):

        d = self.get_doc("/sandbox/code/test_out.pdf")
        d.default_set()
        d.configure()
        d.header_text_set("header")
        d.footer_text_set("footer")
        d.image_add("/sandbox/code/3bot.jpg", height=200, width=200)
        d.h1_add("Heading 1")
        d.h1_add("Heading 1 to the right", custom_style={"alignment": 2})
        d.h2_add("Heading 2")
        d.h3_add("Heading 3")
        d.text_add('hello world this is the awesome <a color="blue" href="www.3bot.org">3bot</a> ' * 50)
        d.table_create(
            [["id", "name", "age", "nationality"], ["0", "foo", 15, "Egyptian"], ["1", "bar", 71, "Belgian"]]
        )
        d.save()
