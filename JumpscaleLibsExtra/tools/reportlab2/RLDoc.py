from Jumpscale import j
try:
    from reportlab.lib.pagesizes import A4
except ImportError:
    j.builders.runtimes.python3.pip_package_install("reportlab")
    from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Image, Table
from .TextFlowables import H1, H2, H3, Normal
from reportlab.lib import colors
j.sal.ubuntu.apt_install_check("graphviz", "dot")


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
        self._doc.bottomMargin = 1 * cm
        self._doc.topMargin = 1 * cm
        frame = self.frame_create(
            x1=self._doc.topMargin,
            y1=self._doc.bottomMargin,
            width=self._doc.width + 2 * cm,
            height=self._doc.height + 2 * cm,
            id="default",
        )
        template = PageTemplate(id="legal_doc", frames=frame, onPage=self._default_header_footer)
        self._templates = [template]

    def header_text_set(self, text):
        self._header = text

    def footer_text_set(self, text):
        self._footer = text

    def _default_header_footer(self, canvas, doc, pagenr_auto=False):

        canvas.saveState()
        if self._header:
            P = H1(self._header).get()
            w, h = P.wrap(doc.width, doc.topMargin)
            P.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
            canvas.restoreState()
            canvas.saveState()

        if self._footer:
            P = H1(self._footer).get()
            w, h = P.wrap(doc.width - 20, doc.bottomMargin)
            P.drawOn(canvas, doc.leftMargin, h)
            canvas.restoreState()

        if pagenr_auto:
            canvas.saveState()
            P = H1("page:%s" % self._pagenr, self._styleRightAlignment)
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

    def _paragraph_add(self, text, style, **kwargs):
        self._flowables.append(Paragraph(text, style, **kwargs))

    def h1_add(self, text, custom_style=None):
        self._flowables.append(H1(text, custom_style).get())

    def h2_add(self, text, custom_style=None):
        self._flowables.append(H2(text, custom_style).get())

    def h3_add(self, text, custom_style=None):
        self._flowables.append(H3(text, custom_style).get())

    def text_add(self, text, custom_style=None):
        self._flowables.append(Normal(text, custom_style).get())

    def image_add(self, file_name, width=None, height=None, horizontal_align="CENTER"):
        self._flowables.append(Image(file_name, width, height, hAlign=horizontal_align))

    def table_create(self, data, style=None):
        if not style:
            style = [
                ("LINEABOVE", (0, 0), (-1, -1), 1, colors.black),
                ("LINEBEFORE", (0, 0), (-1, -1), 1, colors.black),
                ("LINEAFTER", (0, 0), (-1, -1), 1, colors.black),
                ("LINEBELOW", (0, 0), (-1, -1), 1, colors.black),
            ]
        self._flowables.append(Table(data, style=style))

    def graph_add(self, content):
        md5 = j.data.hash.md5_string(content)
        md5 = bytes(md5.encode()).decode()
        name = "graph_%s" % md5
        content_path = j.sal.fs.getTmpFilePath()
        dest_path = j.sal.fs.getTmpFilePath() + ".png"
        j.sal.fs.writeFile(filename=content_path, contents=content)
        j.sal.process.execute("dot '%s' -Tpng > '%s'" % (content_path, dest_path))
        j.sal.fs.remove(content_path)
        self.image_add(dest_path)

    def md_add(self, content=None):
        parts = j.data.markdown.document_get(content).parts
        for part in parts:
            if part.type == "header" and part.level == 1:
                self.h1_add(part.title)
            elif part.type == "header" and part.level == 2:
                self.h2_add(part.title)
            elif part.type == "header" and part.level == 3:
                self.h3_add(part.title)
            elif part.type == "block":
                self.text_add(part.html)
            elif part.type == "table":
                data = [part.header]
                data.extend(part.rows)
                self.table_create(data=data)
            else:
                print(f"Skipping {part.type} part, Not implemented yet")
