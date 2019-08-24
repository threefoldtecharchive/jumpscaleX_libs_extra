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
import os
from tempfile import TemporaryDirectory

from radicale import pathutils, storage


class CollectionDeleteMixin:
    def delete(self, href=None):
        if href is None:
            # Delete the collection
            j.sal.bcdbfs.dir_remove(self._filesystem_path)
        else:
            # Delete an item
            if not pathutils.is_safe_filesystem_path_component(href):
                raise pathutils.UnsafePathError(href)
            path = pathutils.path_to_filesystem(self._filesystem_path, href)
            if not j.sal.bcdbfs.is_file(path):
                raise storage.ComponentNotFoundError(href)
            j.sal.bcdbfs.file_remove(path)
            # Track the change
            self._update_history_etag(href, None)
            self._clean_history()
