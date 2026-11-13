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
import stat
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
    """Check whether a disk backs a mounted filesystem or active swap.

    If the mounted-device topology cannot be determined, return True so callers
    avoid destructive writes to a device that might be in use. The function
    name is retained for compatibility.
    """
    return _is_mounted_device(disk, _get_mounted_device_names())


def _device_name(device):
    """Return a block device's basename, including for /dev paths."""
    path = str(device).split('[', 1)[0]
    if not path.startswith('/dev/'):
        path = '/dev/%s' % path
    return os.path.basename(os.path.realpath(path))


def _device_path(device):
    path = str(device)
    if not path.startswith('/dev/'):
        path = '/dev/%s' % path.lstrip('/')
    path = os.path.realpath(path)
    if os.path.commonpath(('/dev', path)) != '/dev':
        return None
    return path


def _is_block_device(device):
    path = _device_path(device)
    if path is None:
        return False
    try:
        return stat.S_ISBLK(os.stat(path).st_mode)
    except OSError:
        return False


def _flush_disk_cache(device):
    try:
        subprocess.run(
            ['hdparm', '-f', device],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        pass


def _collect_device_names(devices):
    if not isinstance(devices, list) or not devices:
        return None
    names = set()
    for device in devices:
        if not isinstance(device, dict):
            return None
        name = device.get('name')
        if not name:
            return None
        names.add(_device_name(name))
        children = device.get('children') or []
        if not isinstance(children, list):
            return None
        if children:
            child_names = _collect_device_names(children)
            if child_names is None:
                return None
            names.update(child_names)
    return names


def _get_swap_device_sources():
    """Return active swap block-device sources, or None if unreadable."""
    try:
        with open('/proc/swaps', 'r') as swap_file:
            next(swap_file, None)
            return {line.split()[0] for line in swap_file
                    if line.split() and line.split()[0].startswith('/dev/')}
    except OSError:
        return None


def _get_mounted_device_names():
    """Return devices backing mounts and active swap, or None if uncertain.

    Use findmnt to identify mounted block-device sources, then lsblk's inverse
    dependency tree to include partitions, device-mapper devices, and their
    backing devices. Active swap devices are included too. Returning None is
    deliberately fail-closed for destructive benchmark runs.
    """
    try:
        mounts = subprocess.run(
            ['findmnt', '--json', '--evaluate', '--output', 'TARGET,SOURCE'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if mounts.returncode != 0:
        return None
    try:
        mount_data = json.loads(mounts.stdout)
    except (TypeError, ValueError):
        return None
    if not isinstance(mount_data, dict):
        return None
    filesystems = mount_data.get('filesystems', [])
    if not isinstance(filesystems, list):
        return None

    root_found = False
    sources = set()
    pending_filesystems = list(filesystems)
    while pending_filesystems:
        filesystem = pending_filesystems.pop()
        if not isinstance(filesystem, dict):
            continue
        children = filesystem.get('children') or []
        if not isinstance(children, list):
            return None
        pending_filesystems.extend(children)
        source = str(filesystem.get('source', '')).split('[', 1)[0]
        if filesystem.get('target') == '/':
            root_found = True
            if not source.startswith('/dev/'):
                return None
        if source.startswith('/dev/'):
            sources.add(source)

    if not root_found or not sources:
        return None
    swap_sources = _get_swap_device_sources()
    if swap_sources is None:
        return None
    sources.update(swap_sources)

    mounted_devices = set()
    for source in sources:
        try:
            result = subprocess.run(
                ['lsblk', '--json', '--paths', '--inverse', '--output',
                 'NAME,TYPE', source],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except OSError:
            return None
        if result.returncode != 0:
            return None
        try:
            block_data = json.loads(result.stdout)
        except (TypeError, ValueError):
            return None
        if not isinstance(block_data, dict):
            return None
        devices = block_data.get('blockdevices', [])
        if not isinstance(devices, list) or not devices:
            return None
        device_names = _collect_device_names(devices)
        if device_names is None:
            return None
        mounted_devices.update(device_names)

    return mounted_devices or None


def _is_mounted_device(disk, mounted_devices):
    return (mounted_devices is None
            or _device_name(disk) in mounted_devices)


def get_disks_name(hw_lst, without_bootable=False):
    """Get a list of disk names."""
    disks = []
    mounted_devices = None
    if without_bootable:
        mounted_devices = _get_mounted_device_names()

    for entry in hw_lst:
        if entry[0] == 'disk' and entry[2] == 'size':
            if 'I:' in entry[1]:
                continue
            if not _is_block_device(entry[1]):
                sys.stderr.write(
                    'Skipping disk %s because it is not a block device\n' %
                    entry[1])
                continue
            if (without_bootable
                    and _is_mounted_device(entry[1], mounted_devices)):
                sys.stderr.write(
                    'Skipping disk %s in destructive mode because it backs '
                    'a mounted filesystem or device safety could not be '
                    'verified\n' % entry[1])
            else:
                disks.append(entry[1])
    return disks


def run_fio(hw_lst, disks_list, mode, io_size, time, rampup_time):
    """Run the 'fio' benchmark tool."""
    fio = [
        'fio',
        '--ioengine=libaio',
        '--invalidate=1',
        '--ramp_time=%d' % rampup_time,
        '--iodepth=32',
        '--runtime=%d' % time,
        '--time_based',
        '--direct=1',
        '--output-format=json',
        '--bs=%s' % io_size,
        '--rw=%s' % mode,
        '--random_generator=tausworthe64',
    ]
    valid_disks = []
    global_disk_list = ''
    for disk in disks_list:
        device = _device_path(disk)
        if device is None or not _is_block_device(device):
            sys.stderr.write(
                'Skipping fio target %s because it is not a block device\n' %
                disk)
            continue
        _flush_disk_cache(device)
        short_disk = os.path.basename(device)
        fio.extend(['--name=MYJOB-%s' % short_disk,
                    '--filename=%s' % device])
        valid_disks.append(device)
        global_disk_list += '%s,' % short_disk
    if not valid_disks:
        return
    global_disk_list = global_disk_list.rstrip(',')
    sys.stderr.write(
        'Benchmarking storage %s for %s seconds in '
        '%s mode with blocksize=%s\n' %
        (global_disk_list, time, mode, io_size))
    fio_cmd = subprocess.check_output(fio)
    data = json.loads(fio_cmd)
    for job in data['jobs']:
        current_disk = job['jobname'].replace("MYJOB-", "")
        if len(valid_disks) > 1:
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
        mounted_devices = _get_mounted_device_names()
        if mounted_devices is None:
            sys.stderr.write(
                'Unable to determine mounted storage devices; skipping '
                'destructive disk benchmarks\n')
    else:
        mounted_devices = set()

    sys.stderr.write('Running storage bench on %d disks in'
                     ' %s mode for %d seconds\n' %
                     (disks_num, mode, total_runtime))
    writable_disks = []
    for disk in disks:
        if destructive:
            if _is_mounted_device(disk, mounted_devices):
                sys.stderr.write(
                    'Skipping destructive writes to %s because it backs a '
                    'mounted filesystem or device safety could not be '
                    'verified\n' % disk)
            else:
                writable_disks.append(disk)
                run_fio(hw_lst, ['%s' % disk], "write", "1M",
                        running_time, RAMP_TIME)
                run_fio(hw_lst, ['%s' % disk], "randwrite", "4k",
                        running_time, RAMP_TIME)

        run_fio(hw_lst, ['%s' % disk],
                "read", "1M", running_time, RAMP_TIME)
        run_fio(hw_lst, ['%s' % disk],
                "randread", "4k", running_time, RAMP_TIME)

    if disks_num > 1:
        if destructive and writable_disks:
            run_fio(hw_lst, writable_disks,
                    "write", "1M", running_time, RAMP_TIME)
            run_fio(hw_lst, writable_disks,
                    "randwrite", "4k", running_time, RAMP_TIME)
        run_fio(hw_lst, disks, "read", "1M", running_time, RAMP_TIME)
        run_fio(hw_lst, disks, "randread", "4k", running_time, RAMP_TIME)
