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

"""
API to the hpacucli utility. Can be used to gather informations
about disks, RAID arrays or controllers or to configure them.
"""

import os
import re
import sys

import pexpect

from hardware import detect_utils


ALL_SHOW_REGEXP = re.compile(r'^(.*) in Slot ([0-9]+).*\(sn: (.*)\)', re.M)
ERROR_REGEXP = re.compile('Error: (.*)', re.M)
LOGICAL_REGEXP = re.compile(r'\s*logicaldrive (.*) \((.*), (.*), (.*)\)')
PHYSICAL_REGEXP = re.compile(r'\s*physicaldrive (.*) \(.*, (.*), (.*), (.*)\)')
PROMPT_REGEXP = re.compile('=> ')


class Error(Exception):
    """Exception to capture errors while calling hpacucli sub-commands."""

    def __init__(self, value):
        super(Error, self).__init__()
        self.value = value

    def __str__(self):
        return repr(self.value)


def parse_ctrl_all_show(output):
    """Parse the output of the 'ctrl <sel> all show' hpacucli sub-command."""
    lst = []
    for line in output.split('\n'):
        res = ALL_SHOW_REGEXP.search(line)
        if res:
            lst.append((int(res.group(2)), res.group(1), res.group(3)))
    return lst


def _generic_parsing(line, status, ignore_list):
    items = line.split(': ')
    if len(items) == 2:
        item = items[0].strip().lower().replace(
            ' ', '_').replace('(', '').replace(')', '').replace('__', '_')
        value = items[1].strip()
        if item not in ignore_list:
            status[item] = ' '.join(value.split())


def _parse_ctrl_d_disk_show(output):
    status = {}
    for line in output.split('\n'):
        text = line.split()
        if 'array' in text:
            status['array'] = text[1]
        _generic_parsing(line, status, ['port', 'bay', 'box'])

    return status


def _parse_ctrl_show(output):
    status = {}
    for line in output.split('\n'):
        _generic_parsing(line, status, ['slot'])

    return status


def _parse_ctrl_d_all_show(output, regexp):
    """Function to parse lines like:

    array C

       physicaldrive 1I:1:2 (port 1I:box 1:bay 2, SATA, 1 TB, OK)

    into an associative array with the matching result like:
    [('array C', [('1I:1:2', 'SATA', '1 TB', 'OK')]),]
    The regexp arg must extract the 4 informations from description lines.
    """
    arr = []
    cur = []
    idx = None
    for line in output.split('\n'):
        line = line.strip()
        if line[:5].lower() == 'array' or line.lower() == 'unassigned':
            if idx:
                arr.append((idx, cur))
                cur = []
            idx = line
        else:
            res = regexp.search(line)
            if res:
                cur.append(res.groups())

    if idx:
        arr.append((idx, cur))
    return arr


def parse_ctrl_ld_all_show(output):
    """Parse the output of the

    'ctrl <sel> ld all show' hpacucli sub-command.
    """
    return _parse_ctrl_d_all_show(output, LOGICAL_REGEXP)


def parse_ctrl_pd_all_show(output):
    """Parse the output of the

    'ctrl <sel> pd all show' hpacucli sub-command.
    """
    return _parse_ctrl_d_all_show(output, PHYSICAL_REGEXP)


def parse_ctrl_show(output):
    """Parse the output of the

    'ctrl <sel> pd <disk> show' hpacucli sub-command.
    """
    return _parse_ctrl_show(output)


def parse_ctrl_pd_disk_show(output):
    """Parse the output of the

    'ctrl <sel> pd <disk> show' hpacucli sub-command.
    """
    return _parse_ctrl_d_disk_show(output)


def parse_error(output):
    """Parse the output of an hpacucli sub-command for an error.

    Raises an Error exception if one is found.
    """
    res = ERROR_REGEXP.search(output)
    if res:
        raise Error(res.group(1))


def parse_ctrl_ld_show(output):
    """Parse the output of the

    'ctrl <sel> ld <id> show' hpacucli sub-command.
    """
    arr = {}
    idx = None
    for line in output.split('\n'):
        if idx is not None:
            res = PHYSICAL_REGEXP.search(line.strip())
            if res:
                arr[idx] = res.group(1)
            else:
                arr[idx] = line
            idx = None
            continue
        res = line.split(':')
        if len(res) == 2:
            if res[1] == '':
                idx = res[0].strip()
            else:
                idx = None
                arr[res[0].strip()] = res[1].strip()
        # handle this kind of lines:
        # Disk Name: /dev/sda          Mount Points: None
        elif len(res) == 3:
            middle = re.split(r"\s+", res[1].strip(), 1)
            arr[res[0].strip()] = middle[0]
            arr[middle[1]] = res[2].strip()
    return arr


