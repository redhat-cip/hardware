# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import subprocess
import sys

from hardware import smart_utils_info


def _parse_line(line):
    line = line.strip().decode(errors='ignore')
    return line


def read_smart_field(hwlst, line, device_name, item, title):
    if item in line:
        if "temperature" in title:
            try:
                hwlst.append(("disk", device_name, "SMART/%s" % title,
                              line.split(item)[1].strip().split()[0]))
                hwlst.append(("disk", device_name, "SMART/%s_unit" % title,
                              line.split(item)[1].strip().split()[1]))
            except Exception:
                sys.stderr.write("read_smart_field: Error while searching "
                                 "for %s in %s\n" % (item, line))
        else:
            value = ""
            for result in line.split(item)[1:]:
                value = "%s %s" % (value, result.strip())
            hwlst.append(("disk", device_name, "SMART/%s" % title,
                          value.strip()))
            return value.strip()
    return ""


def read_smart_scsi_error_log(hwlst, line, device_name, error_log):
    result = line.split()
    if len(result) > 7:
        hwlst.append(("disk", device_name,
                      "SMART/%s_%s" % (error_log, "total_corrected_errors"),
                      result[4].strip()))
        hwlst.append(("disk", device_name,
                      "SMART/%s_%s" % (error_log, "gigabytes_processed"),
                      result[6].strip()))
        hwlst.append(("disk", device_name,
                      "SMART/%s_%s" % (error_log, "total_uncorrected_errors"),
                      result[7].strip()))


def read_smart_scsi(hwlst, device, optional_flag="", mode=""):
    optional_string = ""
    if optional_flag:
        optional_string = " with %s" % optional_flag

    device_name = os.path.basename(device)
    if mode:
        device_name = "%s{%s}" % (device_name, optional_flag.split()[1])

    sdparm_cmd = subprocess.Popen("smartctl -a %s %s" %
                                  (device, optional_flag),
                                  shell=True,
                                  stdout=subprocess.PIPE)
    vendor = ""
    product = ""
    for line in sdparm_cmd.stdout:
        line = _parse_line(line)

        # This disk doesn't exists or doesn't support SMART
        if "INQUIRY failed" in line:
            return

        # Being a SCSI raid controller, we can have ATA devices
        if line.startswith("ID#"):
            return read_smart_ata(hwlst, device, optional_flag, mode)

        temp = read_smart_field(hwlst, line, device_name, "Vendor:", "vendor")
        if temp:
            sys.stderr.write("read_smart_scsi: Found S.M.A.R.T information "
                             "on %s%s\n" % (device, optional_string))
            vendor = temp
            continue

        temp = read_smart_field(
            hwlst, line, device_name, "Product:", "product")
        if temp:
            product = temp
            continue

        if (line.startswith("Device does not support SMART")
                or "Unavailable - device lacks SMART capability." in line):
            # Device is said no to support smart but on some RAID arrays
            # we can bypass it
            if optional_flag == "":
                if (vendor == "DELL") and ("PERC" in product):
                    for pdisk_number in range(0, 24):
                        read_smart_scsi(hwlst, device,
                                        "-d megaraid,%d" % pdisk_number,
                                        "megaraid")
                if (vendor == "HP") and ("LOGICAL VOLUME" in product):
                    for pdisk_number in range(0, 24):
                        read_smart_scsi(hwlst, device,
                                        "-d cciss,%d" % pdisk_number, "cciss")
            return hwlst

        for smart_info, hwlst_value in smart_utils_info.SMART_FIELDS.items():
            read_smart_field(hwlst, line, device_name, smart_info, hwlst_value)

        for error_log in ["read", "write", "verify"]:
            if line.startswith("%s:" % error_log):
                read_smart_scsi_error_log(hwlst, line, device_name, error_log)
                continue
    return hwlst


