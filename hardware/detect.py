# Copyright (C) 2013-2015 eNovance SAS <licensing@enovance.com>
#
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

"""Main entry point for hardware and system detection routines in eDeploy."""

import argparse
import json
import os
import pprint
from subprocess import PIPE
from subprocess import Popen
import sys

from hardware import areca
from hardware.benchmark import cpu as bm_cpu
from hardware.benchmark import disk as bm_disk
from hardware.benchmark import mem as bm_mem
from hardware import bios_hp
from hardware import detect_utils
from hardware import diskinfo
from hardware import hpacucli
from hardware import infiniband as ib
from hardware import ipmi
from hardware import megacli
from hardware import rtc
from hardware import system


AUXV_FLAGS = ["AT_HWCAP", "AT_HWCAP2", "AT_PAGESZ",
              "AT_FLAGS", "AT_PLATFORM"]
# These flags may or not be present on a particular arch
AUXV_OPT_FLAGS = ["AT_BASE_PLATFORM"]


def modprobe(module):
    'Load a kernel module using modprobe.'
    status, _ = detect_utils.cmd('modprobe %s' % module)
    if status == 0:
        sys.stderr.write('Info: Probing %s failed\n' % module)


def detect_ipmi(hw_lst):
    'Detect IPMI interfaces.'
    modprobe("ipmi_smb")
    modprobe("ipmi_si")
    modprobe("ipmi_devintf")
    if (os.path.exists('/dev/ipmi0')
            or os.path.exists('/dev/ipmi/0')
            or os.path.exists('/dev/ipmidev/0')):
        for channel in range(0, 16):
            status, _ = detect_utils.cmd(
                'ipmitool channel info %d 2>&1 | grep -sq Volatile' % channel)
            if status == 0:
                hw_lst.append(('system', 'ipmi', 'channel', '%s' % channel))
                break
        status, output = detect_utils.cmd('ipmitool lan print')
        if status == 0:
            ipmi.parse_lan_info(output, hw_lst)

        return True

    # do we need a fake ipmi device for testing purpose ?
    status, _ = detect_utils.cmd('grep -qi FAKEIPMI /proc/cmdline')
    if status == 0:
        # Yes ! So let's create a fake entry
        hw_lst.append(('system', 'ipmi-fake', 'channel', '0'))
        sys.stderr.write('Info: Added fake IPMI device\n')
        return True

    sys.stderr.write('Info: No IPMI device found\n')
    return False


def detect_infiniband(hw_lst):
    """Detect Infiniband devices.

    To detect if an IB device is present, we search for a pci device.
    This pci device shall be from vendor Mellanox (15b3) from class 0280
    Class 280 stands for a Network Controller while ethernet device are 0200.
    """
    status, _ = detect_utils.cmd(
        "lspci -d 15b3: -n|awk '{print $2}'|grep -q '0280'")
    if status != 0:
        sys.stderr.write('Info: No Infiniband device found\n')
        return False

    for ib_card in range(len(ib.ib_card_drv())):
        card_type = ib.ib_card_drv()[ib_card]
        ib_infos = ib.ib_global_info(card_type)
        nb_ports = ib_infos['nb_ports']
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'card_type', card_type))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'device_type', ib_infos['device_type']))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'fw_version', ib_infos['fw_ver']))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'hw_version', ib_infos['hw_ver']))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'nb_ports', nb_ports))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'sys_guid', ib_infos['sys_guid']))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'node_guid', ib_infos['node_guid']))
        for port in range(1, int(nb_ports) + 1):
            ib_port_infos = ib.ib_port_info(card_type, port)
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'state', ib_port_infos['state']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'physical_state',
                           ib_port_infos['physical_state']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'rate', ib_port_infos['rate']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'base_lid', ib_port_infos['base_lid']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'lmc', ib_port_infos['lmc']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'sm_lid', ib_port_infos['sm_lid']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'port_guid', ib_port_infos['port_guid']))
    return True


def read_hwmon(hwlst, entry, sensor, label_name, appendix, processor_num,
               entry_name):
    try:
        hwmon = "%s_%s" % (sensor, appendix)
        filename = "/sys/devices/platform/%s/%s" % (entry, hwmon)
        if not os.path.isfile(filename):
            if len(hwmon) > 16:
                # Some kernels are shortening the filename to 17 chars
                # Let's try to find if we are in this case
                filename = "/sys/devices/platform/%s/%s" % (entry, hwmon[:16])
                if not os.path.isfile(filename):
                    sys.stderr.write("read_hwmon: No entry found for %s/%s\n" %
                                     (label_name, entry_name))
                    return
            else:
                sys.stderr.write("read_hwmon: No entry found for %s/%s\n" %
                                 (label_name, entry_name))
                return

        value = open(filename, 'r').readline().strip()
        hwlst.append(('cpu', 'physical_%d' % processor_num, "%s/%s" %
                      (label_name, entry_name), value))
    except Exception:
        pass


