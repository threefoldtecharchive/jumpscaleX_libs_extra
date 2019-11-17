import os
from Jumpscale import j
import requests

JSConfigClient = j.baseclasses.object_config


class OdooServer(JSConfigClient):
    _SCHEMATEXT = """
           @url =  jumpscale.odoo.server.1
           name** = "default" (S)
           host = "127.0.0.1" (S)
           port = 8069 (I)
           admin_login = "admin"(S)
           admin_passwd_ = "admin" (S)
           admin_email = "info@example.com" (S)
           db_login = "odoouser"
           db_passwd_ = "admin"            
           databases = (LO) !jumpscale.odoo.server.db.1
           
           @url =  jumpscale.odoo.server.db.1
           name** = "odoo_test" (S)
           admin_email = "info@example.com" (S)                      
           admin_passwd_ = "123456" (S)
           country_code = "be"
           lang="en_US"
           phone = "0100425887"
           
           """

    def _init(self, **kwargs):
        self._config_path = j.sal.fs.joinPaths(j.dirs.CFGDIR, "odoo_config_%s.conf" % self.name)
        if self.host == "localhost":
            self.host = " 127.0.0.1"
        self._client = None

    @property
    def client(self):
        if not self._client:
            self._client = j.clients.odoo.get(
                name=self.name, host=self.host, port=self.port, login_admin=self.admin_login, password_=self.db_passwd_
            )
        return self._client

    @property
    def _path(self):
        p = "%s/odoo_db/%s" % (j.core.myenv.config["DIR_VAR"], self.name)
        j.sal.fs.createDir(p)
        return p

    def _write_config(self):
        if j.sal.fs.exists(self._config_path):
            return
        db = self.databases.new()
        C = """
        [options]
        admin_passwd = {admin_passwd_}
        db_host = {host}
        db_user = {db_login}
        db_password = {db_passwd_}
        port = {port}
        email_from = "{admin_email}"
        """
        args = self._data._ddict
        j.sal.fs.writeFile(self._config_path, j.core.tools.text_replace(C, args=args, text_strip=True))
        j.sal.fs.copyFile(self._config_path, j.core.tools.text_replace("{DIR_BASE}/cfg/odoo.conf"))

    def client_get(self, name):
        db = self._database_obj_get(name)
        cl = j.clients.odoo.get(
            name=db.name,
            host=self.host,
            port=self.port,
            login_admin=db.admin_email,
            password_=db.admin_passwd_,
            database=db.name,
        )
        cl.save()
        return cl

    def databases_reset(self, db_name=None):
        """
        remove all databases
        :return:
        """
        API_DROP = "http://{}:{}/web/database/drop".format(self.host, self.port)
        res = None
        if db_name:
            db = self._database_obj_get(db_name)
            data = {"master_pwd": self.admin_passwd_, "name": db_name}
            res = requests.post(url=API_DROP, data=data)
        else:
            for db in self.databases:
                data = {"master_pwd": self.admin_passwd_, "name": db.name}
                res = requests.post(url=API_DROP, data=data)
        return res

    def databases_list(self):
        """
        list databases from postgresql
        :return:
        """
        if j.builders.db.psql.running():
            res = j.sal.process.execute('psql -h localhost -U postgres --command="SELECT datname FROM pg_database;"')
            if res:
                return res[1].replace(" ", "").split("\n")[2:-3]
        else:
            raise j.exceptions.Base(
                "postgres is not running! To run postgres and odoo servers : \n j.servers.odoo.default.start()"
            )

    def databases_create(self, reset=False):
        """
        remove the database if reset=True
        create db in postgresql
        set admin passwd

        :return:
        """
        if reset:
            self.databases_reset()
        if self.databases == []:
            self.databases.new()
        for db in self.databases:
            API_CREATE = "http://{}:{}/web/database/create".format(self.host, self.port)
            data = {
                "master_pwd": self.db_passwd_,
                "name": db.name,
                "login": db.admin_email,
                "password": db.admin_passwd_,
                "phone": db.phone,
                "lang": db.lang,
                "country_code": db.country_code,
            }
            res = requests.post(url=API_CREATE, data=data)
            if b"already exists" in res.content:
                self._log_warning("db:%s exists" % db.name)

    def _database_obj_get(self, name):
        name = name.lower()
        for db in self.databases:
            if db.name == name:
                return db
        raise j.exceptions.Base("could not find database :%s" % name)

    def database_export(self, name, dest=None):
        db = self._database_obj_get(name)
        BACKUP_API = "http://{}:{}/web/database/backup".format(self.host, self.port)
        data = {"master_pwd": db.db_secret_, "name": name, "backup_format": "zip"}
        res = requests.post(url=BACKUP_API, data=data, stream=True)
        if not dest:
            dest = j.core.tools.text_replace("{DIR_VAR}/odoo/exports/%s" % db.name)
            j.sal.fs.createDir(dest)

        with open(dest + "%s.zip" % name, "wb") as f:
            for c in res.iter_content():
                f.write(c)
        return dest + "%s.zip" % name

    def database_import(self, name, dest=None):
        db = self._database_obj_get(name)
        IMPORT_API = "http://{}:{}/web/database/restore".format(self.host, self.port)

        if not dest:
            dest = j.core.tools.text_replace("{DIR_VAR}/odoo/exports/%s" % db.name)
            dest += "%s.zip" % name
            # CHECK DIR EXISTS
            # look for newest one
        data = {"master_pwd": db.db_secret_, "backup_file": dest, "name": name, "copy": False}
        res = requests.post(url=IMPORT_API, data=data)
        return res

    def start(self):
        """
        Starts odoo server in tmux
        """
        self._write_config()
        j.builders.db.psql.start()
        if self.databases == []:
            db = self.databases.new()
            db.admin_email = self.admin_login
            db.admin_passwd_ = self.admin_passwd_
            self.save()
        else:
            db = self.databases[0]
        cl = j.clients.postgres.db_client_get(dbname=db.name)
        j.builders.apps.odoo.set_dbname(db.name)
        j.sal.process.execute(
            """psql -h localhost -U postgres \
                --command="CREATE TABLE IF NOT EXISTS initialize_table (available boolean);" """
        )
        search = j.sal.process.execute(
            """psql -h localhost -U postgres \
                --command="SELECT * FROM initialize_table WHERE available = 'yes';" """
        )
        if int(search[1].split("\n")[-3].split(" ")[0].split("(")[1]) > 0:
            odoo_start = j.builders.apps.odoo._replace(
                "sudo -H -u odoouser python3 {DIR_BASE}/apps/odoo/odoo/odoo-bin -c {DIR_CFG}/odoo.conf"
            )
        else:
            odoo_start = j.builders.apps.odoo._replace(
                "sudo -H -u odoouser python3 {DIR_BASE}/apps/odoo/odoo/odoo-bin -c {DIR_CFG}/odoo.conf -d %s -i base"
                % db.name
            )
            j.sal.process.execute(
                """psql -h localhost -U postgres \
                --command='INSERT INTO initialize_table (available) VALUES (TRUE);' """
            )

        odoo_cmd = j.servers.startupcmd.get("odoo")
        odoo_cmd.cmd_start = odoo_start

        odoo_cmd.process_strings = j.core.tools.text_replace("{DIR_BASE}/apps/odoo/odoo/odoo-bin -c")
        odoo_cmd.path = j.core.tools.text_replace("{DIR_BASE}/bin")
        odoo_cmd.ports = [8069]

        self._log_info("start odoo server")
        odoo_cmd.start()

    def stop(self):
        self._log_info("stop odoo server and postgresql")
        if not j.core.tools.cmd_installed("postgres"):
            j.builders.db.psql.install()

        odoo_cmd = j.servers.startupcmd.get("odoo")
        odoo_cmd.stop()
        j.builders.db.psql.stop()


