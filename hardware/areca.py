#
# Copyright (C) 2016 RedHat
#
# Author: Erwan Velu <erwan.velu@redhat.com>
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

'''Wrapper functions around the areca command.'''

from __future__ import print_function
import re
from subprocess import PIPE
from subprocess import Popen

SEP_REGEXP = re.compile(r'\s*:\s*')


def split_units(lis):
    'If the value have unit, remove it from the value and return the unit name'
    for unit in ['RPM', '%', ' V', ' C', 'Seconds', 'Times', 'MHz', 'KB', 'MB',
                 'GB']:
        match = re.search("(.*)%s$" % unit, lis[1])
        if match:
            lis[1] = match.group(1).replace(' ', '')
            return unit.replace(' ', '')
    return None


def parse_output(output, rev=False):
    'Parse the output of the areca command into an associative array.'
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
            match = re.search('\[(Enclosure#.*)', lis[0])
            if match:
                append = match.group(1).replace('#', '') + "/"
                continue
            if append:
                lis[0] = "%s%s" % (append, lis[0])
            if len(lis[1]) > 1 and lis[1][-1] == '.':
                lis[1] = lis[1][:-1]
            unit = split_units(lis)
            try:
                res[lis[0].title().replace(' ', '')] = int(lis[1])
                if unit:
                    res["%s/unit" % (lis[0].title().replace(' ', ''))] = unit
            except ValueError:
                res[lis[0].title().replace(' ', '')] = lis[1]
                if unit:
                    res["%s/unit" % lis[0].title().replace(' ', '')] = unit
    return res


def split_parts(sep, output):
    'Split the output string according to the regexp sep.'
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


def run_areca(*args):
    'Run the areca command in a subprocess and return the output.'
    cmd = 'cli64 ' + ' '.join(args)
    proc = Popen(cmd,
                 shell=True,
                 stdout=PIPE,
                 universal_newlines=True)
    return proc.communicate()[0]


def run_and_parse(*args):
    '''Run the areca command in a subprocess.

Returns the output as an associative array.
'''
    res = run_areca(*args)
    return parse_output(res)


def run_and_parse_rev(*args):
    '''Run the areca command in a subprocess.

Returns the output as an associative array.
'''
    res = run_areca(*args)
    return parse_output(res, rev=True)


def adsys_info():
    'Get advanced system info.'
    arr = run_and_parse('adsys info')
    return arr


def hw_info():
    'Get hardware info.'
    arr = run_and_parse_rev('hw info')
    return arr


def sys_info():
    'Get system info.'
    arr = run_and_parse('sys info')
    return arr


def sys_showcfg():
    'Get system configuration.'
    arr = run_and_parse('sys showcfg')
    return arr


def hdd_pwr_info():
    'Get hard disk power information.'
    return run_and_parse('hddpwr info')


def disk_info(disk):
    'Get hard disk information.'
    output = run_and_parse('disk info drv=%d' % disk)
    return output


def disable_password():
    'Command to temporarly disable password on the cli'
    run_areca('set password=0000')
# areca.py ends here