def detect_temperatures(hwlst):
    for entry in os.listdir("/sys/devices/platform/"):
        if entry.startswith("coretemp."):
            processor_num = int(entry.split(".")[1])
            for label in os.listdir("/sys/devices/platform/%s" % entry):
                if label.startswith("temp") and label.endswith("_label"):
                    sensor = label.split("_")[0]
                    try:
                        with open("/sys/devices/platform/%s/%s_label" %
                                  (entry, sensor), 'r') as fsensor:
                            label_name = fsensor.readline()
                            label_name = label_name.strip().replace(" ", "_")
                    except Exception:
                        sys.stderr.write("detect_temperatures: "
                                         "Cannot open label on %s/%s\n" %
                                         (entry, sensor))
                        continue

                    read_hwmon(hwlst, entry, sensor, label_name, "input",
                               processor_num, "temperature")
                    read_hwmon(hwlst, entry, sensor, label_name, "max",
                               processor_num, "max")
                    read_hwmon(hwlst, entry, sensor, label_name, "crit",
                               processor_num, "critical")
                    read_hwmon(hwlst, entry, sensor, label_name, "crit_alarm",
                               processor_num, "critical_alarm")


def detect_rtc_clock(hw_lst):
    hw_lst.append(('system', 'rtc', 'utc', rtc.get_rtc()))


def detect_auxv(hw_lst):
    new_env = os.environ.copy()
    new_env["LD_SHOW_AUXV"] = "1"

    cmd = Popen("/bin/true",
                env=new_env,
                stdout=PIPE)
    stdout, err = cmd.communicate()
    if err is not None:
        sys.stderr.write("Info: AUXV output received\n")
        return

    auxv = dict()
    supported_flags = AUXV_FLAGS + AUXV_OPT_FLAGS
    for line in stdout.decode("utf-8").splitlines():
        k, v = [i.strip() for i in line.split(":")]
        if k in supported_flags:
            auxv[k[3:].lower()] = v
            hw_lst.append(('hw', 'auxv', k[3:].lower(), v))


def parse_ahci(hrdw, words):
    if len(words) < 4:
        return
    if "flags" in words[2]:
        flags = ""
        for flag in sorted(words[3:]):
            flags = "%s %s" % (flags, flag)
        hrdw.append(('ahci', words[1], "flags", flags.strip()))


def parse_dmesg(hrdw):
    """Run dmesg and parse the output."""

    _, output = detect_utils.cmd("dmesg")
    for line in output.split('\n'):
        words = line.strip().split(" ")

        if words[0].startswith("[") and words[0].endswith("]"):
            words = words[1:]

        if not words:
            continue

        if "ahci" in words[0]:
            parse_ahci(hrdw, words)


def parse_args(arguments):
    """Arguments parser."""

    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--human',
                        help='Print output in human readable format',
                        action='store_true',
                        default=False)

    benchmark = parser.add_argument_group('benchmark')
    benchmark.add_argument('--benchmark', '-b',
                           choices=['cpu', 'mem', 'disk'],
                           nargs='+',
                           help=('Run benchmark for specific components. '
                                 'Valid components are: cpu, mem, disk'))
    benchmark.add_argument('--benchmark-disk-destructive',
                           help=('If specified make the disk component '
                                 'benchmark to be destructive'),
                           action='store_true',
                           default=False)

    return parser.parse_args(arguments)


def main():
    """Command line entry point."""

    os.environ["LANG"] = "en_US.UTF-8"
    args = parse_args(sys.argv[1:])

    hrdw = []

    hrdw.append(areca.detect())
    hrdw.append(hpacucli.detect())
    hrdw.append(megacli.detect())
    hrdw.append(diskinfo.detect())

    system_info = system.detect()
    if not system_info:
        sys.exit(1)
    hrdw.append(system_info)

    detect_ipmi(hrdw)
    detect_infiniband(hrdw)
    detect_temperatures(hrdw)
    detect_utils.get_ddr_timing(hrdw)
    detect_utils.ipmi_sdr(hrdw)
    detect_rtc_clock(hrdw)
    detect_auxv(hrdw)
    parse_dmesg(hrdw)
    bios_hp.dump_hp_bios(hrdw)

    if args.benchmark:
        if 'cpu' in args.benchmark:
            bm_cpu.cpu_perf(hrdw)
        if 'mem' in args.benchmark:
            bm_mem.mem_perf(hrdw)
        if 'disk' in args.benchmark:
            bm_disk.disk_perf(hrdw,
                              destructive=args.benchmark_disk_destructive)

    hrdw = detect_utils.clean_tuples(hrdw)

    hrdw = list(filter(None, hrdw))

    if args.human:
        pprint.pprint(hrdw)
    else:
        print(json.dumps(hrdw))
