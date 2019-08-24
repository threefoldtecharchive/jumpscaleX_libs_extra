from Jumpscale import j

JSBASE = j.baseclasses.object


from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class MyFileSystemEventHandler(FileSystemEventHandler, JSBASE):
    def __init__(self):
        JSBASE.__init__(self)

        if j.tools.develop.node_active is not None:
            self.nodes = [j.tools.develop.node_active]
        else:
            self.nodes = j.tools.develop.nodes.getall()

    def handler(self, event, action="copy"):
        self._log_debug("%s:%s" % (event, action))
        changedfile = event.src_path
        if event.is_directory:
            if changedfile.find("/.git") != -1:
                return
            elif changedfile.find("/__pycache__/") != -1:
                return
            elif changedfile.find(".egg-info") != -1:
                return
            if event.event_type == "modified":
                return
            j.tools.develop.sync()
        else:
            error = False
            for node in self.nodes:
                if node.selected == False:
                    continue
                if error is False:
                    if changedfile.find("/.git/") != -1:
                        return
                    elif changedfile.find("/__pycache__/") != -1:
                        return
                    elif changedfile.endswith(".pyc"):
                        return
                    else:
                        destpart = changedfile.split("code/", 1)[-1]
                        dest = j.sal.fs.joinPaths(node.prefab.core.dir_paths["CODEDIR"], destpart)
                    e = ""
                    if action == "copy":
                        self._log_debug("copy: %s %s:%s" % (changedfile, node, dest))
                        try:
                            node.sftp.put(changedfile, dest)
                        except Exception as e:
                            self._log_debug("** ERROR IN COPY, WILL SYNC ALL")
                            self._log_debug(str(e))
                            error = True
                    elif action == "delete":
                        self._log_debug("delete: %s %s:%s" % (changedfile, node, dest))
                        try:
                            node.sftp.remove(dest)
                        except Exception as e:
                            if "No such file" in str(e):
                                return
                            else:
                                error = True
                                # raise j.exceptions.Base(e)
                    else:
                        raise j.exceptions.RuntimeError(
                            "action not understood in filesystemhandler on sync:%s" % action
                        )

                if error:
                    try:
                        self._log_debug(e)
                    except BaseException:
                        pass
                    node.sync()
                    error = False

    def on_moved(self, event):
        j.tools.develop.sync()
        self.handler(event, action="delete")

    def on_created(self, event):
        self.handler(event)

    def on_deleted(self, event):
        self.handler(event, action="delete")

    def on_modified(self, event):
        self.handler(event)
