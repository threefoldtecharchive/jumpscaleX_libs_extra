# This file is part of Radicale Server - Calendar Server
# Copyright © 2014 Jean-Marc Martins
# Copyright © 2012-2017 Guillaume Ayoub
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Radicale.  If not, see <http://www.gnu.org/licenses/>.

"""
Storage backends.

This module loads the storage backend, according to the storage configuration.

Default storage uses one folder per collection and one file per collection
entry.

"""
import datetime
import binascii
import contextlib
import json
import logging
import os
import pickle
import posixpath
import shlex
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from hashlib import md5
from importlib import import_module
from itertools import chain, groupby
from math import log
from random import getrandbits
from tempfile import NamedTemporaryFile, TemporaryDirectory
from Jumpscale import j
import vobject

from radicale import xmlutils
import fcntl

INTERNAL_TYPES = ("multifilesystem",)


def load(configuration, logger):
    """Load the storage manager chosen in configuration."""
    collection_class = Collection

    class CollectionCopy(collection_class):
        """Collection copy, avoids overriding the original class attributes."""

    CollectionCopy.configuration = configuration
    CollectionCopy.logger = logger
    return CollectionCopy


def check_and_sanitize_item(vobject_item, is_collection=False, uid=None, tag=None):
    """Check vobject items for common errors and add missing UIDs.

    ``is_collection`` indicates that vobject_item contains unrelated
    components.

    If ``uid`` is not set, the UID is generated randomly.

    The ``tag`` of the collection.

    """
    if tag and tag not in ("VCALENDAR", "VADDRESSBOOK"):
        raise ValueError("Unsupported collection tag: %r" % tag)
    if vobject_item.name == "VCALENDAR" and tag == "VCALENDAR":
        component_name = None
        object_uid = None
        object_uid_set = False
        for component in vobject_item.components():
            # https://tools.ietf.org/html/rfc4791#section-4.1
            if component.name == "VTIMEZONE":
                continue
            if component_name is None or is_collection:
                component_name = component.name
            elif component_name != component.name:
                raise ValueError("Multiple component types in object: %r, %r" % (component_name, component.name))
            if component_name not in ("VTODO", "VEVENT", "VJOURNAL"):
                continue
            component_uid = get_uid(component)
            if not object_uid_set or is_collection:
                object_uid_set = True
                object_uid = component_uid
                if component_uid is None:
                    component.add("UID").value = uid or random_uuid4()
                elif not component_uid:
                    component.uid.value = uid or random_uuid4()
            elif not object_uid or not component_uid:
                raise ValueError("Multiple %s components without UID in " "object" % component_name)
            elif object_uid != component_uid:
                raise ValueError(
                    "Multiple %s components with different UIDs in object: "
                    "%r, %r" % (component_name, object_uid, component_uid)
                )
            # vobject interprets recurrence rules on demand
            try:
                component.rruleset
            except Exception as e:
                raise ValueError("invalid recurrence rules in %s" % component.name) from e
    elif vobject_item.name == "VCARD" and tag == "VADDRESSBOOK":
        # https://tools.ietf.org/html/rfc6352#section-5.1
        object_uid = get_uid(vobject_item)
        if object_uid is None:
            vobject_item.add("UID").value = uid or random_uuid4()
        elif not object_uid:
            vobject_item.uid.value = uid or random_uuid4()
    elif vobject_item.name == "VLIST" and tag == "VADDRESSBOOK":
        # Custom format used by SOGo Connector to store lists of contacts
        pass
    else:
        raise ValueError(
            "Item type %r not supported in %s collection" % (vobject_item.name, repr(tag) if tag else "generic")
        )


def check_and_sanitize_props(props):
    """Check collection properties for common errors."""
    tag = props.get("tag")
    if tag and tag not in ("VCALENDAR", "VADDRESSBOOK"):
        raise ValueError("Unsupported collection tag: %r" % tag)


def random_uuid4():
    """Generate a pseudo-random UUID"""
    r = "%016x" % getrandbits(128)
    return "%s-%s-%s-%s-%s" % (r[:8], r[8:12], r[12:16], r[16:20], r[20:])


def scandir(path, only_dirs=False, only_files=False):
    """Iterator for directory elements. (For compatibility with Python < 3.5)

    ``only_dirs`` only return directories

    ``only_files`` only return files

    """
    if sys.version_info >= (3, 5):
        for entry in os.scandir(path):
            if (not only_files or entry.is_file()) and (not only_dirs or entry.is_dir()):
                yield entry.name
    else:
        for name in os.listdir(path):
            p = os.path.join(path, name)
            if (not only_files or os.path.isfile(p)) and (not only_dirs or os.path.isdir(p)):
                yield name


