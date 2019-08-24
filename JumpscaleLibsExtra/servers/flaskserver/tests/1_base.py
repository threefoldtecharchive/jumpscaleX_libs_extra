from Jumpscale import j


def main(self):
    """
    to run:

    kosmos 'j.servers.web.test(name="base")'

    """

    ws = j.servers.web.configure("test")

    # link to blueprints dir in tests
    ws.path_blueprints = "%s/tests/blueprints" % self._dirpath

    ws.start()

    j.shell()

    self._log_info("TEST DONE")

    return "OK"
