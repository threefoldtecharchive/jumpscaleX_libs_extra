import pytest
import unittest
import sys
from unittest import mock
from Jumpscale import j


class TestOpencCloudClientFactory(unittest.TestCase):
    @pytest.mark.ssh_factory
    @mock.patch("Jumpscale.clients.openvcloud.Account.Account")
    def test_machine_create_name_empty(self, account):
        from Jumpscale.clients.openvcloud.Space import Space

        with pytest.raises(RuntimeError):
            model = dict()
            model["id"] = 123
            space = Space(account=account, model=model)
            space.machine_create(name=" ", sshkeyname="auto_0")

    @pytest.mark.skip(reason="test need to be reviewed")
    @pytest.mark.ssh_factory
    @mock.patch("Jumpscale.clients.openvcloud.Account.Account")
    @mock.patch("Jumpscale.clients.openvcloud.Machine.Machine")
    def test_machine_create_image_find_id_called(self, account, machine):
        from Jumpscale.clients.openvcloud.Space import Space

        model = dict()
        model["id"] = 123
        space = Space(account=account, model=model)
        space.account.client.api.cloudapi.machines.list = mock.MagicMock(return_value=[{"name": "dummy"}])
        space.image_find_id = mock.MagicMock()
        space._node_set = mock.MagicMock()
        space.machine_create(name="dummy", sshkeyname="auto_0", image="imageName", sizeId="sizeID")

        space.image_find_id.assert_called_with("imageName")

    @pytest.mark.skip(reason="test need to be reviewed")
    @pytest.mark.ssh_factory
    @mock.patch("Jumpscale.clients.openvcloud.Account")
    @mock.patch("Jumpscale.clients.openvcloud.Space.image_find_id")
    @mock.patch("Jumpscale.clients.openvcloud.Space.size_find_id")
    @mock.patch("Jumpscale.clients.openvcloud.Space.machines")
    def test_machine_create_size_id(self, account, a, b, c, d):
        from Jumpscale.clients.openvcloud import Space

        model = dict()
        model["id"] = 123
        space = Space(account=account, model=model)
        space.machine_create(name="dummy", memsize=5, vcpus=5, sshkeyname="auto_0", image="imageName")

        space.size_find_id.assert_called_with(5, 5)

    @pytest.mark.skip(reason="test need to be reviewed")
    @pytest.mark.ssh_factory
    @mock.patch("Jumpscale.clients.openvcloud.Account")
    @mock.patch("Jumpscale.clients.openvcloud.Space.image_find_id")
    @mock.patch("Jumpscale.clients.openvcloud.Space.size_find_id")
    @mock.patch("Jumpscale.clients.openvcloud.Space.machines")
    def test_machine_create_configure_machine(self, account, a, b, c, d):
        from Jumpscale.clients.openvcloud import Space

        model = dict()
        model["id"] = 123
        space = Space(account=account, model=model)
        space.machine_create(name="dummy", sshkeyname="auto_0", sshkeypath="auto_0Path")

        space.configure_machine.assert_called_with(
            machine=space.machines["dummy"], name="dummy", sshkeyname="auto_0", sshkey_path="auto_0Path"
        )

    @pytest.mark.skip(reason="test need to be reviewed")
    @pytest.mark.ssh_factory
    @mock.patch("Jumpscale.clients.openvcloud.Account")
    @mock.patch("Jumpscale.clients.openvcloud.Space.image_find_id")
    @mock.patch("Jumpscale.clients.openvcloud.Space.size_find_id")
    @mock.patch("Jumpscale.clients.openvcloud.Space.machines")
    @mock.patch("Jumpscale.clients.openvcloud.Space.createPortForward")
    @mock.patch("Jumpscale.clients.openvcloud.Space._authorizeSSH")
    def test_machine_create_create_port_forward(self, account, a, b, c, e, d):
        from Jumpscale.clients.openvcloud import Space

        model = dict()
        model["id"] = 123
        space = Space(account=account, model=model)
        space.machine_create(name="dummy", sshkeyname="auto_0", sshkeypath="auto_0Path")

        machine = space.machines["dummy"]
        space.createPortForward.assert_called_with(machine)

    @pytest.mark.skip(reason="test need to be reviewed")
    @pytest.mark.ssh_factory
    @mock.patch("Jumpscale.clients.openvcloud.Account")
    @mock.patch("Jumpscale.clients.openvcloud.Space.image_find_id")
    @mock.patch("Jumpscale.clients.openvcloud.Space.size_find_id")
    @mock.patch("Jumpscale.clients.openvcloud.Space.machines")
    @mock.patch("Jumpscale.clients.openvcloud.Space.createPortForward")
    @mock.patch("Jumpscale.clients.openvcloud.Space._authorizeSSH")
    def test_machine_create_authorize_ssh(self, account, a, b, c, e, d):
        from Jumpscale.clients.openvcloud import Space

        model = dict()
        model["id"] = 123
        space = Space(account=account, model=model)
        space.machine_create(name="dummy", sshkeyname="auto_0", sshkeypath="auto_0Path")

        machine = space.machines["dummy"]
        space._authorizeSSH.assert_called_with(machine=machine, sshkeyname="auto_0", sshkey_path="auto_0Path")
