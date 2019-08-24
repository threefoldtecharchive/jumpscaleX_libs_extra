import json
import re as _re
from enum import Enum

import requests

from sal_zos.disks.Disks import StorageType

from .units import GB, GiB

# regex for _parse_dmi
_handle_re = _re.compile("^Handle\\s+(.+),\\s+DMI\\s+type\\s+(\\d+),\\s+(\\d+)\\s+bytes$")
_in_block_re = _re.compile("^\\t\\t(.+)$")
_record_re = _re.compile("\\t(.+):\\s+(.+)$")
_record2_re = _re.compile("\\t(.+):$")


class CapacityParser:
    def disk_info_from_smartctl(self, smartctl_data, disk_size, disk_type):
        """
        Parses smartctl output of a disk to disk_info

        @param devicename: name of the disk device
        @param smartctl_data: output from smartctl
        @param disk_size: size of disk
        @param disk_type: type of disk (StorageType)

        @return disk_info of the disk
        """

        disk_info = _parse_smarctl(smartctl_data)
        disk_info["size"] = disk_size
        disk_info["type"] = disk_type

        return disk_info

    def hw_info_from_dmi(self, dmi_data):
        """
        Parses dmi to hw_info

        @param dmi_data: output of dmi

        @return hw_info
        """
        return _parse_dmi(dmi_data)

    def get_report(self, total_mem, hw_info, disk_info, indent=None):
        """
        Takes in hardware info and parses it into a report

        @param total_mem: total memory of the system in bytes
        @param hw_info: hardware information
        @param disk_info: disk information

        @return Report of the capacity
        """
        return Report(total_mem, hw_info, disk_info, indent=indent)


class Report:
    """
        Report takes in hardware information and parses it into a report.
    """

    def __init__(self, total_mem, hw_info, disk_info, indent=None):
        """
        @param total_mem: total system memory in bytes
        @param hw_info: hardware information
        @param disk_info: disk information
        """
        self._total_mem = total_mem
        self.processor = _cpu_info(hw_info)
        self.memory = _memory_info(hw_info)
        self.motherboard = _mobo_info(hw_info)
        self.disk = _disks_info(disk_info)

        # json indent for pretty printing
        self.indent = indent

    @property
    def CRU(self):
        """
        return the number of core units
        """
        unit = 0
        for cpu in self.processor:
            if cpu["thread_nr"]:
                unit += int(cpu["thread_nr"])
            elif cpu["core_nr"]:
                unit += int(cpu["core_nr"])
            else:
                # when no thread_nr or core_nr is available we assume it's a single core/thread processor
                unit += 1
        return unit

    @property
    def location(self):
        resp = requests.get("http://geoip.nekudo.com/api/en/full")
        location = None
        if resp.status_code == 200:
            data = resp.json()
            location = dict(
                continent=data.get("continent", {}).get("names", {}).get("en", "Unknown"),
                country=data.get("country", {}).get("names", {}).get("en", "Unknown"),
                city=data.get("city", {}).get("names", {}).get("en", "Unknown"),
                longitude=data.get("location", {}).get("longitude", 0),
                latitude=data.get("location", {}).get("latitude", 0),
            )
        return location

    @property
    def MRU(self):
        """
        return the number of memory units in GiB
        """
        size = self._total_mem / GiB
        return round(size, 2)

    @property
    def HRU(self):
        """
        return the number of hd units in GiB
        size field of disks is expected to be in bytes
        """
        unit = 0
        for disk in self.disk:
            if disk["type"] in [StorageType.HDD.name, StorageType.ARCHIVE.name]:
                unit += int(disk["size"]) / GiB
        return round(unit, 2)

    @property
    def SRU(self):
        """
        return the number of ssd units in GiB
        size field of disks is expected to be in bytes
        """
        unit = 0
        for disk in self.disk:
            if disk["type"] in [StorageType.SSD.name, StorageType.NVME.name]:
                unit += int(disk["size"]) / GiB
        return round(unit, 2)

    def __repr__(self):
        return json.dumps(
            {"processor": self.processor, "memory": self.memory, "motherboard": self.motherboard, "disk": self.disk},
            indent=self.indent,
        )

    def __str__(self):
        return repr(self)


