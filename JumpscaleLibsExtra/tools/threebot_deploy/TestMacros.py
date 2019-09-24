def load_wiki(**kwargs):
    wiki = j.tools.markdowndocs.load(kwargs["url"], name=kwargs["repo"])
    wiki.write()
