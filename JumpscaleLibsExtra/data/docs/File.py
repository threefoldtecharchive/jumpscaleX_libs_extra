from Jumpscale import j


class File(j.baseclasses.object_config):
    """
    eg. a picture, html doc, ...
    """

    _SCHEMATEXT = """
        @url = jumpscale.docs.docsite.1
        name* = ""
        path = ""        
        state* = "image,html,css" (E)
        extension* = ""        

        """

    def _init(self, **kwargs):
        pass
