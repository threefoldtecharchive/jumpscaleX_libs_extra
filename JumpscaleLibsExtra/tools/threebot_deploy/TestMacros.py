def load_wiki(**kwargs):
    wiki = j.tools.markdowndocs.load(path=kwargs["url"], name=kwargs["repo"])
    wiki.write()
