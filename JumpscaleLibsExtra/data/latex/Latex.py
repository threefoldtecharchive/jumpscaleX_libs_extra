from Jumpscale import j

JSBASE = j.baseclasses.object
from pylatex import *
from pylatex.utils import bold

skip = j.baseclasses.testtools._skip


class Latex(j.baseclasses.object):
    __jslocation__ = "j.data.latex"

    def install(self):
        p = j.tools.prefab.local
        if p.platformtype.platform_is_osx:
            self._log_info("will install mactex, is huge, will have to wait long")
            cmd = "brew cask install mactex"
            p.core.run(cmd)
        else:
            "latexmk"
            raise NotImplemented("need to do for ubuntu")

        p.runtimes.pip.install("pylatex,numpy")

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/67")
    def test_generation(self, install=False):
        """
        kosmos 'j.data.latex.test_generation(install=False)'

        make sure you do
        ```
        export PATH=/usr/local/texlive/2018/bin/x86_64-darwin/:$PATH
        ```
        """
        if install:
            self.install()

        p = j.tools.prefab.local

        from pylatex.utils import italic

        geometry_options = {"tmargin": "2cm", "lmargin": "1cm", "rmargin": "1cm", "bmargin": "2cm"}
        doc = Document(geometry_options=geometry_options, fontenc="T1", lmodern=True, textcomp=True)

        header = PageStyle("header")
        # Create left header
        with header.create(Head("L")):
            header.append("Page date: ")
            header.append(LineBreak())
            header.append("R3")
        # Create center header
        with header.create(Head("C")):
            header.append("Company")
        # Create right header
        with header.create(Head("R")):
            header.append(simple_page_number())
        # Create left footer
        with header.create(Foot("L")):
            header.append("Left Footer")
        # Create center footer
        with header.create(Foot("C")):
            header.append("Center Footer")
        # Create right footer
        with header.create(Foot("R")):
            header.append("Right Footer")

        doc.preamble.append(header)
        doc.change_document_style("header")

        # Add Heading
        with doc.create(MiniPage(align="c")):
            doc.append(LargeText(bold("Title")))
            doc.append(LineBreak())
            doc.append(MediumText(bold("As at:")))

        with doc.create(Section("The simple stuff")):
            doc.append("Some regular text and some ")
            doc.append(italic("italic text. "))
            doc.append("\nAlso some crazy characters: $&#{}")
            with doc.create(Subsection("Math that is incorrect")):
                # j.shell()
                doc.append(Math(data=["2*3", "=", 9]))

        with doc.create(Subsection("Table of something")):
            with doc.create(Tabular("rc|cl")) as table:
                table.add_hline()
                table.add_row((1, 2, 3, 4))
                table.add_hline(1, 2)
                table.add_empty_row()
                table.add_row((4, 5, 6, 7))

        url = "https://media.wired.com/photos/598e35994ab8482c0d6946e0/master/w_628,c_limit/phonepicutres-TA.jpg"
        p.network.tools.download(url, to="/tmp/latex/image.jpg", overwrite=False, retry=3)

        with doc.create(Subsection("An image")):
            with doc.create(Figure(position="h!")) as kitten_pic:
                kitten_pic.add_image("/tmp/latex/image.jpg", width="300px")
                kitten_pic.add_caption("Look it's on its back")

        markers = []
        for i in range(20):
            marker = Marker("mylabel_%s" % i)
            markers.append(marker)
            label = Label(marker)

            with doc.create(Section("this is my section", label=label)):
                doc.append("Some text.\n")
                doc.append("This is another paragraph.\n")
                C = """
                Sometimes the compiler will not be able to complete the document in one pass.
                In this case it will instruct you to “Rerun LaTeX” via the log output
                In order to deal with this, you need to make sure that latexmk is installed.
                Pylatex will detect and use it automatically.

                In this case it will instruct you to “Rerun LaTeX” via the log output
                In order to deal with this, you need to make sure that latexmk is installed.
                Pylatex will detect and use it automatically.

                In this case it will instruct you to “Rerun LaTeX” via the log output
                In order to deal with this, you need to make sure that latexmk is installed.
                Pylatex will detect and use it automatically.


                """
                doc.append(LineBreak())
                doc.append(j.core.text.strip(C))
                doc.append("Some text.")

        doc.append(Command("newpage"))
        with doc.create(Section("this is my section 2")):
            doc.append(Hyperref(markers[0], "mylabel_text"))
            doc.append(LineBreak())
            doc.append(Ref(markers[0]))
            doc.append(LineBreak())
            doc.append("Some text.")

        # with doc.create(Section("table of contents")):
        doc.append(Command("tableofcontents"))

        doc.generate_pdf("/tmp/latex/full", clean_tex=False)
