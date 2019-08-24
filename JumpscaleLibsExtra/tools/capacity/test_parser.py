import os
from unittest import TestCase

import pytest

from Jumpscale import j

# commented out this import since sal_zos is not ported to jumpscalex, once it is
# we need to enable the import and enable the tests as well.
# from .capacity_parser import CapacityParser
from .reservation_parser import ReservationParser, _parser_vm, _parse_vdisk


class TestParser(TestCase):
    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.data1 = j.sal.fs.readFile(os.path.join(dirname, "dmidecode1.txt"))
        self.data2 = j.sal.fs.readFile(os.path.join(dirname, "dmidecode2.txt"))
        self.memory = 1024 ** 3
        self.parser = CapacityParser()

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_has_keys(self):
        hwdata = self.parser.hw_info_from_dmi(self.data1)
        self.assertIn("0x0000", hwdata)
        self.assertIn("0x0001", hwdata)

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def get_report(self, data):
        hwdata = self.parser.hw_info_from_dmi(data)
        return self.parser.get_report(self.memory, hwdata, {})

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_report_data1(self):
        report = self.get_report(self.data1)
        self.assertEqual(report.CRU, 8, "Something wrong when parsing CPU data")
        self.assertEqual(report.MRU, 1, "Something wrong when parsing Memory data")

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_report_data2(self):
        report = self.get_report(self.data2)
        self.assertEqual(report.CRU, 4, "Something wrong when parsing CPU data")
        self.assertEqual(report.MRU, 1, "Something wrong when parsing Memory data")

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_report_motherboard(self):
        report = self.get_report(self.data1)
        self.assertEqual(report.motherboard[0]["serial"], "W1KS42E13PU", "Failed to parse serial")


class TestReservedParser(TestCase):
    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_parse_vm_valid(self):
        with self.subTest():
            assert _parser_vm({"cpu": 1, "memory": 128}) == {"mru": 0.125, "cru": 1, "hru": 0, "sru": 0}

        with self.subTest():
            assert _parser_vm({"cpu": 10, "memory": 1024}) == {"mru": 1, "cru": 10, "hru": 0, "sru": 0}

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_parse_vm_cpu_negative(self):
        vm_data = {"cpu": -1, "memory": 128}
        with pytest.raises(TypeError, message="negative cpu should raise j.exceptions.Value"):
            ressources = _parser_vm(vm_data)

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_parse_vm_memory_negative(self):
        vm_data = {"cpu": 1, "memory": -512}
        with pytest.raises(TypeError, message="negative memory should raise j.exceptions.Value"):
            ressources = _parser_vm(vm_data)

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_parse_vdisk_valid(self):
        assert _parse_vdisk({"size": 10, "diskType": "ssd"}) == {"mru": 0, "cru": 0, "hru": 0, "sru": 10}

        assert _parse_vdisk({"size": 10, "diskType": "hdd"}) == {"mru": 0, "cru": 0, "hru": 10, "sru": 0}

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_parse_vdisk_wrong_type(self):
        with pytest.raises(ValueError):
            _parse_vdisk({"size": 10, "diskType": "usb"})

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_parser_get_report_simple(self):
        parser = ReservationParser()
        vms = [{"cpu": 1, "memory": 1024}]
        vdisks = [{"size": 10, "diskType": "ssd"}]
        gateways = [{}]
        report = parser.get_report(vms, vdisks, gateways)
        assert report.MRU == 1.1
        assert report.CRU == 1.1
        assert report.HRU == 0
        assert report.SRU == 10.0

    @pytest.mark.skip(reason="Importing CapacityParser is failing")
    def test_parser_get_report_multi(self):
        parser = ReservationParser()
        vms = [{"cpu": 1, "memory": 1024}, {"cpu": 2, "memory": 2048}, {"cpu": 1, "memory": 2048}]
        vdisks = [{"size": 10, "diskType": "ssd"}, {"size": 50, "diskType": "hdd"}, {"size": 1000, "diskType": "hdd"}]
        gateways = [{}, {}, {}]
        report = parser.get_report(vms, vdisks, gateways)
        assert report.MRU == 5.3
        assert report.CRU == 4.3
        assert report.HRU == 1050.0
        assert report.SRU == 10.0