def _cpu_info(data):
    result = []
    for entry in data.values():
        if entry["DMIType"] == 4:
            info = {
                "speed": entry.get("Current Speed"),
                "core_nr": entry.get("Core Enabled"),
                "thread_nr": entry.get("Thread Count"),
                "serial": entry.get("Serial Number"),
                "manufacturer": entry.get("Manufacturer"),
                "version": entry.get("Version"),
                "id": entry.get("ID"),
            }
            result.append(info)
    return result


def _memory_info(data):
    result = []
    for entry in data.values():
        if entry["DMIType"] == 17:
            info = {
                "speed": entry.get("Speed"),
                "size": entry.get("Size"),
                "width": entry.get("Total Width"),
                "serial": entry.get("Serial Number"),
                "manufacturer": entry.get("Manufacturer"),
                "asset_tag": entry.get("Asset Tag"),
            }
            result.append(info)
    return result


def _mobo_info(data):
    result = []
    for entry in data.values():
        if entry["DMIType"] == 2:
            info = {
                "name": entry.get("Produce Name"),
                "version": entry.get("Version"),
                "serial": entry.get("Serial Number"),
                "manufacturer": entry.get("Manufacturer"),
                "asset_tag": entry.get("Asset Tag"),
            }
            result.append(info)
    return result


def _disks_info(data):
    result = []
    for device_name, entry in data.items():
        info = {
            "name": device_name,
            "model": entry.get("Device Model"),
            "firmware_version": entry.get("Firmware Version"),
            "form_factor": entry.get("Firmware Version"),
            "device_id": entry.get("LU WWN Device Id"),
            "rotation_state": entry.get("Rotation Rate"),
            "serial": entry.get("Serial Number"),
            "user_capacity": entry.get("User Capacity"),
            "sector_size": entry.get("Sector Sizes"),
            "size": entry.get("size"),
            "type": entry.get("type"),
        }
        result.append(info)
    return result


def _parse_dmi(data):
    output_data = {}
    #  Each record is separated by double newlines
    split_output = data.split("\n\n")

    for record in split_output:
        record_element = record.splitlines()

        #  Entries with less than 3 lines are incomplete / inactive; skip them
        if len(record_element) < 3:
            continue

        handle_data = _handle_re.findall(record_element[0])

        if not handle_data:
            continue
        handle_data = handle_data[0]

        dmi_handle = handle_data[0]

        output_data[dmi_handle] = {}
        output_data[dmi_handle]["DMIType"] = int(handle_data[1])
        output_data[dmi_handle]["DMISize"] = int(handle_data[2])

        #  Okay, we know 2nd line == name
        output_data[dmi_handle]["DMIName"] = record_element[1]

        in_block_elemet = ""
        in_block_list = ""

        #  Loop over the rest of the record, gathering values
        for i in range(2, len(record_element), 1):
            if i >= len(record_element):
                break
            #  Check whether we are inside a \t\t block
            if in_block_elemet != "":

                in_block_data = _in_block_re.findall(record_element[1])

                if in_block_data:
                    if not in_block_list:
                        in_block_list = in_block_data[0][0]
                    else:
                        in_block_list = in_block_list + "\t\t" + in_block_data[0][1]

                    output_data[dmi_handle][in_block_elemet] = in_block_list
                    continue
                else:
                    # We are out of the \t\t block; reset it again, and let
                    # the parsing continue
                    in_block_elemet = ""

            record_data = _record_re.findall(record_element[i])

            #  Is this the line containing handle identifier, type, size?
            if record_data:
                output_data[dmi_handle][record_data[0][0]] = record_data[0][1]
                continue

            #  Didn't findall regular entry, maybe an array of data?

            record_data2 = _record2_re.findall(record_element[i])

            if record_data2:
                #  This is an array of data - let the loop know we are inside
                #  an array block
                in_block_elemet = record_data2[0][0]
                continue

    if not output_data:
        raise j.exceptions.Base("Unable to parse 'dmidecode' output")

    return output_data


def _parse_smarctl(data):
    result = {}
    for line in data.splitlines()[4:]:
        if not line:
            continue
        ss = line.split(":", 1)
        if len(ss) != 2:
            continue
        result[ss[0].strip()] = ss[1].strip()
    return result
