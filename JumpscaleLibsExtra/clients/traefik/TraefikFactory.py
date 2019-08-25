from Jumpscale import j

from .TraefikClient import Backend, BackendServer, Frontend, FrontendRule, TraefikClient

JSConfigBaseFactory = j.baseclasses.object_config_collection


class TraefikFactory(JSConfigBaseFactory):
    __jslocation__ = "j.clients.traefik"
    _CHILDCLASS = TraefikClient

    def get(
        self,
        name=None,
        id=None,
        die=True,
        create_new=True,
        childclass_name=None,
        host="127.0.0.1",
        port=2379,
        user="root",
        password="root",
        **kwargs,
    ):
        """Get Traefik client instance after getting an etcd client instance 
            If client found with name in param 'etcd_instance' , the client instance is used. Otherwise a new etcd client instance is created

        :param name: traefik client name, defaults to None
        :type name: str
        :param id: id of the obj to find, is a unique id
        :param name: of the object, can be empty when searching based on id or the search criteria (kwargs)
        :param search criteria (if name not used) or data elements for the new one being created
        :param die, means will give error when object not found
        :param create_new, if True it will automatically create a new one
        :param childclass_name, if different typen of childclass, specify its name, needs to be implemented in _childclass_selector
        :param etcd_instance: etcd client instance name, defaults to "main"
        :type etcd_instance: str
        :param host: etcd host IPAddress, defaults to "127.0.0.1"
        :type host: str (ipaddr in schema), optional
        :param port: etcd port, defaults to "2379"
        :type port: str (ipport in schema), optional
        :param user: etcd user, defaults to "root"
        :type user: str, optional
        :param password: etcd password, defaults to "root"
        :type password: str, optional
        :return: Traefik client
        :rtype: Traefik
        """
        if "etcd_instance" not in kwargs:
            raise j.exceptions.Value("New or existing etcd_instance name required")
        j.clients.etcd.get(name=kwargs["etcd_instance"], host=host, port=port, user=user, password_=password)
        return JSConfigBaseFactory.get(
            self, name=name, id=id, die=die, create_new=create_new, childclass_name=childclass_name, **kwargs
        )

    def test(self, build=False):

        if build:

            # check is ubuntu 1804
            # build etcd
            # start etcd

            raise j.exceptions.Base("not implemented")

        # make client connection to it

        cl = self.get(name="traefik_test", etcd_name="traefik_test_etcd", user="root", password="v16ffehxnq")

        # create a proxy object. A proxy has a name and is combination of frontends and backends
        proxy = cl.proxy_create("myproxy")

        # set a backend on your proxy
        backend = proxy.backend_set(endpoints=["http://192.168.1.5:8080"])
        # add another server to your backend
        server = backend.server_add("http://192.168.1.15:8080")
        # set the weight for the load balancing on the second backend server
        server.weight = "20"

        # set a frontend on your proxy
        frontend = proxy.frontend_set("my.domain.com")

        # write the configuration into etcd
        proxy.deploy()
        # delete all frontend and backend configuration of this proxy from etcd
        proxy.delete()