def get_etag(text):
    """Etag from collection or item.

    Encoded as quoted-string (see RFC 2616).

    """
    etag = md5()
    etag.update(text.encode("utf-8"))
    return '"%s"' % etag.hexdigest()


def get_uid(vobject_component):
    """UID value of an item if defined."""
    return vobject_component.uid.value if hasattr(vobject_component, "uid") else None


def get_uid_from_object(vobject_item):
    """UID value of an calendar/addressbook object."""
    if vobject_item.name == "VCALENDAR":
        if hasattr(vobject_item, "vevent"):
            return get_uid(vobject_item.vevent)
        if hasattr(vobject_item, "vjournal"):
            return get_uid(vobject_item.vjournal)
        if hasattr(vobject_item, "vtodo"):
            return get_uid(vobject_item.vtodo)
    elif vobject_item.name == "VCARD":
        return get_uid(vobject_item)
    return None


def sanitize_path(path):
    """Make path absolute with leading slash to prevent access to other data.

    Preserve a potential trailing slash.

    """
    trailing_slash = "/" if path.endswith("/") else ""
    path = posixpath.normpath(path)
    new_path = "/"
    for part in path.split("/"):
        if not is_safe_path_component(part):
            continue
        new_path = posixpath.join(new_path, part)
    trailing_slash = "" if new_path.endswith("/") else trailing_slash
    return new_path + trailing_slash


def is_safe_path_component(path):
    """Check if path is a single component of a path.

    Check that the path is safe to join too.

    """
    return path and "/" not in path and path not in (".", "..")


def is_safe_filesystem_path_component(path):
    """Check if path is a single component of a local and posix filesystem
       path.

    Check that the path is safe to join too.

    """
    return (
        path
        and not os.path.splitdrive(path)[0]
        and not os.path.split(path)[0]
        and path not in (os.curdir, os.pardir)
        and not path.startswith(".")
        and not path.endswith("~")
        and is_safe_path_component(path)
    )


def path_to_filesystem(root, *paths):
    """Convert path to a local filesystem path relative to base_folder.

    `root` must be a secure filesystem path, it will be prepend to the path.

    Conversion of `paths` is done in a secure manner, or raises ``ValueError``.

    """
    paths = [sanitize_path(path).strip("/") for path in paths]
    safe_path = root
    for path in paths:
        if not path:
            continue
        for part in path.split("/"):
            if not is_safe_filesystem_path_component(part):
                raise UnsafePathError(part)
            safe_path_parent = safe_path
            safe_path = os.path.join(safe_path, part)
            # Check for conflicting files (e.g. case-insensitive file systems
            # or short names on Windows file systems)
            if os.path.lexists(safe_path) and part not in scandir(safe_path_parent):
                raise CollidingPathError(part)
    return safe_path


def left_encode_int(v):
    length = int(log(v, 256)) + 1 if v != 0 else 1
    return bytes((length,)) + v.to_bytes(length, "little")


class UnsafePathError(ValueError):
    def __init__(self, path):
        message = "Can't translate name safely to filesystem: %r" % path
        super().__init__(message)


class CollidingPathError(ValueError):
    def __init__(self, path):
        message = "File name collision: %r" % path
        super().__init__(message)


class ComponentExistsError(ValueError):
    def __init__(self, path):
        message = "Component already exists: %r" % path
        super().__init__(message)


class ComponentNotFoundError(ValueError):
    def __init__(self, path):
        message = "Component doesn't exist: %r" % path
        super().__init__(message)


class Item:
    def __init__(
        self,
        collection,
        item=None,
        href=None,
        last_modified=None,
        text=None,
        etag=None,
        uid=None,
        name=None,
        component_name=None,
    ):
        """Initialize an item.

        ``collection`` the parent collection.

        ``href`` the href of the item.

        ``last_modified`` the HTTP-datetime of when the item was modified.

        ``text`` the text representation of the item (optional if ``item`` is
        set).

        ``item`` the vobject item (optional if ``text`` is set).

        ``etag`` the etag of the item (optional). See ``get_etag``.

        ``uid`` the UID of the object (optional). See ``get_uid_from_object``.

        """
        if text is None and item is None:
            raise ValueError("at least one of 'text' or 'item' must be set")
        self.collection = collection
        self.href = href
        self.last_modified = last_modified
        self._text = text
        self._item = item
        self._etag = etag
        self._uid = uid
        self._name = name
        self._component_name = component_name

    def __getattr__(self, attr):
        return getattr(self.item, attr)

    def serialize(self):
        if self._text is None:
            try:
                self._text = self.item.serialize()
            except Exception as e:
                raise RuntimeError(
                    "Failed to serialize item %r from %r: %s" % (self.href, self.collection.path, e)
                ) from e
        return self._text

    @property
    def item(self):
        if self._item is None:
            try:
                self._item = vobject.readOne(self._text)
            except Exception as e:
                raise RuntimeError("Failed to parse item %r from %r: %s" % (self.href, self.collection.path, e)) from e
        return self._item

    @property
    def etag(self):
        """Encoded as quoted-string (see RFC 2616)."""
        if self._etag is None:
            self._etag = get_etag(self.serialize())
        return self._etag

    @property
    def uid(self):
        if self._uid is None:
            self._uid = get_uid_from_object(self.item)
        return self._uid

    @property
    def name(self):
        if self._name is not None:
            return self._name
        return self.item.name

    @property
    def component_name(self):
        if self._component_name is not None:
            return self._component_name
        return xmlutils.find_tag(self.item)


