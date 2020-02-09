# Tarantool framewrok

This tool allow to generate some lua model based on capnp schema.
The lua model are composed of some stored procedure directly loaded into tarantool.
Then on top of that we have some python class that also get generated and calls the stored procedure in tarantool.

## How to generate lua models from capnp
To generate the lua and python code, you need to have a folder that will contains all the generated files. In our filesystem we create a structure like this:
```
-  models
 | - user
```
So a folder calleds `models` and another folder called `user`

Then, you need to define your capnp schema. In our example we'll use the following example schema:

```capnp
@0xbc08a7d76708ae85;

struct User {
  region @0   :UInt16;
  id @1       :UInt32;
  epoch @2    :UInt32;
  pubkey @3   :Data;
  sign @5     :Data;
  link @6     :UInt32;
  name @7     :Text;
  description @8 :Text;
}
```
Save this schema in `models/user/model.capnp`

Once this is done, you can now generate the lua and python code. Before we generate the models we need to have a running instance of tarantool. To start an instance of tarantool do the following:
- configure the tarantool client:
```python
j.clients.tarantool.client_configure(name='example', ipaddr='localhost', port=3301, login='root', password='superscret')
```
With this command you create a configuration for a tarantool instance called `example` that will listent on `localhost:3301` and that has an admin user called `root` with `supersecret` as password

- start the tarantool instance:
```python
j.clients.tarantool.server_start(name='example', port=3301)
```
This command will start a tarantool instance called `example` that listent on `localhost:3301` in a tmux window.

Now you have a running tarantool instance. You can now generate the lua and python models.
```python
# instanciate a client for the example instance
cl = j.clients.tarantool.client_get('example')
# generate the code for the models
# path='models' need to point to the folder created previously that contains the user folder and the model.capnp file
cl.addModels(path='models')
```
As a result, there will be some new file created, you models folder should now look like
```
-  models
 | - user
    | - __init__.py
    | - model.capnp
    | - model.lua
    | - UserCollection.py
```
- *model.lua* : contains all the stored procedure. As you will see by inspecting the file. The generated lua code is organize as a module. All the methods are defined as local, then we pack all the public method in a table and return this table.

- *UserCollection.py* : contains all the python code that wrap the calls to the lua stored procedure.

In your client, you also now have access to the newly created models. Here is a small example script that create a new user object, save it and then retreive it back
```python
user1 = cl.models.UserCollection.new()
user1.dbobj.name = "john"
user1.dbobj.description = "this is some description %s" % i
user1.dbobj.region = 10
user1.dbobj.epoch = j.data.time.getTimeEpoch()
user1.save()

user2 = tt.models.UserCollection.get(key=user1.key)
assert user1.dbobj.name == user2.dbobj.name
assert user1.dbobj.description == user2.dbobj.description
assert user1.dbobj.region == user2.dbobj.region
assert user1.dbobj.epoch == user2.dbobj.epoch
```
