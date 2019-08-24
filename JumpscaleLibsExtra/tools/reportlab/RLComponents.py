from Jumpscale import j
from . import mistune
import re


class RLBase:
    @property
    def markdown(self):
        return str(self.text)

    @property
    def html(self):
        return mistune.markdown(self.text, escape=True, hard_wrap=True)

    def __repr__(self):
        return "%s:\n%s" % (self.type, self.text)

    __str__ = __repr__


class RLList(RLBase):
    def __init__(self, text):
        self.text = text
        self.type = "list"

    @property
    def as_list(self):
        return lines2list(self.text)

    @property
    def markdown(self):
        return self.text


class RLTable(RLBase):
    def __init__(self):
        self.header = []
        self.rows = []
        self.type = "table"

    def rows_as_objects(self):
        nrcols = len(self.header)
        res = []
        for row in self.rows:
            oo = object()
            for x in range(nrcols):
                val = row[x]
                if val.strip() == ".":
                    val = ""
                else:
                    try:
                        val = int(val)
                    except:
                        pass
                key = self.header[x]
                oo.__dict__[key] = val
            res.append(oo)
        return res

    def header_add(self, cols):
        """
        cols = columns can be comma separated string or can be list
        """
        if j.data.types.string.check(cols):
            cols = [item.strip().strip("'").strip('"').strip() for item in cols.split(",")]

        self.header = cols
        for nr in range(len(self.header)):
            if self.header[nr] is None or self.header[nr].strip() == "":
                self.header[nr] = " . "

    def row_add(self, cols):
        """
        cols = columns  can be comma separated string or can be list
        """
        if j.data.types.string.check(cols):
            cols = [item.strip().strip("'").strip('"').strip() for item in cols.split(",")]
        while len(cols) < len(self.header):
            cols.append("  ")
        if len(cols) != len(self.header):
            raise j.exceptions.Input(
                "cols need to be same size as header.\n %s vs %s\nline:%s\n" % (len(cols), len(self.header), cols)
            )

        for nr in range(len(cols)):
            if cols[nr] is None or str(cols[nr]).strip() == "":
                cols[nr] = " . "
        self.rows.append(cols)

    def _findSizes(self):
        m = [0 for item in self.header]
        x = 0
        for col in self.header:
            if len(col) > m[x]:
                m[x] = len(col)
            x += 1
        for row in self.rows:
            x = 0
            for col in row:
                col = str(col)
                if len(col) > m[x]:
                    m[x] = len(col)
                    if m[x] < 3:
                        m[x] = 3
                x += 1
        return m

    @property
    def text(self):
        return str(self.markdown)

    @property
    def markdown(self):
        def pad(text, l, add=" "):
            if l < 4:
                l = 4
            text = str(text)
            while len(text) < l:
                text += add
            return text

        pre = ""
        m = self._findSizes()

        # HEADER
        x = 0
        out = "|"
        for col in self.header:
            col = pad(col, m[x])
            out += "%s|" % col
            x += 1
        out += "\n"

        # INTERMEDIATE
        x = 0
        out += "|"
        for col in self.header:
            col = pad("", m[x], "-")
            out += "%s|" % col
            x += 1
        out += "\n"

        for row in self.rows:
            x = 0
            out += "|"
            for col in row:
                col = pad(col, m[x])
                out += "%s|" % col
                x += 1
            out += "\n"

        out += "\n"
        return out


class RLHeader(RLBase):
    def __init__(self, level, title):
        self.level = level
        self.title = title
        self.type = "header"

    @property
    def markdown(self):
        pre = ""
        for i in range(self.level):
            pre += "#"
        return "%s %s" % (pre, self.title)

    @property
    def text(self):
        return self.markdown


# class RLListItem(RLBase):

#     def __init__(self, level, text):
#         self.level = level
#         self.text = text
#         self.type = "list"


#     def __repr__(self):
#         pre = ''
#         if self.level > 1:
#             pre = '    ' * (self.level - 1)
#         return "%s%s" % (pre, self.text)

#     __str__ = __repr__


