from .Country import Country


class Api(object):
    def __init__(self, request):
        self.request = request


class UserAPI(Api):
    def list(self, query=None):
        if not query:
            return self.request.get("/user")
        return self.request.get("/user", q=query)

    def create(
        self,
        username,
        email,
        password,
        firstname,
        lastname,
        title=None,
        gender=None,
        street=None,
        city=None,
        country=None,
        zip=None,
    ):

        data = {
            "account": {"username": username, "email": email},
            "profile": {
                "firstname": firstname,
                "lastname": lastname,
                "title": title,
                "gender": gender,
                "street": street,
                "city": city,
                "zip": zip,
                "country": Country.get_code(country),
            },
            "password": {"newPassword": password},
        }

        return self.request.post("/user", data)

    def get(self, user_id):
        return self.request.get("/user/{}".format(user_id))

    def update(
        self,
        user_id,
        username=None,
        email=None,
        password=None,
        firstname=None,
        lastname=None,
        title=None,
        gender=None,
        street=None,
        city=None,
        country=None,
        zip=None,
        enabled=None,
    ):
        """
        IMPORTANT: Set Parameter value to '' if you want to remove it, otherwise it will be ignored
        """
        data = {}

        if username is not None or email is not None:
            data["account"] = {}
            if username is not None:
                data["account"]["username"] = username
            if email is not None:
                data["account"]["email"] = email

        if password is not None:
            data["password"] = {"newPassword": password}

        if (
            firstname is not None
            or lastname is not None
            or title is not None
            or gender is not None
            or street is not None
            or city is not None
            or country is not None
            or zip is not None
        ):
            data["profile"] = {}
            if firstname is not None:
                data["profile"]["firstname"] = firstname
            if lastname is not None:
                data["profile"]["lastname"] = lastname
            if title is not None:
                data["profile"]["title"] = title
            if gender is not None:
                data["profile"]["gender"] = gender
            if street is not None:
                data["profile"]["street"] = street
            if city is not None:
                data["profile"]["city"] = city
            if zip is not None:
                data["profile"]["zip"] = zip
            if country is not None:
                data["profile"]["country"] = Country.get_code(country)

            if enabled is not None:
                if enabled:
                    data["account"]["enabled"] = 1
                else:
                    data["account"]["enabled"] = 0

        return self.request.put("/user/{}".format(user_id), data)

    def delete(self, user_id):
        return self.request.delete("/user/full/{}".format(user_id))

    def enable(self, user_id):
        data = {"account": {"status": 1}}
        return self.request.put("/user/{}".format(user_id), data)

    def disable(self, user_id):
        data = {"account": {"status": 0}}
        return self.request.put("/user/{}".format(user_id), data)


class CommentApi(Api):
    def get(self, comment_id):
        return self.request.get("/comment/{}".format(comment_id))


class PostAPI(Api):
    def list(self, space_id=None):
        if space_id:
            res = self.request.get("/space/{}".format(space_id))
            if "code" in res and res["code"] != 200:
                return res
            return self.request.get("/post/container/{}".format(res["contentcontainer_id"]))
        return self.request.get("/post")

    def get(self, post_id):
        return self.request.get("/post/{}".format(post_id))

    def delete(self, post_id):
        return self.request.delete("/post/{}".format(post_id))

    def update(self, post_id, message):
        data = {"message": message}

        return self.request.put("/post/{}".format(post_id), data)

    def create(self, space_id, message):
        res = self.request.get("/space/{}".format(space_id))
        if "code" in res and res["code"] != 200:
            return res

        data = {"message": message}
        return self.request.post("/post/container/{}".format(res["contentcontainer_id"]), data)


class SpaceAPI(Api):
    def get(self, space_id):
        return self.request.get("/space/{}".format(space_id))

    def list(self, query=None):
        if not query:
            return self.request.get("/space")
        return self.request.get("/space", q=query)

    def delete(self, space_id):
        return self.request.delete("/space/{}".format(space_id))

    def create(self, name, description=None, private=False, tags=[], join_policy_invites_only=False):
        """
        :param join_policy_invites_only: only used when space is public, if false means invites & requests
        :return:
        """

        data = {
            "name": name,
            "description": description,
            "tags": ",".join(tags),
            "visibility": 0 if private else 1,  # 0 means members only, 1 means for registerd users
        }

        if not private:
            data["join_policy"] = 0 if join_policy_invites_only else 1
        else:
            data["join_policy"] = 0
        return self.request.post("/space", data)

    def enable(self, space_id):
        data = {"status": 1}
        return self.request.put("/space/{}".format(space_id), data)

    def disable(self, space_id):
        data = {"status": 0}
        return self.request.put("/space/{}".format(space_id), data)

    def archive(self, space_id):
        data = {"status": 2}
        return self.request.put("/space/{}".format(space_id), data)

    def unarchive(self, space_id):
        return self.enable(space_id)

    def update(self, space_id, name=None, description=None, tags=None, private=None, join_policy_invites_only=None):
        data = {}

        if name:
            data["name"] = name
            data["url"] = name

        if description:
            data["description"] = description

        if tags is not None:
            data["tags"] = ",".join(tags)

        if private is not None:
            if private is True:
                data["visibility"] = 0
                data["join_policy"] = 0
            else:
                data["visibility"] = 1
                if join_policy_invites_only is not None:

                    data["join_policy"] = 0 if join_policy_invites_only is True else 1

        return self.request.put("/space/{}".format(space_id), data)