def read_smart_ata(hwlst, device, optional_flag="", mode=""):
    foundid = False
    device_name = os.path.basename(device)
    optional_string = ""
    if optional_flag:
        optional_string = " with %s" % optional_flag

    values = {}
    if mode:
        device_name = "%s{%s}" % (device_name, optional_flag.split()[1])

    sdparm_cmd = subprocess.Popen("smartctl -a %s %s" % (device,
                                                         optional_flag),
                                  shell=True, stdout=subprocess.PIPE)
    for line in sdparm_cmd.stdout:
        line = _parse_line(line)

        if read_smart_field(hwlst, line, device_name, "Device Model:",
                            "device_model"):
            sys.stderr.write("read_smart_ata: Found S.M.A.R.T information "
                             "on %s%s\n" % (device, optional_string))
            continue

        if read_smart_field(hwlst, line, device_name, "Serial Number:",
                            "serial_number"):
            continue

        if read_smart_field(hwlst, line, device_name, "Firmware Version:",
                            "firmware_version"):
            continue

        if read_smart_field(hwlst, line, device_name, "Rotation Rate:",
                            "rotation_rate"):
            continue

        if line.startswith("ID#"):
            foundid = True
            continue
        if foundid is False:
            continue
        elif not line:
            break
        try:
            fields = line.split()
            if len(fields) < 10:
                raise ValueError(
                    'Expected at least 10 fields in %s, found %d.' %
                    (line, len(fields)))
            values["id"] = fields[0]
            values["name"] = fields[1]
            values["flag"] = fields[2]
            values["value"] = fields[3]
            values["worst"] = fields[4]
            values["thresh"] = fields[5]
            values["type"] = fields[6]
            values["updated"] = fields[7]
            values["when_failed"] = fields[8]
            if values["when_failed"] == "-":
                values["when_failed"] = "NEVER"
            raw_values = fields[9:]
            raw_value = ""
            for raw in raw_values:
                raw_value = "%s %s" % (raw_value, raw)
            values["raw"] = raw_value
            for title in ["value", "worst", "thresh", "when_failed", "raw"]:
                hwlst.append(("disk", device_name,
                              "SMART/%s(%s)/%s" % (values["name"],
                                                   values["id"],
                                                   title),
                              values[title]))
            continue

        except Exception:
            sys.stderr.write("read_smart: failed to read line : %s\n" % line)
            continue


def read_smart(hwlst, device, optional_flag=""):
    optional_string = ""
    if optional_flag:
        optional_string = " with %s" % optional_flag

    if os.path.exists(device):
        sys.stderr.write(
            "read_smart: Reading S.M.A.R.T information on %s%s\n" %
            (device, optional_string))
        sdparm_cmd = subprocess.Popen("smartctl -a %s %s" %
                                      (device,
                                       optional_flag),
                                      shell=True,
                                      stdout=subprocess.PIPE)
        for line in sdparm_cmd.stdout:
            line = _parse_line(line)

            if (line.startswith("Device does not support SMART")
                    or ("Unavailable - device lacks SMART capability" in line)
                    or line.startswith(
                        "Device supports SMART and is Enabled")):
                return read_smart_scsi(hwlst, device, optional_flag)

            if line.startswith("ID#"):
                return read_smart_ata(hwlst, device, optional_flag)

        # If no ID# was found, let's retry with "-d ata"
        if optional_flag == "":
            return read_smart(hwlst, device, "-d ata")

    sys.stderr.write("read_smart: no device %s\n" % device)
    return


def read_smart_nvme(hwlst, device_name):
    device_path = '/dev/%s' % device_name

    if os.path.exists(device_path):
        sys.stderr.write(
            "read_smart_nvme: Reading S.M.A.R.T information on %s\n" %
            device_path)

        # to be compatible with smart tools version < 7.x we need
        # to specify the broadcast namespace
        # see https://www.smartmontools.org/ticket/1134 for details
        sdparm_cmd = subprocess.Popen(
            "smartctl -d nvme,0xffffffff -a %s" % device_path,
            shell=True, stdout=subprocess.PIPE)

        for line in sdparm_cmd.stdout:
            line = line.strip().decode(errors='ignore')
            for disk_info, info_tag in smart_utils_info.NVME_INFOS.items():
                read_smart_field(hwlst, line, device_name, disk_info, info_tag)
        return hwlst

    sys.stderr.write("read_smart: no device %s\n" % device_name)
    return
