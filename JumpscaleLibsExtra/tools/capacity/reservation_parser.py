"""
this module contain the logic of parsing the service data of the different primitive
and convert it into ressource units
"""
from .units import GiB, MiB


class ReservationParser:
    def __init__(self):
        self._ressources = {"mru": 0.0, "cru": 0.0, "hru": 0.0, "sru": 0.0}

    def get_report(self, vms, vdisks, gateways):
        for vm in vms:
            for k, v in _parser_vm(vm.data).items():
                self._ressources[k] += v

        for vdisk in vdisks:
            for k, v in _parse_vdisk(vdisk.data).items():
                self._ressources[k] += v

        for gw in gateways:
            for k, v in _parse_gateway(gw.data).items():
                self._ressources[k] += v

        return Report(**self._ressources)


class Report:
    def __init__(self, cru, mru, hru, sru):
        self._cru = round(cru, 2)
        self._mru = round(mru, 2)
        self._hru = hru
        self._sru = sru

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


def _parser_vm(vm_data):
    """
    compute the amount of ressource unit use by the VM service

    :param vm_data: data of a zero-os/0-templates/vm  service
    :type vm_data: dict
    :raises ValueError: if some info are missing in the vm_data
    :return: dict containing the amount of ressource unit used
    :rtype: dict
    """

    for k in ["memory", "cpu"]:
        if k not in vm_data:
            raise j.exceptions.Value("vm_data doesn't contain %s" % k)

    cpu = int(vm_data["cpu"])
    memory = int(vm_data["memory"])

    if memory < 0:
        raise j.exceptions.Value("memory cannot be negative")

    if cpu < 0:
        raise j.exceptions.Value("cpu cannot be negative")

    return {"mru": (memory * MiB) / GiB, "cru": cpu, "hru": 0, "sru": 0}


def _parse_vdisk(disk_data):
    """
    compute the amount of ressource unit use by a vdisk service

    [description]

    :param disk_data: data of a zero-os/0-templates/vdisk service
    :type disk_data: dict
    :raises ValueError: raised if some info are missing in the data or if the disk type is wrong
    :return: dict containing the amount of ressource unit used
    :rtype: dict
    """

    ressource = {"mru": 0, "cru": 0, "hru": 0, "sru": 0}

    for k in ["size", "diskType"]:
        if k not in disk_data:
            raise j.exceptions.Value("disk_data doesn't contain %s" % k)

    if disk_data["diskType"] == "ssd":
        ressource["sru"] = int(disk_data["size"])
    elif disk_data["diskType"] == "hdd":
        ressource["hru"] = int(disk_data["size"])
    else:
        raise j.exceptions.Value("disk type %s is not valid" % disk_data["diskType"])

    return ressource


def _parse_gateway(gw_data):
    """
    compute the amount of ressource unit use by a gateway service

    :return: dict containing the number of ressource unit used
    :rtype: [type]
    """

    return {"hru": 0, "sru": 0, "mru": 0.1, "cru": 0.1}
