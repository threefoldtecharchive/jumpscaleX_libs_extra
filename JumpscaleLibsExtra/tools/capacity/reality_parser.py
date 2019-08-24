"""
this module contain the logic of parsing the actual usage of the ressource unit of a zero-os node
"""

from .units import GiB
from sal_zos.disks.Disks import StorageType


class RealityParser:
    def __init__(self):
        self._ressources = {"mru": 0.0, "cru": 0.0, "hru": 0.0, "sru": 0.0}

    def get_report(self, disks, storage_pools, total_cpu_nr, used_cpu, used_memory):
        self._ressources["mru"] = _parse_memory(used_memory)
        self._ressources["cru"] = _parse_cpu(total_cpu_nr, used_cpu)
        storage = _parse_storage(disks, storage_pools)
        self._ressources["sru"] = storage["sru"]
        self._ressources["hru"] = storage["hru"]

        return Report(**self._ressources)


class Report:
    def __init__(self, cru, mru, hru, sru):
        self._cru = round(cru, 2)
        self._mru = round(mru, 2)
        self._hru = round(hru, 2)
        self._sru = round(sru, 2)

    @property
    def CRU(self):
        return self._cru

    @property
    def MRU(self):
        return self._mru

    @property
    def SRU(self):
        return self._sru

    @property
    def HRU(self):
        return self._hru

    def __repr__(self):
        return str(dict(cru=self.CRU, mru=self.MRU, hru=self.HRU, sru=self.SRU))

    __str__ = __repr__


def _parse_storage(disks, storage_pools):

    disk_mapping = {}
    for disk in disks:
        for part in disk.partitions:
            if part.devicename not in disk_mapping:
                disk_mapping[part.devicename] = disk.type

    ressoures = {"sru": 0, "hru": 0}
    for sp in storage_pools:
        if len(sp.devices) <= 0:
            continue

        if sp.mountpoint == "/mnt/storagepools/sp_zos-cache":
            continue

        disk_type = disk_mapping[sp.devices[0]]
        size = sp.fsinfo["data"]["used"]

        if disk_type in [StorageType.HDD, StorageType.ARCHIVE]:
            ressoures["hru"] += size / GiB
        elif disk_type in [StorageType.SSD, StorageType.NVME]:
            ressoures["sru"] += size / GiB
        else:
            raise j.exceptions.Value("disk type %s is not valid" % disk.type.name)

    return ressoures


def _parse_cpu(total_cpu_nr, used_cpu):
    # self._node.client.aggregator.query("machine.CPU.percent")
    cpu_percentages = [value["current"]["3600"]["avg"] for value in used_cpu.values()]
    return (total_cpu_nr * sum(cpu_percentages)) / 100


def _parse_memory(used_memory):
    """
    convert the used memory in bytes to ressource units


    :param used_memory: amount of used memory in bytes
    :type used_memory: float
    :return: number of MRU
    :rtype: float
    """

    return used_memory / GiB
