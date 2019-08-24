## Python client


#### Initialize

```python
from client import HumhubClient

client = HumhubClient(base_url='http://172.17.0.2', api_key='Riv5bNRAMEGJ4TR3s0GutEj7')
users = client.users
posts = client.posts
likes = client.likes
wikis = client.wikis
comments = client.comments
spaces = client.spaces


```


### User manipulation

```python

users.list() # List all users
users.list(query='username-email-or-tag') # search users by username, email or tag
users.get(user_id=1)
users.delete(user_id=1)
client.countries # List all supported countries (used when creating/updating user)
users.create(username='Required-field', email='Required-field', firstname='Required-field', lastname='Required-field', title=None, ..)
users.update(user_id=1, email='new-email', city='new-city', ..)
```

### Post manipulation
```python
posts.list()
posts.list(space_id=1) # filter posts in certain namespace
posts.get(post_id=1)
posts.delete(post_id=1)
posts.create(space_id=2, message='Required-field')
posts.update(post_id=1,  message='Required-field')
```

### Likes manipulation
```python
likes.list() # all likes
likes.list(commnet_id=1) # likes for certain comment
likes.list(post_id=1) # likes for certain post
likes.list(wiki_page_id=1) # likes for certain wiki page

likes.get(like_id=1) # info about certain like (including what is being liked [post, comment,..]
likes.unlike(like_id=1) # unlike

likes.like(commnet_id=1) # like a comment
likes.like(post_id=1) # likes post
likes.like(wiki_page_id=1) # like a wiki page
```

### Wiki manipulation
```python
wikis.list() # all wiki pages
wikis.list(space_id=1) # all wiki pages in certain space
wikis.get(wiki_page_id=1) # get certain wiki page
wikis.delete(wiki_page_id=1) # delete certain wiki page
# create normal page in certain space
wikis.create(space_id='space-id-integer', title='Required-field', content=None, is_category=False, parent_category_page_id=None, is_home=False, only_admin_can_edit=False, is_public=False)
# create category page (can have sub pages) in certain space 
# Category pages can not be sub pages themselves so value `parent_category_page_id` will be ignoed
wikis.create(space_id='space-id-integer', title='Required-field', content=None, is_category=True, parent_category_page_id=None, is_home=False, only_admin_can_edit=False, is_public=False)
# create wiki page [Sub page/Child page] in another Category page
# provide parent_category_page_id (Parent page ID) & set is_category to false
wikis.create(space_id='space-id-integer', title='Required-field', content=None, is_category=False, parent_category_page_id='Parent-Category-page-id', is_home=False, only_admin_can_edit=False, is_public=False) 
# create personal wiki for certain user
wikis.create(user_id='user-id-integer', title='Required-field', content=None, is_category=False, parent_category_page_id='Parent-Category-page-id', is_home=False, only_admin_can_edit=False, is_public=False) 
# Update wiki page
wikis.update(wiki_page_id='Required-wiki-page-id-integer', title='Required-field', content=None, is_category=False, parent_category_page_id=None, is_home=False, only_admin_can_edit=False, is_public=False) 
# migrate all wikipages in space/user wiki to another space/user wiki
wikis.migrate(from_use_id=None, from_space_id=None, to_user_id=None, to_space_id=None)
```

### Comments
```python
comments.get(id=1) # Get comment by ID
```

### Spaces
```python

spaces.list() # all spaces
spaces.list(query='text') # all spaces with name, description or tags mathcing query
spaces.delete(space_id=1) # delete certain space
spaces.enable(space_id=1) # enable certain space
spaces.disable(space_id=1) # disable certain space
spaces.archive(space_id=1) # archive certain space
spaces.unarchive(space_id=1) # unarchive certain space

# if private -> means visible to users or not
# join_policy_invites_only -> True :: Members can access space only by invites
#                          -> False ::  Members can access space by invites and by requests (assuming space is visible)
# if private is True, then join_policy_invites_only value will be ignored and will always be True
spaces.create(name='Required-field', description=None, private=False, tags=[], join_policy_invites_only=False)

# Update space
spaces.update(self, space_id, name=None, description=None, tags=None, private=None, join_policy_invites_only=None)
```