class RLComment(RLBase):
    def __init__(self, text):
        self.text = text
        self.type = "comment"

    def markdown(self):
        out = "<!--\n%s\n-->\n" % self.text


class RLComment1Line(RLBase):
    def __init__(self, text):
        self.text = text
        self.type = "comment1line"

    @property
    def markdown(self):
        out = "<!--%s-->\n" % self.text
        return out


# def _transform_links(self, text):
#     # replace links.
#     # Anything that isn't a square closing bracket
#     name_regex = "[^]]+"
#     # http:// or https:// followed by anything but a closing paren
#     url_regex = "http[s]?://[^)]+"

#     markup_regex = '\[({0})]\(\s*({1})\s*\)'.format(name_regex, url_regex)

#     return re.sub(markup_regex, r'<a href="\2">\1</a>', text)


class RLBlock(RLBase):
    def __init__(self, text):
        self.text = text
        self.type = "block"

    @property
    def html(self):
        return mistune.markdown(self.text, escape=True, hard_wrap=True)

    @property
    def markdown(self):
        out = self.text
        if len(out) > 0:
            if out[-1] != "\n":
                out += "\n"
            if out[-2] != "\n":
                out += "\n"
        return out


class RLCodeMacroDataBase(RLBase):
    @property
    def html(self):
        return "<code>\n\n%s\n</code>\n\n" % self.text


class RLCode(RLCodeMacroDataBase):
    def __init__(self, text, lang):
        self.text = text
        self.type = "code"
        self.lang = lang
        self.method = ""

    @property
    def markdown(self):
        out = "```%s\n" % self.lang
        out += self.text.strip()
        out += "\n```\n"
        return out


class RLMacro(RLCodeMacroDataBase):
    def __init__(self, data="", lang="", method=""):
        self.data = data
        self.lang = lang
        self.type = "macro"
        self.method = method.strip()
        self.result = ""

    @property
    def _markdown(self):
        out = "```%s\n!!!%s\n" % (self.lang, self.method)
        t = self.data.strip()
        out += t
        if t:
            out += "\n"
        out += "```\n"
        return out

    @property
    def markdown(self):
        if self.result:
            return self.result
        else:
            return self._markdown

    @property
    def text(self):
        return str(self.markdown)


class RLData(RLCodeMacroDataBase):
    def __init__(self, ddict={}, toml="", yaml=""):

        self.type = "data"

        self._toml = toml
        self._yaml = yaml
        self._ddict = ddict

        self._hash = ""

    @property
    def datahr(self):
        return j.data.serializers.toml.dumps(self.ddict)

    @property
    def toml(self):
        if self._toml:
            return self._toml
        else:
            return j.data.serializers.toml.dumps(self.ddict)

    @property
    def ddict(self):
        if self._toml:
            return j.data.serializers.toml.loads(self._toml)
        elif self._yaml:
            return j.data.serializers.yaml.loads(self._yaml)
        elif self._ddict is not {}:
            return self._ddict
        else:
            RuntimeError("toml or ddict needs to be filled in in data object")

    @property
    def text(self):
        out = "```toml\n!!!data\n%s\n```\n" % self.toml  # need new header
        return out

    @property
    def hash(self):
        if self._hash == "":
            json = j.data.serializers.json.dumps(self.ddict, True, True)
            self._hash = j.data.hash.md5_string(json)
        return self._hash

    @property
    def markdown(self):
        # out = "```toml\n!!!data\n"
        # out += self.text.strip()
        # out += "\n```\n"
        return self.text


class RLImage(RLCodeMacroDataBase):
    def __init__(self, name, path):
        self.path = path
        self.name = name
        self.type = "image"
        self.extension = j.sal.fs.getFileExtension(path)

    @property
    def markdown(self):
        return "![](%s)" % self.name

    @property
    def text(self):
        return str(self.markdown)


# class Object(RLBase):
#     def __init__(self):
#         pass


#     def __str__(self):
#         out=""
#         for key,val in self.__dict__.items():
#             out+="%s:%s "%(key,val)
#         out=out.strip()
#         return out

#     __repr__ = __str__
