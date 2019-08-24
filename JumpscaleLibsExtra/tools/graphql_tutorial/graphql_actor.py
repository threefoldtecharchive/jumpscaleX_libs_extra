import sys, os
from Jumpscale import j
from sanic import Sanic, response

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path)
from schema import schema, Query

JSBASE = j.baseclasses.object


class graphql_actor(JSBASE):

    _SCHEMA_TEXT = """
        @url = graphql.info.schema
        info_id* = (I)
        title = (S) 
        author = (S)
        name = (S)
        """

    def graphiql_view(self, request):
        print("actor was invoked")
        # TODO: return dynamic data
        # retrun "rednder_graphiql"
        return "render_graphiql"

    def graphiql_view_posts(self, request):
        print("actor was invoked")
        model_objects = None
        request_encoded = eval(request.decode("utf-8"))
        if request_encoded["method"] == "POST":
            data = self.parse_data(request_encoded["body"].decode("utf-8"))
            # Create a model with the data and save the model for later retrieval
            model = j.application.bcdb_system.model_get(schema=self._SCHEMA_TEXT)
            model_objects = model.new()
            model_objects.info_id = data["id"]
            model_objects.title = data["title"]
            model_objects.name = data["name"]
            model_objects.author = data["author"]
            model_objects.save()

    def graphiql_view_counter(self):
        print("actor was invoked")
        # return render couneter
        return "render_counter"

    def parse_data(self, raw_data):
        out_data = {}
        temp = raw_data.split("&")
        for item in temp:
            info = item.split("=")
            out_data[info[0]] = info[1]
        return out_data
