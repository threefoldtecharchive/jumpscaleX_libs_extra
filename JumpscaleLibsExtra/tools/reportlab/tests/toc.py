from Jumpscale import j

j.sal.fs.createDir("/tmp/reportlab")

from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.platypus import PageBreak
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.frames import Frame
from reportlab.lib.units import cm


class MyDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        self.allowSplitting = 0
        BaseDocTemplate.__init__(self, filename=filename, **kw)
        template = PageTemplate("normal", [Frame(1.5 * cm, 1.5 * cm, 18.5 * cm, 26 * cm, id="F1")])
        self.addPageTemplates(template)

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            txt = flowable.getPlainText()
            style = flowable.style.name
            if style == "Heading1":
                key = "h1-%s" % self.seq.nextf("heading1")
                self.canv.bookmarkPage(key)
                self.notify("TOCEntry", (0, txt, self.page, key))
            elif style == "Heading2":
                # ...
                key = "h2-%s" % self.seq.nextf("heading2")
                self.canv.bookmarkPage(key)
                self.notify("TOCEntry", (1, txt, self.page, key))


centered = PS(name="centered", fontSize=12, leading=14, alignment=1, spaceAfter=5)

h1 = PS(name="Heading1", fontSize=14, leading=16)


h2 = PS(name="Heading2", fontSize=12, leading=14)

normal = PS(name="normal", fontSize=12, leading=14)

story = []

toc = TableOfContents()
toc.levelStyles = [
    PS(
        fontName="Times-Bold",
        fontSize=10,
        name="TOCHeading1",
        leftIndent=10,
        firstLineIndent=-10,
        spaceBefore=5,
        leading=10,
    ),
    PS(fontSize=10, name="TOCHeading2", leftIndent=10, firstLineIndent=-5, spaceBefore=0, leading=10),
]
story.append(toc)

story.append(Paragraph("<b>Table of contents</b>", centered))
story.append(PageBreak())
C = """

<b>You are hereby charged</b>
<a name="MYANCHOR2"/><font color="green">here</font>
"""
story.append(Paragraph(C, PS("body")))
story.append(PageBreak())
story.append(Paragraph("First heading", h1))
story.append(Paragraph("Text in first heading", PS("body")))
story.append(Paragraph("First sub heading", h2))
story.append(Paragraph("Text in first sub heading", PS("body")))
story.append(PageBreak())
story.append(Paragraph("Second sub heading", h2))
story.append(Paragraph("Text in second sub heading", PS("body")))
story.append(PageBreak())
story.append(Paragraph("Last heading", h1))
C = """

<b>You are hereby charged</b>
<br/>
<br/>
that on the 28th day of May,1970, you did willfully, unlawfully,
and <i>with malice of forethought</i>, publish an alleged
English-Hungarian phrase book with intent to cause a
breach of the peace. <u>How do you plead</u>?
<br/>
<br/>
<br/>
You are hereby charged that on the 28th day of May, 1970, you did willfully,
unlawfully, and with malice of forethought, publish an alleged English-Hungarian
phrase book with intent to cause a breach of the peace. How do you plead?
Figure 6-6: Simple bold and italic tags
User Guide Chapter 6 Paragraphs 
Page 78
This <a href="#MYANCHOR" color="blue">is a link to</a> an anchor tag ie <a name="MYANCHOR"/><font color="green">here</font>. 
This <link href="#MYANCHOR2" color="blue" fontName="Helvetica">is another link to</link> the same anchor tag.
"""
story.append(Paragraph(C, PS("body")))


def getdrawing():
    from reportlab.graphics.shapes import Drawing
    from reportlab.lib import colors
    from reportlab.graphics.charts.barcharts import VerticalBarChart

    drawing = Drawing(400, 200)
    data = [(13, 5, 20, 22, 37, 45, 19, 4), (14, 6, 21, 23, 38, 46, 20, 5)]
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 50
    bc.height = 125
    bc.width = 300
    bc.data = data
    bc.strokeColor = colors.black
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 50
    bc.valueAxis.valueStep = 10
    bc.categoryAxis.labels.boxAnchor = "ne"
    bc.categoryAxis.labels.dx = 8
    bc.categoryAxis.labels.dy = -2
    bc.categoryAxis.labels.angle = 30
    bc.categoryAxis.categoryNames = ["Jan-99", "Feb-99", "Mar-99", "Apr-99", "May-99", "Jun-99", "Jul-99", "Aug-99"]
    drawing.add(bc)
    return drawing


story.append(getdrawing())

doc = MyDocTemplate("/tmp/reportlab/mintoc.pdf")
doc.multiBuild(story)
