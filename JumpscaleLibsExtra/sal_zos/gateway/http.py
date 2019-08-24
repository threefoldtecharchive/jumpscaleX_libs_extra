from Jumpscale import j
import signal
from .. import templates


class HTTPServer:
    def __init__(self, container, httpproxies):
        self.container = container
        self.httpproxies = httpproxies

    def id(self):
        return self.container.name

    def apply_rules(self):
        # caddy
        caddyconfig = templates.render("caddy.conf", httpproxies=self.httpproxies).strip()
        conf = "/etc/caddy.conf"
        self.container.upload_content(conf, caddyconfig)
        self.container.client.job.kill(self.id(), int(signal.SIGUSR1))
        if caddyconfig == "":
            return
        job = self.container.client.system("caddy -agree -conf {}".format(conf), stdin="\n", id=self.id())
        if j.tools.timer.execute_until(self.is_running, 30, 0.5):
            return True
        if not job.running:
            result = job.get()
            raise j.exceptions.Base(
                "Failed to start caddy server: {} {} {}".format(result.stderr, result.stdout, result.data)
            )
        self.container.client.job.kill(job.id)
        raise j.exceptions.Base("Failed to start caddy server: didnt start listening")

    def is_running(self):
        try:
            self.container.client.job.list(self.id())
        except:
            return False
        portnr = 80
        return self.container.is_port_listening(portnr, 0)