class BaseCollection:

    # Overriden on copy by the "load" function
    configuration = None
    logger = None

    # Properties of instance
    """The sanitized path of the collection without leading or trailing ``/``.
    """
    path = ""

    # @classmethod
    # def static_init():
    #     """init collection copy"""
    #     pass

    @property
    def owner(self):
        """The owner of the collection."""
        return self.path.split("/", maxsplit=1)[0]

    @property
    def is_principal(self):
        """Collection is a principal."""
        return bool(self.path) and "/" not in self.path

    @owner.setter
    def owner(self, value):
        # DEPRECATED: Included for compatibility reasons
        pass

    @is_principal.setter
    def is_principal(self, value):
        # DEPRECATED: Included for compatibility reasons
        pass

    @classmethod
    def discover(cls, path, depth="0"):
        """Discover a list of collections under the given ``path``.

        ``path`` is sanitized.

        If ``depth`` is "0", only the actual object under ``path`` is
        returned.

        If ``depth`` is anything but "0", it is considered as "1" and direct
        children are included in the result.

        The root collection "/" must always exist.

        """
        raise NotImplementedError

    @classmethod
    def move(cls, item, to_collection, to_href):
        """Move an object.

        ``item`` is the item to move.

        ``to_collection`` is the target collection.

        ``to_href`` is the target name in ``to_collection``. An item with the
        same name might already exist.

        """
        if item.collection.path == to_collection.path and item.href == to_href:
            return
        to_collection.upload(to_href, item.item)
        item.collection.delete(item.href)

    @property
    def etag(self):
        """Encoded as quoted-string (see RFC 2616)."""
        etag = md5()
        for item in self.get_all():
            etag.update((item.href + "/" + item.etag).encode("utf-8"))
        etag.update(json.dumps(self.get_meta(), sort_keys=True).encode())
        return '"%s"' % etag.hexdigest()

    @classmethod
    def create_collection(cls, href, collection=None, props=None):
        """Create a collection.

        ``href`` is the sanitized path.

        If the collection already exists and neither ``collection`` nor
        ``props`` are set, this method shouldn't do anything. Otherwise the
        existing collection must be replaced.

        ``collection`` is a list of vobject components.

        ``props`` are metadata values for the collection.

        ``props["tag"]`` is the type of collection (VCALENDAR or
        VADDRESSBOOK). If the key ``tag`` is missing, it is guessed from the
        collection.

        """
        raise NotImplementedError

    def sync(self, old_token=None):
        """Get the current sync token and changed items for synchronization.

        ``old_token`` an old sync token which is used as the base of the
        delta update. If sync token is missing, all items are returned.
        ValueError is raised for invalid or old tokens.

        WARNING: This simple default implementation treats all sync-token as
                 invalid. It adheres to the specification but some clients
                 (e.g. InfCloud) don't like it. Subclasses should provide a
                 more sophisticated implementation.

        """
        token = "http://radicale.org/ns/sync/%s" % self.etag.strip('"')
        if old_token:
            raise ValueError("Sync token are not supported")
        return token, self.list()

    def list(self):
        """List collection items."""
        raise NotImplementedError

    def get(self, href):
        """Fetch a single item."""
        raise NotImplementedError

    def get_multi(self, hrefs):
        """Fetch multiple items. Duplicate hrefs must be ignored.

        DEPRECATED: use ``get_multi2`` instead

        """
        return (self.get(href) for href in set(hrefs))

    def get_multi2(self, hrefs):
        """Fetch multiple items.

        Functionally similar to ``get``, but might bring performance benefits
        on some storages when used cleverly. It's not required to return the
        requested items in the correct order. Duplicated hrefs can be ignored.

        Returns tuples with the href and the item or None if the item doesn't
        exist.

        """
        return ((href, self.get(href)) for href in hrefs)

    def get_all(self):
        """Fetch all items.

        Functionally similar to ``get``, but might bring performance benefits
        on some storages when used cleverly.

        """
        return map(self.get, self.list())

    def get_all_filtered(self, filters):
        """Fetch all items with optional filtering.

        This can largely improve performance of reports depending on
        the filters and this implementation.

        Returns tuples in the form ``(item, filters_matched)``.
        ``filters_matched`` is a bool that indicates if ``filters`` are fully
        matched.

        This returns all events by default
        """
        return ((item, False) for item in self.get_all())

    def pre_filtered_list(self, filters):
        """List collection items with optional pre filtering.

        DEPRECATED: use ``get_all_filtered`` instead

        """
        return self.get_all()

    def has(self, href):
        """Check if an item exists by its href.

        Functionally similar to ``get``, but might bring performance benefits
        on some storages when used cleverly.

        """
        return self.get(href) is not None

    def upload(self, href, vobject_item):
        """Upload a new or replace an existing item."""
        raise NotImplementedError

    def delete(self, href=None):
        """Delete an item.

        When ``href`` is ``None``, delete the collection.

        """
        raise NotImplementedError

    def get_meta(self, key=None):
        """Get metadata value for collection.

        Return the value of the property ``key``. If ``key`` is ``None`` return
        a dict with all properties

        """
        raise NotImplementedError

    def set_meta(self, props):
        """Set metadata values for collection.

        ``props`` a dict with updates for properties. If a value is empty, the
        property must be deleted.

        DEPRECATED: use ``set_meta_all`` instead

        """
        raise NotImplementedError

    def set_meta_all(self, props):
        """Set metadata values for collection.

        ``props`` a dict with values for properties.

        """
        delta_props = self.get_meta()
        for key in delta_props.keys():
            if key not in props:
                delta_props[key] = None
        delta_props.update(props)
        self.set_meta(delta_props)

    @property
    def last_modified(self):
        """Get the HTTP-datetime of when the collection was modified."""
        raise NotImplementedError

    def serialize(self):
        """Get the unicode string representing the whole collection."""
        if self.get_meta("tag") == "VCALENDAR":
            in_vcalendar = False
            vtimezones = ""
            included_tzids = set()
            vtimezone = []
            tzid = None
            components = ""
            # Concatenate all child elements of VCALENDAR from all items
            # together, while preventing duplicated VTIMEZONE entries.
            # VTIMEZONEs are only distinguished by their TZID, if different
            # timezones share the same TZID this produces errornous ouput.
            # VObject fails at this too.
            for item in self.get_all():
                depth = 0
                for line in item.serialize().split("\r\n"):
                    if line.startswith("BEGIN:"):
                        depth += 1
                    if depth == 1 and line == "BEGIN:VCALENDAR":
                        in_vcalendar = True
                    elif in_vcalendar:
                        if depth == 1 and line.startswith("END:"):
                            in_vcalendar = False
                        if depth == 2 and line == "BEGIN:VTIMEZONE":
                            vtimezone.append(line + "\r\n")
                        elif vtimezone:
                            vtimezone.append(line + "\r\n")
                            if depth == 2 and line.startswith("TZID:"):
                                tzid = line[len("TZID:") :]
                            elif depth == 2 and line.startswith("END:"):
                                if tzid is None or tzid not in included_tzids:
                                    vtimezones += "".join(vtimezone)
                                    included_tzids.add(tzid)
                                vtimezone.clear()
                                tzid = None
                        elif depth >= 2:
                            components += line + "\r\n"
                    if line.startswith("END:"):
                        depth -= 1
            template = vobject.iCalendar()
            displayname = self.get_meta("D:displayname")
            if displayname:
                template.add("X-WR-CALNAME")
                template.x_wr_calname.value_param = "TEXT"
                template.x_wr_calname.value = displayname
            description = self.get_meta("C:calendar-description")
            if description:
                template.add("X-WR-CALDESC")
                template.x_wr_caldesc.value_param = "TEXT"
                template.x_wr_caldesc.value = description
            template = template.serialize()
            template_insert_pos = template.find("\r\nEND:VCALENDAR\r\n") + 2
            assert template_insert_pos != -1
            return template[:template_insert_pos] + vtimezones + components + template[template_insert_pos:]
        elif self.get_meta("tag") == "VADDRESSBOOK":
            return "".join((item.serialize() for item in self.get_all()))
        return ""

    @classmethod
    def verify(cls):
        """Check the storage for errors."""
        return True


