from Jumpscale import j

# import time
# import datetime
# import jose.jwt
# from paramiko.ssh_exception import BadAuthenticationType
# from .Machine import Machine
# from .Space import Space

JSBASE = j.baseclasses.object


class Authorizables(j.baseclasses.object):
    def __init__(self):
        JSBASE.__init__(self)

    @property
    def owners(self):
        _owners = []
        for user in self.model["acl"]:
            if not user["canBeDeleted"]:
                _owners.append(user["userGroupId"])
        return _owners

    @property
    def authorized_users(self):
        return [u["userGroupId"] for u in self.model["acl"]]

    def authorize_user(self, username, right=""):
        """
        Will authorize a new user

        returns True if the user was successfully authorized
        returns False if @username is in the list of the authorized users
        """
        if not right:
            right = "ACDRUX"
        if username not in self.authorized_users:
            self._addUser(username, right)
            self.refresh()
            return True
        return False

    def unauthorize_user(self, username):
        """
        Will unauthorize a user

        returns True if the user was successfully unauthorized
        returns False if @username is not in the list of authorized users or has flag 'canBeDeleted' set to False
        """
        canBeDeleted = [u["userGroupId"] for u in self.model["acl"] if u.get("canBeDeleted", True) is True]
        if username in self.authorized_users and username in canBeDeleted:
            self._deleteUser(username)
            self.refresh()
            return True
        return False

    def update_access(self, username, right=""):
        """
        Will update access right of a user

        returns True if the access was successfully updated
        returns False if @username is not in the list of the authorized users
        """
        if not right:
            right = "ACDRUX"
        if username in self.authorized_users:
            self._updateUser(username, right)
            self.refresh()
            return True
        return False
