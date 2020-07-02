# Copyright (C) 2013-2014 eNovance SAS <licensing@enovance.com>
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

import os
import re
import sys

from hardware import detect_utils
from hardware import smart_utils


def sizeingb(size):
    return int((size * 512) / (1000 * 1000 * 1000))


def disksize(name):
    size = open('/sys/block/' + name + '/size').read(-1)
    return sizeingb(int(size))


def disknames():
    names = []
    for name in os.listdir('/sys/block'):
        if (name[1] == 'd' and name[0] in 'shv') or name.startswith('nvme'):
            names.append(name)
    return names


def get_disk_info(name, sizes, hw_lst):
    hw_lst.append(('disk', name, 'size', str(sizes[name])))
    info_list = ['device/vendor', 'device/model', 'device/rev',
                 'queue/optimal_io_size', 'queue/physical_block_size',
                 'queue/rotational', 'queue/nr_requests']
    for info in info_list:
        disk_sys_info = '/sys/block/%s/%s' % (name, info)
        # revision can be explicitly named
        if not os.path.exists(disk_sys_info) and info == 'device/rev':
            info = 'device/revision'
        # for nvme devices we can have a nested device dir
        if not os.path.exists(disk_sys_info):
            disk_sys_info = '/sys/block/%s/device/%s' % (name, info)
        try:
            with open(disk_sys_info, 'r') as dev:
                hw_lst.append(('disk', name, info.split('/')[1],
                               dev.readline().rstrip('\n').strip()))
        except Exception as exc:
            sys.stderr.write(
                'Failed retrieving disk information %s for %s: %s\n' % (
                    info, name, str(exc)))
    try:
        with open('/sys/block/%s/queue/scheduler' % name, 'r') as dev:
            s_line = dev.readline().rstrip('\n').strip()
            sched = re.findall(r'\[(.*?)\]', s_line)
            if sched:
                hw_lst.append(('disk', name, 'scheduler', sched[0]))
    except Exception as exc:
        sys.stderr.write('Cannot extract scheduler for disk %s: %s' % (
            name, exc))


def get_disk_cache(name, hw_lst):
    # WCE & RCD from sysfs
    # https://www.kernel.org/doc/Documentation/scsi/sd-parameters.txt
    device_path = '/sys/block/{0}/device'.format(name)

    try:
        _link_info = os.readlink(device_path)
        _scsi_addr = _link_info.rsplit('/', 1)[1]
        device_path = (device_path + '/scsi_disk/{0}/cache_type').format(
            _scsi_addr)
        with open(device_path, 'r') as cache_info:
            my_text = cache_info.readline().rstrip('\n').strip()
            _wce = '1'
            _rcd = '0'
            if my_text == 'write through':
                _wce = '0'
            elif my_text == 'none':
                _wce = '0'
                _rcd = '1'
            elif 'daft' in my_text:
                _rcd = '1'
            hw_lst.append(('disk', name, 'Write Cache Enable', _wce))
            hw_lst.append(('disk', name, 'Read Cache Disable', _rcd))
    except Exception as exc:
        sys.stderr.write(
            'Failed at getting disk information at %s: %s\n' %
            (device_path, str(exc)))


def get_disk_id(name, hw_lst):
    # In some VMs, the disk-by id doesn't exists
    if os.path.exists('/dev/disk/by-id/'):
        for entry in os.listdir('/dev/disk/by-id/'):
            idp = os.path.realpath('/dev/disk/by-id/' + entry).split('/')
            if idp[-1] == name:
                id_name = "id"
                if entry.startswith('wwn'):
                    id_name = "wwn-id"
                elif entry.startswith('scsi'):
                    id_name = "scsi-id"
                hw_lst.append(('disk', name, id_name, entry))


def parse_hdparm_output(output):
    res = output.split(' = ')
    if len(res) != 2:
        return 0.0
    try:
        mbsec = res[1].split(' ')[-2]
        return float(mbsec)
    except (ValueError, KeyError):
        return 0.0


def diskperfs(names):
    return dict((name, parse_hdparm_output(
        detect_utils.cmd('hdparm -t /dev/%s' % name))) for name in names)


def disksizes(names):
    return dict((name, disksize(name)) for name in names)


def detect():
    """Detect disks."""

    hw_lst = []
    names = disknames()
    sizes = disksizes(names)
    disks = [name for name, size in sizes.items() if size > 0]
    hw_lst.append(('disk', 'logical', 'count', str(len(disks))))
    for name in disks:
        get_disk_info(name, sizes, hw_lst)

        # nvme devices do not need standard cache mechanisms
        if not name.startswith('nvme'):
            get_disk_cache(name, hw_lst)

        get_disk_id(name, hw_lst)

        # smartctl support
        # run only if smartctl command is there
        if detect_utils.which("smartctl"):
            if name.startswith('nvme'):
                sys.stderr.write('Reading SMART for nvme\n')
                smart_utils.read_smart_nvme(hw_lst, name)
            else:
                smart_utils.read_smart(hw_lst, "/dev/%s" % name)
        else:
            sys.stderr.write("Cannot find smartctl, exiting\n")

    return hw_lst