ITEM_CACHE_VERSION = 1


class Database:
    bcdb = j.data.bcdb.get("caldav")
    user_model = bcdb.model_get(url="threebot.calendar.user.1")
    calendar_model = bcdb.model_get(url="threebot.calendar.calendar.1")
    addressbook_model = bcdb.model_get(url="threebot.calendar.addressbook.1")
    event_model = bcdb.model_get(url="threebot.calendar.event.1")
    contact_model = bcdb.model_get(url="threebot.calendar.contact.1")
    attachment_model = bcdb.model_get(url="threebot.calendar.attachment.1")
    email_model = bcdb.model_get(url="threebot.calendar.email.1")
    telephone_model = bcdb.model_get(url="threebot.calendar.telephone.1")
    mailaddress_model = bcdb.model_get(url="threebot.calendar.mailaddress.1")
    instantmessaging_model = bcdb.model_get(url="threebot.calendar.instantmessaging.1")

    @classmethod
    def find_collections(cls, collection_id, user_id):
        calendars = cls.calendar_model.find(calendar_id=collection_id, user_id=user_id)
        if calendars:
            return calendars
        return cls.addressbook_model.find(addressbook_id=collection_id, user_id=user_id)

    @classmethod
    def user_exists(cls, user_id):
        users = cls.user_model.find(user_id=user_id)
        if users:
            return True
        return False

    @classmethod
    def create_user(cls, user_id):
        user = cls.user_model.new()
        user.user_id = user_id
        user.save()

    @classmethod
    def find_items(cls, item_id, collection_id=None, user_id=None):
        collections = cls.find_collections(collection_id, user_id)
        if not collections:
            return []
        collection = collections[0]
        if collection.type == "calendar":
            return cls.event_model.find(item_id=item_id, calendar_id=collection_id, user_id=user_id)
        return cls.contact_model.find(item_id=item_id, addressbook_id=collection_id, user_id=user_id)

    @classmethod
    def get_collection(cls, collection_id, user_id):
        collections = cls.find_collections(collection_id=collection_id, user_id=user_id)
        if len(collections) <= 0:
            raise j.exceptions.NotFound(f"Can not find collection:{collection_id} for user:{user_id}")
        return collections[0]


