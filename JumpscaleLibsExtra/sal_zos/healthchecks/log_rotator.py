import datetime
import os
import re

from .healthcheck import HealthCheckRun


descr = """
Rotate know log files if their size hit 10G or more
"""


class RotateLogs(HealthCheckRun):
    def __init__(self, node):
        resource = "/nodes/{}".format(node.node_id)
        super().__init__("log-rotator", "Log Rotator", "System Load", resource)
        self.node = node

    def run(self, locations=["/var/log"], limit=10):
        message = {"id": "log-rotator", "status": "OK", "text": "Logs did not reach {limit}G".format(limit=limit)}

        if "/var/log" not in locations:
            locations.append("/var/log")
        logs = []
        try:
            # Get total size for all log files
            log_size = get_log_size(self.node, locations)

            # Rotate logs if they are larger than the limit
            if log_size / (1024 * 1024 * 1024) >= limit:  # convert bytes to GIGA
                # Rotate core.log

                for location in locations:
                    # Get Files for this location
                    location_files = get_files(self.node, location, [])
                    logs.extend(location_files)

                for file_path in logs:
                    if file_path == "/var/log/core.log":
                        continue
                    # Delete old rotated files to free up some space
                    # match file.*.date.time
                    if re.match(".*\d{8}-\d{6}", file_path):
                        self.node.client.filesystem.remove(file_path)
                    else:
                        new_path = "%s.%s" % (file_path, datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
                        # Rotate the new logs
                        self.node.client.filesystem.move(file_path, new_path)
                        # Create a new EMPTY file with the same name
                        fd = self.node.client.filesystem.open(file_path, "x")
                        self.node.client.filesystem.close(fd)
                self.node.client.logger.reopen()
                message["text"] = "Logs cleared"
        except Exception as e:
            message["text"] = "Error happened, Can not clear logs"
            message["status"] = "ERROR"

        self.add_message(**message)


def get_files(node, location, files=[]):
    for item in node.client.filesystem.list(location):
        if not item["is_dir"]:
            files.append(os.path.join(location, item["name"]))
        else:
            files = get_files(node, os.path.join(location, item["name"]), files)
    return files


def get_log_size(node, locations):
    size = 0
    for location in locations:
        items = node.client.filesystem.list(location)
        for item in items:
            size += item["size"]
    return size
