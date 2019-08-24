# Graphql Websockets

In this project, `Sanic` is used


# Running Server

- install requirements `pip install -r requirements.txt`
- python3 app.py `Runs server on localhost:8000`

# Testing


## graphiql http://127.0.0.1:8000/graphiql

- query
  
        ```
            query{
              posts {
                id
                title
                author {
                  id
                  name
                }
              }
            }
        ```
        
- Result

     ```
       {
          "data": {
            "posts": [
              {
                "id": 1,
                "title": "one",
                "author": {
                  "id": 1,
                  "name": "Hamdy"
                }
              },
              {
                "id": 2,
                "title": "two",
                "author": {
                  "id": 2,
                  "name": "Aly"
                }
              }
            ]
          }
        }
     ```
- Subscription (Realtime / websockets)
    ```
    subscription{
      countSeconds
    }
    ```       
 - Result (counter that increases)
     ```
     {
      "countSeconds": 36
    }
     ```

## Normal Integration with Apollo client & Vue.js http://127.0.0.1:8000/posts

In this page, a normal `graphql` query is issued using apollo client, getting
posts and displaying them

## Websockets, Apollo client & Vue.js (live update) http://127.0.0.1:8000/counter

In this page, a subscription to an increasing counter is issued to server 
using apollo client and websockets and you can see counter 
increaing 