class LikeAPI(Api):
    def get(self, like_id):
        return self.request.get("/like/{}".format(like_id))

    def unlike(self, like_id):
        return self.request.delete("/like/{}".format(like_id))

    def list(self, post_id=None, comment_id=None, wiki_page_id=None):
        if post_id:
            params = {"model": "post", "pk": post_id}
        elif comment_id:
            params = {"model": "comment", "pk": comment_id}
        elif wiki_page_id:
            params = {"model": "wikipage", "pk": wiki_page_id}
        else:
            params = {}
        return self.request.get("/like", **params)

    def like(self, post_id=None, comment_id=None, wiki_page_id=None):
        if post_id:
            return self.request.put("/like/post/{}".format(post_id), {})
        if comment_id:
            return self.request.put("/like/comment/{}".format(comment_id), {})
        if wiki_page_id:
            return self.request.put("/like/wikipage/{}".format(wiki_page_id), {})
        return {"code": 404, "message": "Select post or comment or wiki page to like", "name": "Not Found"}


class WikiAPI(Api):
    def get(self, wiki_page_id):
        return self.request.get("/wiki/{}".format(wiki_page_id))

    def list(self, space_id=None):
        if not space_id:
            return self.request.get("/wiki")

        res = self.request.get("/space/{}".format(space_id))
        if "code" in res and res["code"] != 200:
            return res

        container_id = res["contentcontainer_id"]

        return self.request.get("/wiki/container/{}".format(container_id))

    def delete(self, wiki_page_id):
        return self.request.delete("/wiki/{}".format(wiki_page_id))

    def create(
        self,
        title,
        space_id=None,
        user_id=None,
        content=None,
        is_category=False,
        parent_category_page_id=None,
        is_home=False,
        only_admin_can_edit=False,
        is_public=False,
    ):
        if space_id:
            res = self.request.get("/space/{}".format(space_id))
            if "code" in res and res["code"] != 200:
                return res

            container_id = res["contentcontainer_id"]
        elif user_id:
            res = self.request.get("/user/{}".format(user_id))
            if "code" in res and res["code"] != 200:
                return res

            container_id = res["account"]["contentcontainer_id"]

        data = {
            "title": title,
            "is_home": 1 if is_home else 0,
            "is_category": 1 if is_category else 0,
            "protected": 1 if only_admin_can_edit else 0,
            "parent_page_id": parent_category_page_id,
            "is_public": 1 if is_public else 0,
            "content": content,
        }

        if is_category:
            data.pop("parent_page_id")

        return self.request.post("/wiki/container/{}".format(container_id), data)

    def update(
        self,
        wiki_page_id,
        title,
        content=None,
        is_category=None,
        parent_category_page_id=None,
        is_home=None,
        only_admin_can_edit=None,
        is_public=None,
    ):
        data = {"title": title, "content": content}

        if is_category is not None:
            data["is_category"] = 1 if is_category else 0

        if parent_category_page_id is not None:
            data["parent_category_page_id"] = parent_category_page_id

        if is_category is not None:
            data["is_category"] = 1 if is_category else 0

        if is_home is not None:
            data["is_home"] = 1 if is_home else 0

        if only_admin_can_edit is not None:
            data["only_admin_can_edit"] = 1 if only_admin_can_edit else 0

        if is_public is not None:
            data["is_public"] = 1 if is_public else 0

        return self.request.put("/wiki/{}".format(wiki_page_id), data)

    def migrate(self, from_use_id=None, from_space_id=None, to_user_id=None, to_space_id=None):
        from_container = None
        to_container = None

        if from_use_id:
            res = self.request.get("/user/{}".format(from_use_id))
            if "code" in res and res["code"] != 200:
                return res
            from_container = res["account"]["contentcontainer_id"]
        if to_user_id:
            res = self.request.get("/user/{}".format(to_user_id))
            if "code" in res and res["code"] != 200:
                return res
            to_container = res["account"]["contentcontainer_id"]

        if from_space_id:
            res = self.request.get("/space/{}".format(from_space_id))
            if "code" in res and res["code"] != 200:
                return res
            from_container = res["contentcontainer_id"]

        if to_space_id:
            res = self.request.get("/space/{}".format(to_space_id))
            if "code" in res and res["code"] != 200:
                return res
            to_container = res["contentcontainer_id"]
        return self.request.post("/wiki/migrate/{0}/{1}".format(from_container, to_container), {})
