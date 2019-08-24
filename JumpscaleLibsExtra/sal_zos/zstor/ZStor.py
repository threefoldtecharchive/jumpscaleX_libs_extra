import logging
import time

logging.basicConfig(level=logging.INFO)


class ZeroStor:
    """zerostor server"""

    def __init__(
        self, name, container, bind="0.0.0.0:8080", data_dir="/mnt/data", meta_dir="/mnt/metadata", max_size_msg=64
    ):

        self.name = name
        self.container = container
        self.bind = bind
        self.data_dir = data_dir
        self.meta_dir = meta_dir
        self.max_size_msg = max_size_msg
        self._ays = None
        self._job_id = "zerostor.{}".format(self.name)

    def stop(self, timeout=30):
        if not self.container.is_running():
            return

        is_running, job = self.is_running()
        if not is_running:
            return

        j.tools.logger._log_debug("stop %s", self)

        self.container.client.job.kill(job["cmd"]["id"])

        # wait for StorageEngine to stop
        start = time.time()
        end = start + timeout
        is_running, _ = self.is_running()
        while is_running and time.time() < end:
            time.sleep(1)
            is_running, _ = self.is_running()

        if is_running:
            raise j.exceptions.Base("zerostor server {} didn't stopped")

    def start(self):
        cmd = '/bin/zerostorserver \
            --bind {bind} \
            --data "{datadir}" \
            --meta "{metadir}" \
            --max-msg-size {msgsize} \
            --async-write \
            '.format(
            bind=self.bind, datadir=self.data_dir, metadir=self.meta_dir, msgsize=self.max_size_msg
        )
        self.container.client.system(cmd, id=self._job_id)
        start = time.time()
        while start + 15 > time.time():
            if self.container.is_port_listening(int(self.bind.split(":")[1])):
                break
            time.sleep(1)
        else:
            raise j.exceptions.Base("Failed to start zerostor server: {}".format(self.name))

    def is_running(self):
        return self.container.is_job_running(self._job_id)
