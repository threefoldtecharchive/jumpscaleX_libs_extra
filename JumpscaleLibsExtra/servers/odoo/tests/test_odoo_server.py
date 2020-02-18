from Jumpscale import j
import random, requests, uuid
import subprocess, uuid

LOGGER = logger
LOGGER.add("PACKAGE_MANAGER_{time}.log")
skip = j.baseclasses.testtools._skip
odoo_server = j.servers.odoo.get()


def random_string():
    return str(uuid.uuid4())[:10]


def info(message):
    j.tools.logger._log_info(message)


def set_database_data(database):
    database.name = str(uuid.uuid4()).replace("-", "")[1:10]
    database.admin_email = "{}@example.com".format(database.name)
    database.admin_passwd_ = random_string()


def before():
    info("​Install odoo server , and get new instance of it ")
    j.servers.odoo.install()
    odoo_server.start()


def after():
    info(" Stop odoo server.")
    odoo_server.stop()


@skip("https://github.com/threefoldtech/jumpscaleX_builders/issues/50")
def test_01_create_database():
    """
    - ​Install and start odoo server , and get new instance of it . 
    - Create new database.
    - Check that created database exist in databases_list.
    - Check that new data base created successfully.
    - stop odoo server.
    """
    info("Create new database ")
    database = odoo_server.databases.new()
    set_database_data(database)
    odoo_server.databases_create()
    odoo_server.save()

    info("Check that created database exist in databases_list.")
    databases = odoo_server.databases_list()
    assert database.name in databases

    info("Check that new database created successfully.")
    database_client = odoo_server.client_get(database.name)
    user_name = random_string()
    user_password = random_string()
    database_client.user_add(user_name, user_password)
    database_client.login(user_name, user_password)
    wrong_passsword = random_string()
    try:
        database_client.login(user_name, wrong_passsword)
        raise "error should be raised "
    except Exception as e:
        info("error raised {}".format(e))

    database_client.user_delete(user_name, user_password)
    try:
        database_client.login(user_name, user_password)
        raise "error should be raised "
    except Exception as e:
        info("error raised {}".format(e))

    info(" stop odoo server.")
    odoo_server.stop()


@skip("https://github.com/threefoldtech/jumpscaleX_builders/issues/50")
def test02_create_databases():
    """
    - ​Install and start odoo server , and get new instance of it . 
    - Create database [db1].
    - Create second database [db2] with reset=false, should create another database only..
    - Create another database [db3] with reset =true, should delete all old databases and create another one.
    """
    info("Create database [db1].")
    db1 = odoo_server.databases.new()
    set_database_data(db1)
    odoo_server.databases_create()
    odoo_server.save()

    info("Create second database [db2] with reset=false, should create another database only.")
    db2 = odoo_server.databases.new()
    set_database_data(db2)
    odoo_server.databases_create(reset=False)
    odoo_server.save()
    assert db1.name in odoo_server.databases_list()
    assert db2.name in odoo_server.databases_list()

    info("Create another database [db3] with reset =true, should delete all old databases and create another one.")
    db3 = odoo_server.databases.new()
    set_database_data(db3)
    odoo_server.databases_create(reset=True)
    odoo_server.save()
    assert db1.name not in odoo_server.databases_list()
    assert db2.name not in odoo_server.databases_list()
    assert db3.name in odoo_server.databases_list()


@skip("https://github.com/threefoldtech/jumpscaleX_builders/issues/50")
def test03_reset_databases(self):
    """
    - ​Install and start odoo server , and get new instance of it . 
    - Try reset_database, should delete all databases.
    """
    info("Create database.")
    db = odoo_server.databases.new()
    set_database_data(db)
    odoo_server.databases_create()
    odoo_server.save()

    info("Try reset_database, should delete all databases.")
    odoo_server.databases_reset()
    assert odoo_server.databases_list() == []


@skip("https://github.com/threefoldtech/jumpscaleX_builders/issues/50")
def test04_export_import_databases(self):
    """
    - ​Install and start odoo server , and get new instance of it . 
    - Export created database, check that zip file exist.
    - Import database, check that imported database exist in database list
    """
    info("Create database.")
    db = odoo_server.databases.new()
    set_database_data(db)
    odoo_server.databases_create()
    odoo_server.save()

    info("Export created database, check that zip file exist.")
    export_dir = "/root/exports/"
    result = j.sal.process.execute("mkdir {}".format(export_dir))
    odoo_server.database_export(db.name, export_dir)
    result = j.sal.process.execute(" ls /root/exports")
    assert "{}.zip".format(db.name) in result[1]

    info("Import database, check that imported database exist in database list")
    odoo_server.databases_reset()
    odoo_server.database_import(db.name, export_dir)
    assert db.name in odoo_server.databases_list()


@skip("https://github.com/threefoldtech/jumpscaleX_builders/issues/50")
def test05_write_and_read(self):
    """
    - ​Install and start odoo server , and get new instance of it .
    - Create database [db].
    - Wrtie data[dt] in [db], check that it writes successfully.
    - Export data [dt].
    - Import data [dt].
    - Read data [dt] from db [db].
    - Delete data [dt], check it deleted successfully.
    """
    pass

