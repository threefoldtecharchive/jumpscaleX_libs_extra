# This file is part of Radicale Server - Calendar Server
# Copyright © 2014 Jean-Marc Martins
# Copyright © 2012-2017 Guillaume Ayoub
# Copyright © 2017-2018 Unrud <unrud@outlook.com>
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
import contextlib
import os
import posixpath

from radicale import pathutils
from radicale.log import logger


class CollectionDiscoverMixin:
    @classmethod
    def discover(cls, path, depth="0", child_context_manager=(lambda path, href=None: contextlib.ExitStack())):
        # Path should already be sanitized
        sane_path = pathutils.strip_path(path)
        attributes = sane_path.split("/") if sane_path else []

        folder = cls._get_collection_root_folder()
        # Create the root collection
        cls._makedirs_synced(folder)
        try:
            filesystem_path = pathutils.path_to_filesystem(folder, sane_path)
        except ValueError as e:
            # Path is unsafe
            logger.debug("Unsafe path %r requested from storage: %s", sane_path, e, exc_info=True)
            return

        # Check if the path exists and if it leads to a collection or an item
        if not j.sal.bcdbfs.is_dir(filesystem_path):
            if attributes and j.sal.bcdbfs.is_file(filesystem_path):
                href = attributes.pop()
            else:
                return
        else:
            href = None

        sane_path = "/".join(attributes)
        collection = cls(pathutils.unstrip_path(sane_path, True))

        if href:
            yield collection._get(href)
            return

        yield collection

        if depth == "0":
            return

        for href in collection._list():
            with child_context_manager(sane_path, href):
                yield collection._get(href)

        for entry in j.sal.bcdfs.list_files_and_dirs(filesystem_path):
            if not j.sal.bcdfs.is_dir(entry):
                continue
            import ntpath

            href = ntpath.basename(entry)
            if not pathutils.is_safe_filesystem_path_component(href):
                if not href.startswith(".Radicale"):
                    logger.debug("Skipping collection %r in %r", href, sane_path)
                continue
            sane_child_path = posixpath.join(sane_path, href)
            child_path = pathutils.unstrip_path(sane_child_path, True)
            with child_context_manager(sane_child_path):
                yield cls(child_path)
