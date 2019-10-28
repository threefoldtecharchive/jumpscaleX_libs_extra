from Jumpscale import j
from .template import nginx_conf


class TaigaServer(j.baseclasses.object_config):
    _SCHEMATEXT = """
           @url =  jumpscale.taiga.server.1
           name** = "default" (S)
           host = "127.0.0.1" (S)
           port = 4321 (I)
           protocol = "http" (S)
           backend_repo = "https://github.com/taigaio/taiga-back.git" (S)
           frontend_repo = "https://github.com/taigaio/taiga-front-dist.git" (S)
           events_repo = "https://github.com/taigaio/taiga-events.git" (S)
           branch_backend = "stable" (S)
           branch_frontend = "stable" (S)
           branch_events = "master" (S)
           secret_ = "123123" (S)
           """

    def _init(self, **kwargs):
        self.taiga_user = "taiga"
        self.NGINX_LOG_DIR = f"/home/{self.taiga_user}/logs"
        self.backend_repo_dir = j.builders.apps.taiga.backend_repo_dir
        self.frontend_repo_dir = j.builders.apps.taiga.frontend_repo_dir
        self.events_repo_dir = j.builders.apps.taiga.events_repo_dir

    def install(self, reset=False):
        j.builders.apps.taiga.install_deps(reset=reset, rabbitmq_secret=self.secret_)
        j.builders.apps.taiga._backend_install(
            backend_repo=self.backend_repo, rabbitmq_secret=self.secret_, branch=self.branch_backend
        )
        j.sal.fs.createDir(self.NGINX_LOG_DIR)
        j.builders.apps.taiga._frontend_install(
            frontend_repo=self.frontend_repo, host=self.host, port=self.port, branch=self.branch_frontend
        )
        j.builders.apps.taiga._events_install(
            events_repo=self.events_repo, rabbitmq_secret=self.secret_, branch=self.branch_events
        )

    def start(self):
        """

        """
        NGINX_CONF = nginx_conf()
        j.sal.fs.writeFile(
            "/etc/nginx/conf.d/taiga.conf",
            NGINX_CONF
            % {
                "port": self.port,
                "log_dir": self.NGINX_LOG_DIR,
                "back_end": self.backend_repo_dir,
                "front_end": self.frontend_repo_dir,
            },
        )
        j.builders.apps.taiga._execute("nginx -t && service nginx restart")
        for startupcmd in self.startupcmd:
            startupcmd.start()

    def stop(self):
        self._log_info("stop taiga")
        for startupcmd in self.startupcmd:
            startupcmd.stop()

    @property
    def startupcmd(self):
        taiga_startup_cmd = j.servers.startupcmd.get("taiga")
        taiga_startup_cmd.path = f"{self.backend_repo_dir}"
        taiga_startup_cmd.cmd_start = f"su {self.taiga_user} -c '/home/{self.taiga_user}/.virtualenvs/{self.taiga_user}/bin/gunicorn --workers 4 --timeout 60 -b 127.0.0.1:8001 taiga.wsgi'"

        taiga_events = j.servers.startupcmd.get("taiga_events")
        taiga_events.path = f"{self.events_repo}"
        taiga_events.cmd_start = f"""
            su {self.taiga_user} -c 'export PATH=$PATH:/sandbox/bin;cd {self.events_repo_dir}; /bin/bash -c \\"node_modules/coffeescript/bin/coffee index.coffee\\"'
            """

        return [taiga_events, taiga_startup_cmd]
