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
from hardware import sensors
from hardware import system


AUXV_FLAGS = ["AT_HWCAP", "AT_HWCAP2", "AT_PAGESZ",
              "AT_FLAGS", "AT_PLATFORM"]
# These flags may or not be present on a particular arch
AUXV_OPT_FLAGS = ["AT_BASE_PLATFORM"]


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

    hrdw.extend(areca.detect())
    hrdw.extend(hpacucli.detect())
    hrdw.extend(megacli.detect())
    hrdw.extend(diskinfo.detect())

    system_info = system.detect()
    if not system_info:
        sys.exit(1)
    hrdw.extend(system_info)

    hrdw.extend(ipmi.detect())
    hrdw.extend(ib.detect())
    hrdw.extend(sensors.detect_temperatures())
    hrdw.extend(ipmi.get_ipmi_sdr())
    hrdw.extend(rtc.detect_rtc_clock())

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