class Cli:
    """Cli class.

    Class to launch an hpacucli command in the background and to
    interact with it to configure or gather information.
    """

    def __init__(self, debug=False):
        self.process = None
        self.debug = debug

    def launch(self):
        """Launch an hpacucli from /usr/sbin.

        Must be called before any other method.
        """
        # With the hpsa kernel module, we need to load the sg kernel
        # module before to have everything working. So we always load
        # it.
        os.system('modprobe sg')
        path = None
        for path2 in ('/usr/sbin/ssacli',
                      '/usr/sbin/hpssacli',
                      '/usr/sbin/hpacucli'):
            if os.path.exists(path2):
                path = path2
                break
        if path:
            try:
                if self.debug:
                    print('Launching', path)
                self.process = pexpect.spawn(path, encoding='utf-8')
                self.process.expect(PROMPT_REGEXP)
            except (OSError, pexpect.EOF, pexpect.TIMEOUT):
                return False
            return True

        return False

    def _sendline(self, line):
        """Internal method to interact with hpacucli.

        Send a command to the hpacucli, wait for the prompt and
        returns the output string.
        """
        if self.debug:
            print(line)
        self.process.sendline(line)
        try:
            self.process.expect(PROMPT_REGEXP)
            ret = self.process.before[len(line):]
        except pexpect.TIMEOUT:
            ret = 'Error: timeout'

        parse_error(ret)
        return ret

    def ctrl_all_show(self):
        """Send the 'ctrl all show' sub-command.

        Returns its output parsed in a structured data.
        """
        return parse_ctrl_all_show(
            self._sendline('ctrl all show'))

    def ctrl_show(self, ctrl):
        """Send the 'ctrl <ctrl> show' sub-command.

        Returns its output parsed in a structured data.
        """
        return parse_ctrl_show(
            self._sendline('ctrl %s show' % ctrl))

    def ctrl_pd_all_show(self, selector):
        """Send the 'ctrl <selector> pd all show' sub-command.

        Returns its output parsed in a structured data.
        """
        return parse_ctrl_pd_all_show(
            self._sendline('ctrl %s pd all show' % selector))

    def ctrl_pd_disk_show(self, selector, disk):
        """Send the 'ctrl <selector> pd <disk> show' sub-command.

        Returns its output parsed in a structured data.
        """
        return parse_ctrl_pd_disk_show(
            self._sendline('ctrl %s pd %s show' % (selector, disk)))

    def ctrl_ld_all_show(self, selector):
        """Send the 'ctrl <selector> ld all show' sub-command.

        Returns its output parsed in a structured data.
        """
        return parse_ctrl_ld_all_show(
            self._sendline('ctrl %s ld all show' % selector))

    def ctrl_ld_show(self, selector, ldid):
        """Send the "ctrl <selector> ld <ldid> show" sub-command.

        Returns its output parsed in a structured data.
        """
        return parse_ctrl_ld_show(
            self._sendline('ctrl %s ld %s show' % (selector, ldid)))

    def ctrl_delete(self, selector):
        """Send the 'ctrl <selector> delete forced' sub-command."""
        self._sendline('ctrl %s delete forced' % selector)
        return True

    def ctrl_create_ld(self, selector, drives, raid):
        """ctrl_create_ld method.

        Send the 'ctrl <selector> create type=ld drives=<drives> raid=<raid>'
        sub-command.
        Returns the created device name like /dev/sda.
        """
        self._sendline(
            'ctrl %s create type=ld drives=%s raid=%s' %
            (selector, ','.join(drives), raid))
        lds = self.ctrl_ld_all_show(selector)
        # get the last created ld which is the one just created
        last_created_id = lds[-1][1][0][0]
        info = self.ctrl_ld_show(selector, last_created_id)
        return info['Disk Name']


def detect():
    """Detect HP RAID controller configuration."""
    hwlist = []
    disk_count = 0
    try:
        cli = Cli(debug=False)
        if not cli.launch():
            return hwlist
        controllers = cli.ctrl_all_show()
        if not controllers:
            sys.stderr.write('Info: No hpa controller found\n')
            return hwlist

    except Error as expt:
        sys.stderr.write('Info: detect_hpa : %s\n' % expt.value)
        return hwlist

    hwlist.append(('hpa', 'slots', 'count', str(len(controllers))))
    global_pdisk_size = 0
    for controller in controllers:
        try:
            slot = 'slot=%d' % controller[0]
            controllers_infos = cli.ctrl_show(slot)
            for controller_info in controllers_infos.keys():
                hwlist.append(('hpa', slot.replace('=', '_'),
                               controller_info,
                               controllers_infos[controller_info]))
            for _, disks in cli.ctrl_pd_all_show(slot):
                for disk in disks:
                    disk_count += 1
                    hwlist.append(('disk', disk[0], 'type', disk[1]))
                    hwlist.append(('disk', disk[0], 'slot',
                                   str(controller[0])))
                    disk_infos = cli.ctrl_pd_disk_show(slot, disk[0])
                    for disk_info in disk_infos.keys():
                        value = disk_infos[disk_info]
                        if disk_info == 'size':
                            value = detect_utils.size_in_gb(
                                disk_infos[disk_info])
                            global_pdisk_size = (
                                global_pdisk_size + float(value))
                        hwlist.append(('disk', disk[0], disk_info,
                                       value))
        except Error as expt:
            sys.stderr.write('Info: detect_hpa : controller %d : %s\n'
                             % (controller[0], expt.value))

    if global_pdisk_size > 0:
        hwlist.append(('disk', 'hpa', 'size', '%.2f' % global_pdisk_size))

    hwlist.append(('disk', 'hpa', 'count', str(disk_count)))
    return hwlist
