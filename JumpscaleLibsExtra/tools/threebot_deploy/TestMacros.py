def load_wiki(**kwargs):
    wiki = j.tools.markdowndocs.load(url=kwargs["url"], name=kwargs["repo"])
    wiki.write()
