from Jumpscale import j
from sanic import Sanic, response
from graphql_ws.websockets_lib import WsLibSubscriptionServer
from graphql.execution.executors.asyncio import AsyncioExecutor
from sanic_graphql import GraphQLView
import os, sys

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path)
from template import render_graphiql, render_posts, render_counter
from schema import schema, Query

app = Sanic(__name__)

gedis = j.clients.gedis.get("default", port=8888)
actor = gedis.actors.graphql_actor

subscription_server = WsLibSubscriptionServer(schema)


@app.listener("before_server_start")
def init_graphql(app, loop):
    """
    init graphql with gevent- create main page with the save data in bcdb
    """
    app.add_route(GraphQLView.as_view(schema=schema, executor=AsyncioExecutor(loop=loop)), "/graphql")


@app.route("/")
async def graphiql_view(request):
    """
    view the homepage with vue.js
    """
    return response.html(render_graphiql())


@app.route("/posts", methods=["GET", "POST"])
async def graphiql_view(request):
    """
    create and display simple blog using apollo and vue.js
    : GET request: view current saved objects
    : POST request: create a new object with the pre-defined schema
    """
    request_decoded = {"method": request.method, "body": request.body}
    actor.graphiql_view_posts(str(request_decoded))
    return response.html(render_posts())


@app.route("/counter", methods=["GET"])
async def graphiql_view(request):
    """
    Example for using websocket with apollo and view.js
    A simple  counter
    """
    return response.html(render_counter())


@app.websocket("/subscriptions", subprotocols=["graphql-ws"])
async def subscriptions(request, ws):
    """
    Create websocket
    """
    await subscription_server.handle(ws)
    return ws


app.run(host="0.0.0.0", port=8001)
