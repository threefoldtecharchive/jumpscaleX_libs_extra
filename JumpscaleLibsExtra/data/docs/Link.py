from Jumpscale import j
import toml

import copy

JSBASE = j.baseclasses.object


class Link(JSBASE):
    def __init__(self, doc, source):
        JSBASE.__init__(self)
        self.docsite = doc.docsite
        self.doc = doc
        self.extension = ""
        self.source = source  # original text of the link
        self.cat = ""  # category in image,doc,link,officedoc, imagelink  #doc is markdown
        self.link_source = ""  # text to replace when rewrite is needed
        self.link_source_original = ""  # original link
        self.error_msg = ""
        self.filename = ""
        self.filepath = ""
        self.link_descr = ""  # whats inside the []
        self.link_to_doc = None
        self._process()

    def _clean(self, name):
        return j.core.text.strip_to_ascii_dense(name)

    def error(self, msg):
        self.error_msg = msg
        msg = "**ERROR:** problem with link:%s\n%s" % (self.source, msg)
        # self._log_error(msg)
        self.docsite.error_raise(msg, doc=self.doc)
        self.doc._content = self.doc._content.replace(self.source, msg)
        return msg

    def _process(self):
        self.link_source = self.source.split("(", 1)[1].split(")", 1)[0]  # find inside ()
        self.link_descr = self.source.split("[", 1)[1].split("]", 1)[0]  # find inside []

        if self.link_source.strip() == "":
            return self.error("link is empty, but url is:%s" % self.source)

        if "@" in self.link_descr:
            self.link_source_original = self.link_descr.split("@")[1].strip()  # was link to original source
            self.link_descr = self.link_descr.split("@")[0].strip()

        if "?" in self.link_source:
            lsource = self.link_source.split("?", 1)[0]
        else:
            lsource = self.link_source
        self.extension = j.sal.fs.getFileExtension(lsource)

        if "http" in self.link_source:
            self.link_source_original = self.link_source
            if self.source.startswith("!"):
                if not self.extension in ["png", "jpg", "jpeg", "mov", "mp4"]:
                    self.extension = (
                        "jpeg"
                    )  # to support url's like https://images.unsplash.com/photo-1533157961145-8cb586c448e1?ixlib=rb-0.3.5&ixid=eyJhcHBfaWQiOjEyMDd9&s=4e252bcd55caa8958985866ad15ec954&auto=format&fit=crop&w=1534&q=80
            else:
                # check link exists
                self.cat = "link"
                if self.docsite.links_verify:
                    self.link_verify()

        else:
            if self.link_source.strip() == "/":
                self.link_source = ""
                return
            if "#" in self.link_source:
                self.link_source = ""
                return

            if "?" in self.link_source:
                self.link_source = self.link_source.split("?", 1)[0]

            if self.link_source.find("/") != -1:
                name = self.link_source.split("/")[-1]
            else:
                name = self.link_source

            self.filename = self._clean(name)  # cleanly normalized name but extension still part of it
            # e.g. balance_inspiration_motivation_life_scene_wander_big.jpg
            if self.filename.strip() == "":
                return self.error("filename is empty")

            # only possible for images (video, image)
            if self.source.startswith("!"):
                self.cat = "image"
                if not self.extension in ["png", "jpg", "jpeg", "mov", "mp4"]:
                    return self.error("found unsupported image file: extension:%s" % self.extension)

            if self.cat == "":
                if self.extension in ["png", "jpg", "jpeg", "mov", "mp4"]:
                    self.cat = "imagelink"
                elif self.extension in ["doc", "docx", "pdf", "xls", "xlsx", "pdf"]:
                    self.cat = "officedoc"
                elif self.extension in ["md", "", None]:
                    self.cat = "doc"  # link to a markdown document
                    try:
                        self.link_to_doc = self.docsite.doc_get(self.link_source, die=True)
                    except Exception as e:
                        if "Cannot find doc" in str(e):
                            return self.error(str(e))
                        raise e
                    return
                else:
                    return self.error("found unsupported extension")

            self.filepath = self.doc.docsite.file_get(self.filename, die=False)
            if self.filepath is None and self.source.startswith("!"):
                # is image try re-download
                self.download()

    @property
    def markdown(self):
        """
        markdown format for the link
        :return:
        """
        if self.source.startswith("!"):
            c = "!"
            if self.link_source_original is not "":
                descr = "%s@%s" % (self.link_descr, self.link_source_original)
            else:
                descr = self.link_descr
        else:
            c = ""
            descr = self.link_descr
        c += "[%s](%s)" % (descr, self.link_source)
        return c

    def download(self):
        def do():
            self._log_info("image download")
            if self.link_verify():
                link_descr = self._clean(self.link_descr)
                name = ""
                if len(link_descr) > 0:
                    name = link_descr
                if name == "":
                    name, dest = self.doc._get_file_path_new(extension=self.extension)
                else:
                    dest = "%s/%s.%s" % (self.doc.path_dir, name, self.extension)

                self.link_source = "%s.%s" % (name, self.extension)  # will be replaced with this name

                self._log_info("download:%s\n%s" % (self.link_source_original, dest))
                try:
                    j.clients.http.download(self.link_source_original, dest)
                except Exception as e:
                    if "404" in str(e) or "400" in str(e):
                        return self.error("could not find file to download:%s" % self.link_source_original)
                    # raise e
                    print("error in download in link")
                    from IPython import embed

                    embed(colors="Linux")
                    k
                self.replace_in_doc()
                self._log_info("download done")
            return "OK"

        self._cache.get("download:%s" % self.link_source_original, method=do, expire=600)

    def link_verify(self):
        def do():
            if "verification" in self.docsite.config:
                for item in self.docsite.config["verification"]:
                    if "ignore" in item:
                        if self.link_source_original.find(item["ignore"]) != -1:
                            return True
                    if "error" in item:
                        if self.link_source_original.find(item["error"]) != -1:
                            self.error("link in error state:%s" % self.link_source_original)
                            return False

            self._log_info("check link exists:%s" % self.link_source)
            if not j.clients.http.ping(self.link_source_original):
                self.error("link not alive:%s" % self.link_source_original)
                return False
            return True

        res = self._cache.get(self.link_source, method=do, expire=3600)
        if res is not True:
            self.error(res)
            return False

    def replace_in_doc(self):
        self._log_info("replace_in_doc")
        self.doc._content = self.doc._content.replace(self.source, self.markdown)
        self.source = self.markdown  # there is a new source now
        print(678)
        from IPython import embed

        embed(colors="Linux")
        s
        # j.sal.fs.writeFile(self.doc.path,self.doc._content)
        self._process()

    def __repr__(self):
        if self.cat == "link":
            return "link:%s:%s" % (self.cat, self.link_source)
        else:
            return "link:%s:%s" % (self.cat, self.filename)

    __str__ = __repr__
