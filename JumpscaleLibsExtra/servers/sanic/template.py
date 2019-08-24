from string import Template


def render_posts():
    return """
        <html>
            <head>
                <style>
                    body {
                      font-family: sans-serif;
                      margin: 0;
                      background: #f0f0f0;
                    }
                
                    #app {
                      padding: 24px;
                      max-width: 400px;
                      margin: auto;
                    }
                    
                    h1 {
                      text-align: center;
                      font-weight: normal;
                    }
                    
                    article {
                      background: white;
                      margin-bottom: 12px;
                      padding: 12px;
                      border-radius: 2px;
                    }
                    
                    .loading {
                      text-align: center;
                      color: #777;
                    }
                    
                    .title {
                      text-transform: uppercase;
                    }
                    
                    .author {
                      color: #777;
                    }
                </style>
                
                
            </head>
        <body>
        <!-- App -->
            <div id="app">
              <h1>Blog</h1>

            <form method="POST">

              id: <input id="id" name="id" type="text"/><br/>
              name: <input id="name" name="name" type="text"/><br/>
              title: <input id="title" name="title" type="text"/><br/>
              author: <input id="author" name="author" type="text"/><br/>

              <input type="submit" value="go" id="submit">
            </form>


              <div>
                <div v-if="loading" class="loading">Loading...</div>
                <article v-for="post of posts">
                  <div class="title">{{ post.title }}</div>
                  <div class="author">By {{ post.author.name }}</div>
                </article>
              </div>
            </div>
        <script src="https://unpkg.com/vue/dist/vue.js"></script>
        <script src="https://unpkg.com/apollo-client-browser@1.9.0"></script>
        <script src="https://unpkg.com/vue-apollo@2.1.0-beta.19"></script>

        <script>
                    console.clear()
            
            const apolloClient = new Apollo.lib.ApolloClient({
              networkInterface: Apollo.lib.createNetworkInterface({
                // Edit: https://launchpad.graphql.com/nnnwvmq07
                uri: 'http://172.17.0.2:8001/graphql',
                transportBatching: true,
              }),
              connectToDevTools: true,
            })
            
            const apolloProvider = new VueApollo.ApolloProvider({
              defaultClient: apolloClient,
            })
            
            const POSTS_QUERY = Apollo.gql`
            {
              posts {
                id
                title
                author {
                  id
                  name
                }
              }
            }
            `
            
            // New VueJS instance
            const app = new Vue({
              // CSS selector of the root DOM element
              el: '#app',
              data: {
                posts: [],
                loading: 0,
              },
              // Apollo GraphQL
              apolloProvider,
              apollo: {
                posts: {
                    query: POSTS_QUERY,
                  loadingKey: 'loading',
                },
              },
            })
        </script>
        </body>
        </html>
    """


def render_counter():
    return """
        <html>
            <head>
                <style>
                    body {
                      font-family: sans-serif;
                      margin: 0;
                      background: #f0f0f0;
                    }

                    #app {
                      padding: 24px;
                      max-width: 400px;
                      margin: auto;
                    }

                    h1 {
                      text-align: center;
                      font-weight: normal;
                    }

                    article {
                      background: white;
                      margin-bottom: 12px;
                      padding: 12px;
                      border-radius: 2px;
                    }

                    .loading {
                      text-align: center;
                      color: #777;
                    }

                    .title {
                      text-transform: uppercase;
                    }

                    .author {
                      color: #777;
                    }
                </style>


            </head>
        <body>
        <!-- App -->
            <div id="app">
              <h1>Blog</h1>
              <div>
                <div v-if="loading" class="loading">Loading...</div>
                <div class="title" v-bind:counter="0">{{counter}}</div>
              </div>
            </div>
        <script src="https://unpkg.com/vue/dist/vue.js"></script>
        <script src="https://unpkg.com/apollo-client-browser@1.9.0"></script>
        <script src="https://unpkg.com/vue-apollo@2.1.0-beta.19"></script>
        <script src="//unpkg.com/subscriptions-transport-ws@0.7.0/browser/client.js"></script>
    <script src="//unpkg.com/graphiql-subscriptions-fetcher@0.0.2/browser/client.js"></script>
    
        <script>
                    console.clear()

            const networkInterface = Apollo.lib.createNetworkInterface({
                uri: 'http://172.17.0.2:8001/graphql' // Your GraphQL endpoint
            });
            
            var wsClient = new window.SubscriptionsTransportWs.SubscriptionClient(
            'ws://172.17.0.2:8001/subscriptions', {
                reconnect: true
            });
              
            const networkInterfaceWithSubscriptions = new window.SubscriptionsTransportWs.addGraphQLSubscriptions(
                networkInterface,
                wsClient
            );

            const apolloClient = new Apollo.lib.ApolloClient({
              networkInterface: networkInterfaceWithSubscriptions
            })
            

            const apolloProvider = new VueApollo.ApolloProvider({
              defaultClient: apolloClient,
            })

            // New VueJS instance
            const app = new Vue({
              // CSS selector of the root DOM element
              el: '#app',
              data: {
                counter: 0,
                loading: 0,
              },
              
            })
            
            apolloClient.subscribe({
              query: Apollo.gql`
                subscription onNewItem {
                    countSeconds
                }`,
              variables: {}
            }).subscribe({
              next (data) {
                app.counter = data;
              }
            });
        </script>
        </body>
        </html>
    """


