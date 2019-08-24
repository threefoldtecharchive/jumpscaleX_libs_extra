from .Minio import Minio
import pytest


def test_replication_config():

    m = Minio(
        "aminio",
        None,
        "admin",
        "admin",
        ["localhost:9999"],
        "anamespace",
        "myprivatekeystring",
        node_port=9000,
        namespace_secret="nssecret",
        nr_datashards=6,
        nr_parityshards=0,
    )
    conf = m._config_as_text()
    expected = """\
namespace: anamespace
password: nssecret
datastor: # required
  shards: # required
    - localhost:9999
  pipeline:
    block_size: 1048576
    compression: # optional, snappy by default
      type: snappy # snappy is the default, other options: lz4, gzip
      mode: default # default is the default, other options: best_speed, best_compression
    encryption: # optional, disabled by default
      type: aes # aes is the default and only standard option
      private_key: myprivatekeystring
    distribution:
      data_shards: 6"""
    assert expected == conf
    assert m.mode == "replication"


def test_distribution_config():
    m = Minio(
        "aminio",
        None,
        "admin",
        "admin",
        ["localhost:9999"],
        "anamespace",
        "myprivatekeystring",
        node_port=9000,
        namespace_secret="nssecret",
        nr_datashards=6,
        nr_parityshards=4,
    )
    conf = m._config_as_text()
    expected = """\
namespace: anamespace
password: nssecret
datastor: # required
  shards: # required
    - localhost:9999
  pipeline:
    block_size: 1048576
    compression: # optional, snappy by default
      type: snappy # snappy is the default, other options: lz4, gzip
      mode: default # default is the default, other options: best_speed, best_compression
    encryption: # optional, disabled by default
      type: aes # aes is the default and only standard option
      private_key: myprivatekeystring
    distribution:
      data_shards: 6
      parity_shards: 4"""
    assert expected == conf
    assert m.mode == "distribution"


def test_tlog_config():
    m = Minio(
        "aminio",
        None,
        "admin",
        "admin",
        ["localhost:9999"],
        "anamespace",
        "myprivatekeystring",
        node_port=9000,
        namespace_secret="nssecret",
        nr_datashards=6,
        nr_parityshards=4,
        tlog_namespace="tlogns",
        tlog_address="ip:port",
    )
    conf = m._config_as_text()
    expected = """\
namespace: anamespace
password: nssecret
datastor: # required
  shards: # required
    - localhost:9999
  pipeline:
    block_size: 1048576
    compression: # optional, snappy by default
      type: snappy # snappy is the default, other options: lz4, gzip
      mode: default # default is the default, other options: best_speed, best_compression
    encryption: # optional, disabled by default
      type: aes # aes is the default and only standard option
      private_key: myprivatekeystring
    distribution:
      data_shards: 6
      parity_shards: 4
minio:
  tlog:
    address: ip:port
    namespace: tlogns
    password: nssecret"""
    assert expected == conf


def test_master_config():
    m = Minio(
        "aminio",
        None,
        "admin",
        "admin",
        ["localhost:9999"],
        "anamespace",
        "myprivatekeystring",
        node_port=9000,
        namespace_secret="nssecret",
        nr_datashards=6,
        nr_parityshards=4,
        master_namespace="masterns",
        master_address="ip:port",
    )
    conf = m._config_as_text()
    expected = """\
namespace: anamespace
password: nssecret
datastor: # required
  shards: # required
    - localhost:9999
  pipeline:
    block_size: 1048576
    compression: # optional, snappy by default
      type: snappy # snappy is the default, other options: lz4, gzip
      mode: default # default is the default, other options: best_speed, best_compression
    encryption: # optional, disabled by default
      type: aes # aes is the default and only standard option
      private_key: myprivatekeystring
    distribution:
      data_shards: 6
      parity_shards: 4
minio:
  master:
    address: ip:port
    namespace: masterns
    password: nssecret"""
    assert expected == conf


def test_master_and_tlog_config():
    m = Minio(
        "aminio",
        None,
        "admin",
        "admin",
        ["localhost:9999"],
        "anamespace",
        "myprivatekeystring",
        node_port=9000,
        namespace_secret="nssecret",
        nr_datashards=6,
        nr_parityshards=4,
        master_namespace="masterns",
        master_address="ip:port",
        tlog_namespace="tlogns",
        tlog_address="ip:port",
    )
    conf = m._config_as_text()
    expected = """\
namespace: anamespace
password: nssecret
datastor: # required
  shards: # required
    - localhost:9999
  pipeline:
    block_size: 1048576
    compression: # optional, snappy by default
      type: snappy # snappy is the default, other options: lz4, gzip
      mode: default # default is the default, other options: best_speed, best_compression
    encryption: # optional, disabled by default
      type: aes # aes is the default and only standard option
      private_key: myprivatekeystring
    distribution:
      data_shards: 6
      parity_shards: 4
minio:
  tlog:
    address: ip:port
    namespace: tlogns
    password: nssecret
  master:
    address: ip:port
    namespace: masterns
    password: nssecret"""
    assert expected == conf
