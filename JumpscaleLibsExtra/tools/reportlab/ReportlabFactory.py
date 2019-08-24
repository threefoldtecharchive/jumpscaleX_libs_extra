from Jumpscale import j

JSBASE = j.baseclasses.object


class ReportlabFactory(j.baseclasses.object):
    def __init__(self):
        self.__jslocation__ = "j.tools.reportlab"
        JSBASE.__init__(self)

    @property
    def _RLDoc(self):
        from .RLDoc import RLDoc

        return RLDoc

    def doc_get(self, path):
        return self._RLDoc(path)

    def install(self):
        p = j.tools.prefab.local
        # if p.platformtype.platform_is_osx:
        #     self._log_info("will install mactex, is huge, will have to wait long")
        #     cmd="brew cask install mactex"
        #     p.core.run(cmd)
        # else:
        #     "latexmk"
        #     raise NotImplemented("need to do for ubuntu")
        p.runtimes.pip.install("reportlab")

    def test(self, install=False):
        """
        kosmos 'j.tools.reportlab.test(install=False)'

        :return:
        """
        if install:
            self.install()
        # self.test_generation()

        testdir = "/tmp/reportlab/"
        j.sal.fs.createDir(testdir)

        # path = j.clients.git.getContentPathFromURLorPath(
        #                         "https://github.com/threefoldfoundation/info_legal/tree/master/HR/dutch")

        url = "https://github.com/threefoldfoundation/info_legal/tree/master/HR/dutch"
        ds = j.tools.markdowndocs.load(url, name="test")

        doc = ds.doc_get("employment_agreement_v1")

        j.shell()

        logo_path = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldfoundation/info_legal/tree/master/images/threefold_logo.png"
        )

        doc = self.doc_get("%s/test.pdf" % testdir)

        doc.pageheader_set("This is a multi-line footer.  It goes on every page.")
        doc.pagefooter_set("TFTech Lochristi ...")

        for i in range(111):
            doc.paragraph_add("This is line %d." % i)

        doc.save()

        "This is a multi-line header.  It goes on every page.  "

    def test_simple_pdf(self):
        from reportlab.pdfgen import canvas

        def hello(c):
            c.drawString(100, 100, "Hello World")

        c = canvas.Canvas("/tmp/reportlab/hello.pdf")
        hello(c)
        c.showPage()
        c.save()

    def test_generation(self):

        p = j.tools.prefab.local
        url = "https://media.wired.com/photos/598e35994ab8482c0d6946e0/master/w_628,c_limit/phonepicutres-TA.jpg"
        p.network.tools.download(url, to="/tmp/reportlab/image.jpg", overwrite=False, retry=3)

        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.rl_config import defaultPageSize
        from reportlab.lib.units import inch

        PAGE_HEIGHT = defaultPageSize[1]
        PAGE_WIDTH = defaultPageSize[0]
        styles = getSampleStyleSheet()

        Title = "Hello world"
        pageinfo = "platypus example"

        def myFirstPage(canvas, doc):
            canvas.saveState()
            canvas.setFont("Times-Bold", 16)
            canvas.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 108, Title)
            canvas.setFont("Times-Roman", 9)
            canvas.drawString(inch, 0.75 * inch, "First Page / %s" % pageinfo)
            canvas.restoreState()

        dr = self._getdrawing()

        j.shell()
