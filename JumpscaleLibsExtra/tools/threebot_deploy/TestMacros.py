def load_wiki(name, url):
    wiki = j.tools.markdowndocs.load(path=url, name=name)
    wiki.write()
