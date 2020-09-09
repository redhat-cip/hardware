# Copyright (C) 2016 RedHat
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

"""Wrapper functions around the areca command."""

import re
from subprocess import PIPE
from subprocess import Popen
import sys

SEP_REGEXP = re.compile(r"\s*:\s*")


def _split_units(lis):
    """Return the unit name if it has a value associated."""
    units = ['RPM', '%', ' V', ' C', 'Seconds',
             'Times', 'MHz', 'KB', 'MB', 'GB']
    for unit in units:
        match = re.search("(.*)%s$" % unit, lis[1])
        if match:
            lis[1] = match.group(1).replace(' ', '')
            return unit.replace(' ', '')
    return None


def _parse_output(output, rev=False):
    """Parse the output of the areca command into an associative array."""
    res = {}
    append = ""
    if rev is True:
        sorted_output = reversed(output.split('\n'))
    else:
        sorted_output = output.split('\n')
    for line in sorted_output:
        lis = re.split(SEP_REGEXP, line.strip())
        if len(lis) == 2:
            if "GuiErrMsg" in lis[0]:
                continue
            match = re.search(r"\[(Enclosure#.*)", lis[0])
            if match:
                append = match.group(1).replace('#', '') + "/"
                continue
            if append:
                lis[0] = "%s%s" % (append, lis[0])
            if len(lis[1]) > 1 and lis[1][-1] == '.':
                lis[1] = lis[1][:-1]
            unit = _split_units(lis)
            try:
                res[lis[0].title().replace(' ', '')] = int(lis[1])
                if unit:
                    res["%s/unit" % (lis[0].title().replace(' ', ''))] = unit
            except ValueError:
                res[lis[0].title().replace(' ', '')] = lis[1]
                if unit:
                    res["%s/unit" % lis[0].title().replace(' ', '')] = unit
    return res


def _split_parts(sep, output):
    """Split the output string according to the regexp sep."""
    regexp = re.compile(sep)
    lines = output.split('\n')
    idx = []
    num = 0
    for line in lines:
        if regexp.search(line):
            idx.append(num)
        num = num + 1
    arr = []
    start = idx[0]
    for num in idx[1:]:
        arr.append('\n'.join(lines[start:num - 1]))
        start = num
    arr.append('\n'.join(lines[start:]))
    return arr


def _run_areca(*args):
    """Run the areca command in a subprocess and return the output."""
    cmd = 'cli64 ' + ' '.join(args)
    proc = Popen(cmd,
                 shell=True,
                 stdout=PIPE,
                 universal_newlines=True)
    return proc.communicate()[0]


def _run_and_parse(*args, rev=False):
    """Run the areca command in a subprocess.

    Returns the output as an associative array.
    """
    res = _run_areca(*args)
    return _parse_output(res, rev=rev)


def _adsys_info():
    """Get advanced system info."""
    arr = _run_and_parse('adsys info')
    return arr


def _hw_info():
    """Get hardware info."""
    arr = _run_and_parse('hw info', rev=True)
    return arr


def _sys_info():
    """Get system info."""
    arr = _run_and_parse('sys info')
    return arr


def _sys_showcfg():
    """Get system configuration."""
    arr = _run_and_parse('sys showcfg')
    return arr


def _hdd_pwr_info():
    """Get hard disk power information."""
    return _run_and_parse('hddpwr info')


def _disk_info(disk):
    """Get hard disk information."""
    output = _run_and_parse('disk info drv=%d' % disk)
    return output


def _disable_password():
    """Command to temporarly disable password on the cli"""
    _run_areca('set password=0000')


def detect():
    """Detect Areca controller configuration."""
    hwlist = []
    device = _sys_info()
    if not device:
        sys.stderr.write('Info: No Areca controller found\n')
        return []
    if "ControllerName" not in device.keys():
        sys.stderr.write('Info: Cannot find Areca controller name\n')
        return []

    sys.stderr.write('Info: Areca controller found: %s version %s\n' %
                     (device['ControllerName'], device['FirmwareVersion']))

    _disable_password()

    for info, value in device.items():
        hwlist.append(('areca', 'system', info, value))

    adsys = _adsys_info()
    for info, value in adsys.items():
        hwlist.append(('areca', 'system', info, value))

    cfg = _sys_showcfg()
    for info, value in cfg.items():
        hwlist.append(('areca', 'config', info, value))

    hw_info_out = _hw_info()
    for info, value in hw_info_out.items():
        hwlist.append(('areca', 'hardware', info, value))

    pwr_info = _hdd_pwr_info()
    for info, value in pwr_info.items():
        hwlist.append(('areca', 'power', info, value))

    for disk_number in range(1, 255):
        disk_info_out = _disk_info(disk_number)
        # If we don't have info about that disk, let's stop here
        if len(disk_info_out) < 2:
            break
        # Extracting disk information
        for info in disk_info_out:
            hwlist.append(('areca', "disk%d" % disk_number, info,
                           disk_info_out[info]))

    if len(hwlist):
        return hwlist

    # If we dont't detect any areca controller, return None
    # This avoid having empty lists
    return None
