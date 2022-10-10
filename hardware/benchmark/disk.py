# -*- coding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
Benchmark Disk functions.
"""

import json
import os
import subprocess
import sys


# NOTE(lucasagomes): The amount of time a specified workload will run before
# logging any performance numbers. Useful for letting performance settle
# before logging results, thus minimizing the runtime required for stable
# results. Note that the ramp_time is considered lead in time for a job,
# thus it will increase the total runtime if a special timeout or runtime
# is specified.
RAMP_TIME = 5


def is_booted_storage_device(disk):
    """Check if a given disk is booted."""
    cmdline = ("grep -w /ahcexport /proc/mounts | cut -d ' ' -f 1 | "
               "sed -e 's/[0-9]*//g'")
    if '/dev/' not in disk:
        disk = '/dev/%s' % disk
    grep_cmd = subprocess.Popen(cmdline,
                                shell=True, stdout=subprocess.PIPE)
    for booted_disk in grep_cmd.stdout:
        booted_disk = booted_disk.decode(errors='ignore')
        booted_disk = booted_disk.rstrip('\n').strip()
        if booted_disk == disk:
            return True
    return False


def get_disks_name(hw_lst, without_bootable=False):
    """Get a list of disk names."""
    disks = []
    for entry in hw_lst:
        if entry[0] == 'disk' and entry[2] == 'size':
            if without_bootable and is_booted_storage_device(entry[1]):
                sys.stderr.write("Skipping disk %s in destructive mode, "
                                 "this is the booted device !\n" % entry[1])
            elif 'I:' in entry[1]:
                pass
            else:
                disks.append(entry[1])
    return disks


def run_fio(hw_lst, disks_list, mode, io_size, time, rampup_time):
    """Run the 'fio' benchmark tool."""
    filelist = [f for f in os.listdir(".") if f.endswith(".fio")]
    for myfile in filelist:
        os.remove(myfile)
    fio = ("fio --ioengine=libaio --invalidate=1 --ramp_time=%d --iodepth=32 "
           "--runtime=%d --time_based --direct=1 --output-format=json "
           "--bs=%s --rw=%s" % (rampup_time, time, io_size, mode))

    global_disk_list = ''
    for disk in disks_list:
        if '/dev/' not in disk:
            disk = '/dev/%s' % disk
        # Flusing Disk's cache prior benchmark
        os.system("hdparm -f %s >/dev/null 2>&1" % disk)
        short_disk = disk.replace('/dev/', '')
        fio = "%s --name=MYJOB-%s --filename='%s'" % (fio, short_disk, disk)
        global_disk_list += '%s,' % short_disk
    global_disk_list = global_disk_list.rstrip(',')
    sys.stderr.write(
        'Benchmarking storage %s for %s seconds in '
        '%s mode with blocksize=%s\n' %
        (global_disk_list, time, mode, io_size))
    fio_cmd = subprocess.check_output(fio, shell=True)
    data = json.loads(fio_cmd)
    for job in data['jobs']:
        current_disk = job['jobname'].replace("MYJOB-", "")
        if len(disks_list) > 1:
            mode_str = "simultaneous_%s_%s" % (mode, io_size)
        else:
            mode_str = "standalone_%s_%s" % (mode, io_size)

        for item in ['read', 'write']:
            if job[item]['runtime'] > 0:
                hw_lst.append(('disk', current_disk, mode_str + '_KBps',
                               str(job[item]['bw'])))
                hw_lst.append(('disk', current_disk, mode_str + '_IOps',
                               str(job[item]['iops'])))


def disk_perf(hw_lst, destructive=False, running_time=10):
    """Reporting disk performance."""
    mode = "non destructive"
    # Let's count the number of runs in safe mode
    disks = get_disks_name(hw_lst)
    disks_num = len(disks)
    total_runtime = disks_num * (running_time + RAMP_TIME) * 2
    if disks_num > 1:
        total_runtime += 2 * (running_time + RAMP_TIME)

    if destructive:
        total_runtime = total_runtime * 2
        mode = 'destructive'

    sys.stderr.write('Running storage bench on %d disks in'
                     ' %s mode for %d seconds\n' %
                     (disks_num, mode, total_runtime))
    for disk in disks:
        is_booted_storage_device(disk)
        if destructive:
            if is_booted_storage_device(disk):
                sys.stderr.write("Skipping disk %s in destructive mode,"
                                 " this is the booted device !" % disk)
            else:
                run_fio(hw_lst, ['%s' % disk], "write", "1M",
                        running_time, RAMP_TIME)
                run_fio(hw_lst, ['%s' % disk], "randwrite", "4k",
                        running_time, RAMP_TIME)

        run_fio(hw_lst, ['%s' % disk],
                "read", "1M", running_time, RAMP_TIME)
        run_fio(hw_lst, ['%s' % disk],
                "randread", "4k", running_time, RAMP_TIME)

    if disks_num > 1:
        if destructive:
            run_fio(hw_lst, get_disks_name(hw_lst, True),
                    "write", "1M", running_time, RAMP_TIME)
            run_fio(hw_lst, get_disks_name(hw_lst, True),
                    "randwrite", "4k", running_time, RAMP_TIME)
        run_fio(hw_lst, disks, "read", "1M", running_time, RAMP_TIME)
        run_fio(hw_lst, disks, "randread", "4k", running_time, RAMP_TIME)
