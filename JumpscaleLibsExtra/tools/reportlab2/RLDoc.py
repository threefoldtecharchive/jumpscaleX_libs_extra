from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph
from Jumpscale import j


class RLDoc:
    def __init__(self, filename, **kwargs):
        self._doc = BaseDocTemplate(filename=filename, **kwargs)
        self._templates = []
        self._frames = {}
        self._flowables = []
        self._header = None
        self._footer = None

    def template_add(self, template):
        self._templates.append(template)

    def frame_create(
        self,
        x1,
        y1,
        width,
        height,
        leftPadding=6,
        bottomPadding=6,
        rightPadding=6,
        topPadding=6,
        id=None,
        showBoundary=0,
        overlapAttachedSpace=None,
        _debug=None,
    ):
        self._frames[id] = Frame(
            x1,
            y1,
            width,
            height,
            leftPadding=leftPadding,
            bottomPadding=bottomPadding,
            rightPadding=rightPadding,
            topPadding=topPadding,
            id=id,
            showBoundary=showBoundary,
            overlapAttachedSpace=overlapAttachedSpace,
            _debug=_debug,
        )
        return self._frames[id]

    def default_set(self):
        """
        sets default margins and frames
        :return: None
        """
        self._doc.leftMargin = 1 * cm
        self._doc.rightMargin = 1 * cm
        self._doc.bottomMargin = 1.5 * cm
        self._doc.topMargin = 1.5 * cm
        frame = self.frame_create(
            self.doc.topMargin, self.doc.bottomMargin, self.doc.width, self.doc.height - 2 * cm, id="default"
        )
        template = PageTemplate(id="legal_doc", frames=frame, onPage=self._header_footer)
        self._templates = [template]

    def set_header_text(self, text):
        self._header = text

    def set_header_text(self, text):
        self._footer = text

    def _default_header_footer(self, canvas, doc, pagenr_auto=True):
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

    def configure(self):
        """
        configures the doc
        """
        self._doc.addPageTemplates(self._templates)

    def save(self):
        self._doc.build(self._flowables)

    def paragraph_add(self, text, style, **kwargs):
        self._flowables.append(Paragraph(text, style, **kwargs))

    ## TODO: add methods to configure self._doc eg. margin_set, ...
