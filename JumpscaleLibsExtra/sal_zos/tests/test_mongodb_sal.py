"""
This test script executes the following scenario:

    1. On a single ZOS node deploy 3 containers with two running instances of mongod - members of shard server and a config server replica sets. Initialize replica sets.
    2. Create another container with running mongos - MongoDB routing service. Add all data shards.
    3. Create a sample collection on the cluster.
    4. Destroy container with PRYMARY shards
    5. Ensure that new PRYMARY was elected and previously created collection is still avaliable.

"""

import time
import re
import pytest
from Jumpscale import j

FLIST = "https://hub.grid.tf/ekaterina_evdokimova_1/ubuntu-16.04-mongodb.flist"


def error_check(result, message=""):
    """ Raise error if call wasn't successfull """

    if result.state != "SUCCESS":
        err = "{}: {} \n {}".format(message, result.stderr, result.data)
        raise j.exceptions.Base(err)


def get_node(ip):
    """ Get robot instance

    :param ip: IP addres of Zero-os node
    """
    node_id = "local"
    j.clients.zos.get(instance=node_id, data={"host": ip, "port": 6379})
    j.clients.zero_os.sal.get_node(instance=node_id)
    return j.clients.zos.sal.get_node(node_id)


def create_container(name, node):
    # determine parent interface for macvlan
    candidates = list()
    for route in node.client.ip.route.list():
        if route["gw"]:
            candidates.append(route)
    if not candidates:
        raise j.exceptions.Base("Could not find interface for macvlan parent")
    elif len(candidates) > 1:
        raise j.exceptions.Base(
            "Found multiple eligible interfaces for macvlan parent: %s" % ", ".join(c["dev"] for c in candidates)
        )
    parent_if = candidates[0]["dev"]
    return node.containers.create(
        name, flist=FLIST, nics=[{"type": "macvlan", "id": parent_if, "name": "stoffel", "config": {"dhcp": True}}]
    )


def get_mongod_shard_config(shard, port):
    # get new configuration of shard replica set
    cmd = """ mongo --port {}  --eval 'rs.status()' """.format(port)
    result = shard.container.client.system(cmd).get()
    error_check(result)
    names = re.findall(r'"name" : "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', result.stdout)
    roles = re.findall(r'"stateStr" : "\w+"', result.stdout)
    return dict(zip(names, roles))


@pytest.mark.skip(reason="not a unit-test")
def test_deploy_cluster(node_ip, cluster_id):
    """ Test case covers mongodb cluster deployment, connection to mongos,
        check db avaliability after nocking out a PRIMARY node for both shard and config replica sets """

    node = get_node(node_ip)
    shard_nr = 3
    shards = []

    # create storagepool
    storagepool = "zos-cache"
    sp = node.storagepools.get(storagepool)

    config_replica = "confReplica{}".format(cluster_id)
    shard_replica = "shardReplica{}".format(cluster_id)
    config_port = 27018
    shard_port = 27019

    # deploy 3 instances of each replica set
    for idx in range(shard_nr):
        container_name = "mongo-shard-{}-{}".format(cluster_id, idx)

        # ensure filesystem
        sp = node.storagepools.get(storagepool)
        try:
            fs = sp.get(container_name)
        except ValueError:
            fs = sp.create(container_name)

        shard = j.clients.zos.sal.get_mongodb(
            name="mongodb",
            node=node,
            container_name=container_name,
            shard_port=shard_port,
            config_port=config_port,
            shard_replica_set=shard_replica,
            config_replica_set=config_replica,
            shard_mount={"storagepool": storagepool, "fs": container_name, "dir": "/mongo/db"},
            config_mount={"storagepool": storagepool, "fs": container_name, "dir": "/mongo/configdb"},
        )

        shard.start(log_to_file=True)
        assert shard.shard_server.is_running()
        assert shard.config_server.is_running()
        shards.append(shard)

    # init replica sets
    hosts = [shards[0].ip, shards[1].ip]
    config_hosts = ["{}:{}".format(host, config_port) for host in hosts]
    shard_hosts = ["{}:{}".format(host, shard_port) for host in hosts]
    shard.init_replica_sets(config_hosts, shard_hosts)

    # deploy container with mongos
    router_container_name = "mongo-router"
    route_port = 27010
    container = create_container(router_container_name, node)

    router = j.clients.zos.sal.get_mongos(container, port=route_port)
    router.start(config_replica, config_hosts, log_to_file=True)

    start = time.time()
    while True:
        try:
            router.add_shards(shard_replica, shard_hosts)
            break
        except:
            if time.time() > start + 30:
                raise

    # create collection
    test_collection = "testCollection"
    cmd = """mongo --host {}:{} --eval 'db.createCollection("{}")'""".format(router.ip, route_port, test_collection)
    result = container.client.bash(cmd).get()
    error_check(result)

    cmd = """mongo --host %s:%s --eval 'db.%s.insert({product: "item"})'""" % (router.ip, route_port, test_collection)
    result = container.client.bash(cmd).get()
    error_check(result)

    # get configuration of shard replica set
    shard_members = get_mongod_shard_config(shard, shard_port)
    assert len(shard_members) == 3

    # get config on config replica set
    config_members = get_mongod_shard_config(shard, config_port)
    assert len(config_members) == 3

    # break primary node
    shard.destroy()

    # switch to alive shard
    shard = shards[0]

    # get configuration of shard replica set

    start = time.time()
    timeout = 100
    primary_is_up = False
    while time.time() < start + timeout and not primary_is_up:
        time.sleep(1)
        new_shard_members = get_mongod_shard_config(shard, shard_port)
        for member in new_shard_members:
            if new_shard_members[member].find("PRIMARY") != -1:
                primary_is_up = True
                print("time to reassign PRYMARY {} sec".format(time.time() - start))
                break

    assert len(new_shard_members) == 2
    assert primary_is_up

    start = time.time()
    primary_is_up = False
    while time.time() < start + timeout and not primary_is_up:
        time.sleep(1)
        new_config_members = get_mongod_shard_config(shard, config_port)
        for member in new_config_members:
            if new_shard_members[member].find("PRIMARY") != -1:
                print("time to reassign PRYMARY {} sec".format(time.time() - start))
                primary_is_up = True
                break

    assert primary_is_up
    assert len(new_config_members) == 2

    time.sleep(15)
    # fetch collection
    cmd = """mongo --host {}:{} --eval 'db.{}.find()'""".format(router.ip, route_port, test_collection)
    result = container.client.bash(cmd).get()
    error_check(result)

    # check that collection contains previously added item
    assert result.stdout.find('"product" : "item"') != -1

    # clean up
    for shard in shards:
        shard.destroy()
    router.destroy()

    print("test was completed successfully")


if __name__ == "__main__":
    test_deploy_cluster("192.168.122.89", cluster_id="32")