class Collection(BaseCollection):
    """Collection stored in several files per calendar."""

    def __init__(self, path, principal=None, folder=None, filesystem_path=None):
        # Path should already be sanitized
        path_list = path.strip("/").split("/")
        if len(path_list) >= 1:
            self.user_id = path_list[0]
        else:
            self.user_id = None
        if len(path_list) >= 2:
            self.collection_id = path_list[1]
        else:
            self.collection_id = None
        self.path = sanitize_path(path).strip("/")
        self._encoding = self.configuration.get("encoding", "stock")
        # DEPRECATED: Use ``self._encoding`` instead
        self.encoding = self._encoding
        self._filesystem_path = None
        self._meta_cache = None
        self._etag_cache = None
        self._item_cache_cleaned = False

    @staticmethod
    def _find_available_file_name(exists_fn, suffix=""):
        # Prevent infinite loop
        for _ in range(1000):
            file_name = random_uuid4() + suffix
            if not exists_fn(file_name):
                return file_name
        # something is wrong with the PRNG
        raise RuntimeError("No unique random sequence found")

    @classmethod
    def discover(cls, path, depth="0", child_context_manager=(lambda path, href=None: contextlib.ExitStack())):
        # Path should already be sanitized
        sane_path = sanitize_path(path).strip("/")
        attributes = sane_path.split("/") if sane_path else []

        if sane_path:
            path_list = sane_path.split("/")
            if len(path_list) == 1:
                if not Database.user_exists(path_list[0]):
                    return
            else:
                collections = Database.find_collections(path_list[1], path_list[0])
                if not collections:
                    return

        if len(attributes) >= 3:
            if Database.find_items(attributes[-1], attributes[-2], attributes[-3]):
                href = attributes.pop()
            else:
                return
        else:
            href = None

        sane_path = "/".join(attributes)
        collection = cls(sane_path)

        if href:
            # it is an item
            yield collection.get(href)
            return

        yield collection

        if depth == "0":
            return

        for href in collection.list():
            with child_context_manager(sane_path, href):
                yield collection.get(href)
        # get all collections for a user
        self = cls(sane_path)
        collections = Database.calendar_model.find(user_id=self.user_id) + Database.addressbook_model.find(
            user_id=self.user_id
        )
        for collection in collections:
            if collection.type == "calendar":
                yield cls("/{}/{}".format(collection.user_id, collection.calendar_id))
            else:
                yield cls("/{}/{}".format(collection.user_id, collection.addressbook_id))

    @classmethod
    def verify(cls):
        item_errors = collection_errors = 0

        @contextlib.contextmanager
        def exception_cm(path, href=None):
            nonlocal item_errors, collection_errors
            try:
                yield
            except Exception as e:
                if href:
                    item_errors += 1
                    name = "item %r in %r" % (href, path.strip("/"))
                else:
                    collection_errors += 1
                    name = "collection %r" % path.strip("/")
                cls.logger.error("Invalid %s: %s", name, e, exc_info=True)

        remaining_paths = [""]
        while remaining_paths:
            path = remaining_paths.pop(0)
            cls.logger.debug("Verifying collection %r", path)
            with exception_cm(path):
                saved_item_errors = item_errors
                collection = None
                for item in cls.discover(path, "1", exception_cm):
                    if not collection:
                        collection = item
                        collection.get_meta()
                        continue
                    if isinstance(item, BaseCollection):
                        remaining_paths.append(item.path)
                    else:
                        cls.logger.debug("Verified item %r in %r", item.href, path)
                if item_errors == saved_item_errors:
                    collection.sync()
        return item_errors == 0 and collection_errors == 0

    @classmethod
    def create_collection(cls, href, collection=None, props=None):
        """
        href example: '/user1/01dea181-55a0-a992-4139-4cf8e948a7cf/'
        """
        self = cls(href)
        if props.get("tag") == "VCALENDAR":
            col = Database.calendar_model.new()
            col.user_id = self.user_id
            col.calendar_id = self.collection_id
            col.save()
        elif props.get("tag") == "VADDRESSBOOK":
            col = Database.addressbook_model.new()
            col.user_id = self.user_id
            col.addressbook_id = self.collection_id
            col.save()

        self.set_meta_all(props)

        if collection:
            if props.get("tag") == "VCALENDAR":
                (collection,) = collection
                items = []
                for content in ("vevent", "vtodo", "vjournal"):
                    items.extend(getattr(collection, "%s_list" % content, []))
                items_by_uid = groupby(sorted(items, key=get_uid), get_uid)
                vobject_items = {}
                for uid, items in items_by_uid:
                    new_collection = vobject.iCalendar()
                    for item in items:
                        new_collection.add(item)
                    href = self._find_available_file_name(vobject_items.get, suffix=".ics")
                    vobject_items[href] = new_collection
                self._upload_all_nonatomic(vobject_items)
            elif props.get("tag") == "VADDRESSBOOK":
                vobject_items = {}
                for card in collection:
                    href = self._find_available_file_name(vobject_items.get, suffix=".vcf")
                    vobject_items[href] = card
                self._upload_all_nonatomic(vobject_items)

        return cls(href)

    def upload_all_nonatomic(self, vobject_items):
        """DEPRECATED: Use ``_upload_all_nonatomic``"""
        return self._upload_all_nonatomic(vobject_items)

    def _upload_all_nonatomic(self, vobject_items):
        """Upload a new set of items.

        This takes a mapping of href and vobject items and
        uploads them nonatomic and without existence checks.

        """

        collection = Database.get_collection(collection_id=self.collection_id, user_id=self.user_id)

        for href, vobject_item in vobject_items.items():
            text = vobject_item.serialize()
            if vobject_item.name == "VCALENDAR":
                item = Database.event_model.new()
                item.item_id = href
                item.content = text
                item.dtstart = int(vobject_item.vevent.dtstart.value.timestamp())
                item.dtend = int(vobject_item.vevent.dtend.value.timestamp())
                item.type = "VEVENT"
                item.timezone = vobject_item.vevent.dtstart.value.tzname()
                item.title = vobject_item.vevent.summary.value
                item.description = vobject_item.vevent.description.value
                item.location = vobject_item.vevent.location.value
                for e in vobject_item.vevent.getChildren():
                    if e.name == "ATTACH":
                        a = Database.attachment_model.new()
                        a.name = e.params["FILENAME"].replace("['", "").replace("']", "")
                        a.encoding = e.params["ENCODING"].replace("['", "").replace("']", "").lower()
                        a.content = e.value
                        a.save()
            else:
                item = Database.contact_model.new()
                item.item_id = href
                item.content = text
                item.type = vobject_item.name
            item.save()
            collection.append(item)
        collection.save()

    @classmethod
    def move(cls, item, to_collection, to_href):
        os.replace(
            path_to_filesystem(item.collection._filesystem_path, item.href),
            path_to_filesystem(to_collection._filesystem_path, to_href),
        )

    def list(self):
        if not self.collection_id:
            return
        collections = Database.find_collections(self.collection_id, self.user_id)
        if collections:
            for item in collections[0].items:
                yield item.item_id

    def get(self, href, verify_href=True):
        item, _ = self._get_with_metadata(href, verify_href=verify_href)
        return item

    def _item_cache_hash(self, raw_text):
        _hash = md5()
        _hash.update(left_encode_int(ITEM_CACHE_VERSION))
        _hash.update(raw_text)
        return _hash.hexdigest()

    def _item_cache_content(self, vobject_item):
        text = vobject_item.serialize()
        etag = get_etag(text)
        uid = get_uid_from_object(vobject_item)
        name = vobject_item.name
        tag, start, end = xmlutils.find_tag_and_time_range(vobject_item)
        return uid, etag, text, name, tag, start, end

    def _get_with_metadata(self, href, verify_href=True):
        """Like ``get`` but additonally returns the following metadata:
        tag, start, end: see ``xmlutils.find_tag_and_time_range``. If
        extraction of the metadata failed, the values are all ``None``."""

        items = Database.find_items(href, self.collection_id, self.user_id)
        if items:
            raw_text = items[0].content
        else:
            return None, (None, None, None)

        vobject_items = tuple(vobject.readComponents(raw_text))
        if len(vobject_items) != 1:
            raise RuntimeError("Content contains %d components" % len(vobject_items))
        vobject_item = vobject_items[0]
        uid, etag, text, name, tag, start, end = self._item_cache_content(vobject_item)
        check_and_sanitize_item(vobject_item, uid=uid, tag=self.get_meta("tag"))

        last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time()))
        return (
            Item(
                self,
                href=href,
                last_modified=last_modified,
                etag=etag,
                text=text,
                item=vobject_item,
                uid=uid,
                name=name,
                component_name=tag,
            ),
            (tag, start, end),
        )

    def get_multi2(self, hrefs):
        collection = Database.get_collection(collection_id=self.collection_id, user_id=self.user_id)
        items = collection.items
        items_refs = list(map(lambda item: item.item_id, items))
        for href in hrefs:

            if href not in items_refs:
                yield (href, None)
            else:
                yield (href, self.get(href, verify_href=False))

    def get_all(self):
        data = (self.get(href, verify_href=False) for href in self.list())
        return (item for item in data if item)

    def get_all_filtered(self, filters):
        tag, start, end, simple = xmlutils.simplify_prefilters(filters, collection_tag=self.get_meta("tag"))
        if not tag:
            # no filter
            yield from ((item, simple) for item in self.get_all())

        for item, (itag, istart, iend) in (self._get_with_metadata(href, verify_href=False) for href in self.list()):
            if tag == itag and istart < end and iend > start:
                yield item, simple and (start <= istart or iend <= end)

    def upload(self, href, vobject_item):
        uid, etag, text, name, tag, _, _ = self._item_cache_content(vobject_item)
        collection = Database.get_collection(collection_id=self.collection_id, user_id=self.user_id)
        if vobject_item.name == "VCALENDAR":
            events = Database.event_model.find(item_id=href)
            new = True
            # already existing
            if events:
                item = events[0]
                new = False
            else:
                item = Database.event_model.new()

            item.item_id = href
            item.calendar_id = self.collection_id
            item.user_id = self.user_id
            item.content = text
            item.epoch = j.data.time.epoch
            item.dtstart = int(vobject_item.vevent.dtstart.value.timestamp())
            item.dtend = int(vobject_item.vevent.dtend.value.timestamp())
            item.type = "VEVENT"
            item.timezone = vobject_item.vevent.dtstart.value.tzname()
            item.title = vobject_item.vevent.summary.value
            item.description = vobject_item.vevent.description.value
            item.location = vobject_item.vevent.location.value

            for e in vobject_item.vevent.getChildren():
                if e.name == "ATTACH":
                    a = Database.attachment_model.new()
                    a.name = e.params["FILENAME"].replace("['", "").replace("']", "")
                    a.encoding = e.params["ENCODING"].replace("['", "").replace("']", "").lower()
                    a.content = e.value
                    a.save()

            item.save()

            if new:
                collection.items.append(item)
            else:
                idx = [i.item_id for i in collection.items].index(f"{vobject_item.vevent.uid.value}.ics")
                collection.items[idx] = item
            collection.save()
            item = Item(
                self, href=href, etag=etag, text=text, item=vobject_item, uid=uid, name=name, component_name=tag
            )
            return item
        else:
            contacts = Database.contact_model.find(item_id=href)

            new = True
            # already existing
            if contacts:
                item = contacts[0]
                new = False
            else:
                item = Database.contact_model.new()

            item.contact_id = vobject_item.uid.value
            item.item_id = href
            item.addressbook_id = self.collection_id
            item.user_id = self.user_id
            item.content = text
            item.epoch = j.data.time.epoch
            item.type = vobject_item.name

            for child in vobject_item.getChildren():
                if child.name == "N":
                    item.givenname = vobject_item.n.value.given
                    item.familyname = vobject_item.n.value.family

                elif child.name == "BDAY":
                    item.birthday = int(datetime.datetime.strptime(child.value, "%Y-%m-%d").timestamp())

                elif child.name == "CALURI":
                    item.calendar_url = child.value

                elif child.name == "CATEGORIES":
                    item.categories = child.value

                elif child.name == "NICKNAME":
                    item.nickname = child.value

                elif child.name == "X-EVOLUTION-VIDEO-URL":
                    item.videchat = child.value

                elif child.name == "X-EVOLUTION-VIDEO-URL":
                    item.videchat = child.value

                elif child.name == "X-EVOLUTION-BLOG-URL":
                    item.blog = child.value

                elif child.name == "FBURL":
                    item.facebook = child.value

                elif child.name == "X-EVOLUTION-ANNIVERSARY":
                    item.anniversary = int(datetime.datetime.strptime(child.value, "%Y-%m-%d").timestamp())

                elif child.name == "NOTE":
                    item.notes = child.value

                elif child.name == "EMAIL":
                    item.emails = []
                    e = Database.email_model.new()
                    e.email = child.value
                    e.type = child.params["TYPE"][0]
                    e.save()
                    item.emails.append(e)

                elif child.name == "TEL":
                    item.telephones = []
                    e = Database.telephone_model.new()
                    e.telephone = child.value
                    e.type = child.params["TYPE"][0]
                    e.save()
                    item.telephones.append(e)

                elif child.name == "ADR":
                    item.mailaddresses = []
                    e = Database.mailaddress_model.new()
                    e.street = child.value.street
                    e.city = child.value.city
                    e.country = child.value.country
                    e.code = child.value.code
                    e.region = child.value.region
                    e.box = child.value.box
                    e.type = child.params["TYPE"][0]
                    e.save()
                    item.mailaddresses.append(e)

                elif child.name == "TITLE":
                    item.job.title = child.value

                elif child.name == "X-EVOLUTION-MANAGER":
                    item.job.manager = child.value

                elif child.name == "X-EVOLUTION-ASSISTANT":
                    item.job.assistant = child.value

                elif child.name == "PRO":
                    item.job.profession = child.value

                elif child.name == "ORG":
                    item.job.company = child.value[0]
                    if len(child.value) >= 2:
                        item.job.department = child.value[1]
                    if len(child.value) == 3:
                        item.job.offic = child.value[2]

                elif child.name in ["X-TWITTER", "X-SKYPE"]:
                    item.ims = []
                    im = Database.instantmessaging_model.new()
                    im.username = child.value
                    im.type = child.name.replace("X-", "").capitalize()
                    item.ims.append(im)

            item.save()

            if new:
                collection.items.append(item)
            else:
                idx = [i.contact_id for i in collection.items].index(vobject_item.uid.value)
                collection.items[idx] = item
            collection.save()
            item = Item(
                self, href=href, etag=etag, text=text, item=vobject_item, uid=uid, name=name, component_name=tag
            )
            return item

    def delete(self, href=None):
        if href is None:
            collection = Database.get_collection(self.collection_id, self.user_id)
            collection.delete()
        else:
            items = Database.find_items(item_id=href, collection_id=self.collection_id, user_id=self.user_id)
            if items:
                item = items[0]
                item.delete()
                collection = Database.get_collection(self.collection_id, self.user_id)
                try:
                    collection.items.remove(item)
                except ValueError:
                    idx = -1
                    for i, item in enumerate(collection.items):
                        if item.item_id == href:
                            idx = i
                    if idx != -1:
                        collection.items.pop(idx)
                collection.save()

    def get_meta(self, key=None):
        try:
            if self.collection_id and self.user_id:
                collection = Database.get_collection(collection_id=self.collection_id, user_id=self.user_id)
                self._meta_cache = json.loads(collection.props)
            else:
                self._meta_cache = {}
            check_and_sanitize_props(self._meta_cache)
        except ValueError as e:
            raise RuntimeError("Failed to load properties of collection " "%r: %s" % (self.path, e)) from e
        return self._meta_cache.get(key) if key else self._meta_cache

    def set_meta_all(self, props):
        collection = Database.get_collection(collection_id=self.collection_id, user_id=self.user_id)
        collection.props = json.dumps(props, sort_keys=True)
        collection.save()

    @property
    def last_modified(self):
        return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time()))

    @property
    def etag(self):
        # reuse cached value if the storage is read-only
        if self._etag_cache is None:
            self._etag_cache = super().etag
        return self._etag_cache
