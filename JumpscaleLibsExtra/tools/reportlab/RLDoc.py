from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph
from Jumpscale import j


class RLDoc:
    def __init__(self, path):

        self.path = path

        styles = getSampleStyleSheet()
        styles2 = getSampleStyleSheet()
        self._styleN = styles["Normal"]
        self._styleH1 = styles["Heading1"]
        self._styleH2 = styles["Heading2"]
        self._styleRightAlignment = styles2["Normal"]  # to make sure we don't overwrite the normal styles (IS HACK)
        self._styleRightAlignment.alignment = 2
        self._header = ""
        self._footer = ""
        self._pagenr = 0

        self.doc = BaseDocTemplate(self.path, pagesize=A4)
        self.doc.leftMargin = 1 * cm
        self.doc.rightMargin = 1 * cm
        self.doc.bottomMargin = 1.5 * cm
        self.doc.topMargin = 1.5 * cm
        frame = Frame(self.doc.leftMargin, self.doc.bottomMargin, self.doc.width, self.doc.height - 2 * cm, id="normal")
        template = PageTemplate(id="legal_doc", frames=frame, onPage=self._header_footer)
        self.doc.addPageTemplates([template])

        self.parts = []

    def save(self):
        self.doc.build(self.parts)

    def _header_footer(self, canvas, doc, pagenr_auto=True):
        self._pagenr += 1

        canvas.saveState()
        header = self._header.replace("{pagenr}", str(self._pagenr))
        P = Paragraph(header, self._styleN)
        w, h = P.wrap(doc.width, doc.topMargin)
        P.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
        canvas.restoreState()

        canvas.saveState()
        footer = self._footer.replace("{pagenr}", str(self._pagenr))
        P = Paragraph(footer, self._styleN)
        w, h = P.wrap(doc.width - 20, doc.bottomMargin)
        P.drawOn(canvas, doc.leftMargin, h)
        canvas.restoreState()

        if pagenr_auto:
            canvas.saveState()
            P = Paragraph("page:%s" % self._pagenr, self._styleRightAlignment)
            w, h = P.wrap(doc.width - doc.rightMargin, doc.bottomMargin)
            P.drawOn(canvas, doc.leftMargin, h)
            canvas.restoreState()

    def pageheader_set(self, txt):
        """

        :param txt: text in format
        :return:
        """
        self._header = txt

    def pagefooter_set(self, txt):
        """

        :param txt: text in format
        :return:
        """
        self._footer = txt

    def table_add(self, md_part):
        """
        returns table which needs to be manipulated
        """
        j.shell()
        self.parts.append(t)
        return t

    def header_add(self, md_part):
        """
        """
        j.shell()
        self.parts.append(MDHeader(level, title))

    def listpart_add(self, level, text):
        """
        """
        self.parts.append(MDListpart(level, text))

    def comment_add(self, md_part):
        """
        """
        j.shell()
        self.parts.append(MDComment(text))

    def comment1line_add(self, md_part):
        """
        """
        self.parts.append(MDComment1Line(text))

    def paragraph_add(self, txt):
        """
        """
        self.parts.append(Paragraph(txt, self._styleN))

    def code_add(self, md_part):
        """
        """
        j.shell()

    def data_add(self, md_part):
        j.shell()

    def codeblock_add(self, md_part):
        """
        add markdown part
        """
        j.shell()
