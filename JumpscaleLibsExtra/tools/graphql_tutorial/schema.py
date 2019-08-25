from Jumpscale import j
import random
import asyncio
import graphene


class Author(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()


class Post(graphene.ObjectType):
    id = graphene.Int()
    title = graphene.String()
    author = graphene.Field(Author)


class Query(graphene.ObjectType, j.baseclasses.object_config):
    posts = graphene.List(Post)

    def resolve_posts(self, root):
        _SCHEMA_TEXT = """
        @url = graphql.info.schema
        info_id* = (I)
        title = (S) 
        author = (S)
        name = (S)
        """
        model = j.application.bcdb_system.model_get(schema=_SCHEMA_TEXT)

        results = []
        for item in model.iterate():
            results.append(Post(id=item.id, title=item.title, author=Author(id=item.id, name=item.name)))
        return results


class RandomType(graphene.ObjectType):
    seconds = graphene.Int()
    random_int = graphene.Int()


class Subscription(graphene.ObjectType):
    count_seconds = graphene.Float(up_to=graphene.Int())
    random_int = graphene.Field(RandomType)

    async def resolve_count_seconds(root, info, up_to=500):
        for i in range(up_to):
            print("YIELD SECOND", i)
            yield i
            await asyncio.sleep(1.0)
        yield up_to

    async def resolve_random_int(root, info):
        i = 0
        while True:
            yield RandomType(seconds=i, random_int=random.randint(0, 500))
            await asyncio.sleep(1.0)
            i += 1


schema = graphene.Schema(query=Query, subscription=Subscription)