def render_graphiql():
    return Template(
        """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>GraphiQL</title>
  <meta name="robots" content="noindex" />
  <style>
    html, body {
      height: 100%;
      margin: 0;
      overflow: hidden;
      width: 100%;
    }
  </style>
  <link href="//cdn.jsdelivr.net/graphiql/${GRAPHIQL_VERSION}/graphiql.css" rel="stylesheet" />
  <script src="//cdn.jsdelivr.net/fetch/0.9.0/fetch.min.js"></script>
  <script src="//cdn.jsdelivr.net/react/15.0.0/react.min.js"></script>
  <script src="//cdn.jsdelivr.net/react/15.0.0/react-dom.min.js"></script>
  <script src="//cdn.jsdelivr.net/graphiql/${GRAPHIQL_VERSION}/graphiql.min.js"></script>
  <script src="//unpkg.com/subscriptions-transport-ws@${SUBSCRIPTIONS_TRANSPORT_VERSION}/browser/client.js"></script>
  <script src="//unpkg.com/graphiql-subscriptions-fetcher@0.0.2/browser/client.js"></script>
</head>
<body>
  <script>
    // Collect the URL parameters
    var parameters = {};
    window.location.search.substr(1).split('&').forEach(function (entry) {
      var eq = entry.indexOf('=');
      if (eq >= 0) {
        parameters[decodeURIComponent(entry.slice(0, eq))] =
          decodeURIComponent(entry.slice(eq + 1));
      }
    });
    // Produce a Location query string from a parameter object.
    function locationQuery(params, location) {
      return (location ? location: '') + '?' + Object.keys(params).map(function (key) {
        return encodeURIComponent(key) + '=' +
          encodeURIComponent(params[key]);
      }).join('&');
    }
    // Derive a fetch URL from the current URL, sans the GraphQL parameters.
    var graphqlParamNames = {
      query: true,
      variables: true,
      operationName: true
    };
    var otherParams = {};
    for (var k in parameters) {
      if (parameters.hasOwnProperty(k) && graphqlParamNames[k] !== true) {
        otherParams[k] = parameters[k];
      }
    }
    var fetcher;
    if (true) {
      var subscriptionsClient = new window.SubscriptionsTransportWs.SubscriptionClient('${subscriptionsEndpoint}', {
        reconnect: true
      });
      fetcher = window.GraphiQLSubscriptionsFetcher.graphQLFetcher(subscriptionsClient, graphQLFetcher);
    } else {
      fetcher = graphQLFetcher;
    }
    // We don't use safe-serialize for location, because it's not client input.
    var fetchURL = locationQuery(otherParams, '${endpointURL}');
    // Defines a GraphQL fetcher using the fetch API.
    function graphQLFetcher(graphQLParams) {
        return fetch(fetchURL, {
          method: 'post',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(graphQLParams),
          credentials: 'include',
        }).then(function (response) {
          return response.text();
        }).then(function (responseBody) {
          try {
            return JSON.parse(responseBody);
          } catch (error) {
            return responseBody;
          }
        });
    }
    // When the query and variables string is edited, update the URL bar so
    // that it can be easily shared.
    function onEditQuery(newQuery) {
      parameters.query = newQuery;
      updateURL();
    }
    function onEditVariables(newVariables) {
      parameters.variables = newVariables;
      updateURL();
    }
    function onEditOperationName(newOperationName) {
      parameters.operationName = newOperationName;
      updateURL();
    }
    function updateURL() {
      history.replaceState(null, null, locationQuery(parameters) + window.location.hash);
    }
    // Render <GraphiQL /> into the body.
    ReactDOM.render(
      React.createElement(GraphiQL, {
        fetcher: fetcher,
        onEditQuery: onEditQuery,
        onEditVariables: onEditVariables,
        onEditOperationName: onEditOperationName,
      }),
      document.body
    );
  </script>
</body>
</html>"""
    ).substitute(
        GRAPHIQL_VERSION="0.10.2",
        SUBSCRIPTIONS_TRANSPORT_VERSION="0.7.0",
        subscriptionsEndpoint="ws://172.17.0.2:8001/subscriptions",
        endpointURL="/graphql",
    )
