#
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Frederic Lepied <frederic.lepied@enovance.com>
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

'''Wrapper functions around the megacli command.'''

from __future__ import print_function
import os
import re
from subprocess import PIPE
from subprocess import Popen
import sys

SEP_REGEXP = re.compile(r'\s*:\s*')


def which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Return the path to an executable.

    Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.

    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.
    """

    # Check that a given file can be accessed with the correct mode.
    # Additionally check that `file` is not a directory, as on Windows
    # directories pass the os.access check.
    def _access_check(myfile, mode):
        return (os.path.exists(myfile) and os.access(myfile, mode)
                and not os.path.isdir(myfile))

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to
    # the current directory, e.g. ./script
    if os.path.dirname(cmd):
        if _access_check(cmd, mode):
            return cmd
        return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)

    if not path:
        return None

    path = path.split(os.pathsep)

    # On other platforms you don't have things like PATHEXT to tell you
    # what file suffixes are executable, so just pass on cmd as-is.

    files = [cmd]

    seen = set()
    for directory in path:
        normdir = os.path.normcase(directory)
        if normdir not in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(directory, thefile)
                if _access_check(name, mode):
                    return name
    return None


def search_exec(possible_names):
    prog_path = None
    for prog_name in possible_names:
        prog_path = which(prog_name)
        if prog_path is not None:
            break

    return prog_path


def parse_output(output):
    'Parse the output of the megacli command into an associative array.'
    res = {}
    for line in output.split('\n'):
        lis = re.split(SEP_REGEXP, line.strip())
        if len(lis) == 2:
            if len(lis[1]) > 1 and lis[1][-1] == '.':
                lis[1] = lis[1][:-1]
            try:
                res[lis[0].title().replace(' ', '')] = int(lis[1])
            except ValueError:
                res[lis[0].title().replace(' ', '')] = lis[1]
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


def run_megacli(*args):
    'Run the megacli command in a subprocess and return the output.'
    prog_exec = search_exec(["megacli", "MegaCli", "MegaCli64"])
    if prog_exec:
        cmd = prog_exec + ' - ' + ' '.join(args)
        proc = Popen(cmd, shell=True, stdout=PIPE, universal_newlines=True)
        return proc.communicate()[0]

    sys.stderr.write('Cannot find megacli on the system\n')
    return ""


def run_and_parse(*args):
    '''Run the megacli command in a subprocess.

Returns the output as an associative array.
'''
    res = run_megacli(*args)
    return parse_output(res)


def adp_count():
    'Get the numberof adaptaters.'
    arr = run_and_parse('adpCount')
    if 'ControllerCount' in arr:
        return int(arr['ControllerCount'])
    return 0


def adp_all_info(ctrl):
    'Get adaptater info.'
    arr = run_and_parse('adpallinfo -a%d' % ctrl)
    for key in ('RaidLevelSupported', 'SupportedDrives'):
        if key in arr:
            arr[key] = arr[key].split(', ')
    return arr


def pd_get_num(ctrl):
    'Get the number of physical drives on a controller.'
    try:
        key = 'NumberOfPhysicalDrivesOnAdapter%d' % ctrl
        return run_and_parse('PDGetNum -a%d' % ctrl)[key]
    except KeyError:
        return 0


def enc_info(ctrl):
    'Get enclosing info on a controller.'
    parts = split_parts(' +Enclosure [0-9]+:',
                        run_megacli('EncInfo -a%d' % ctrl))
    all_ = list(map(parse_output, parts))
    for entry in all_:
        for key in entry.keys():
            if re.search('Enclosure\d+', key):
                entry['Enclosure'] = int(key[len('Enclosure'):])
                del entry[key]
                break
    return all_


def pdinfo(ctrl, encl, disk):
    'Get info about a physical drive on an enclosure and a controller.'
    return run_and_parse('pdinfo -PhysDrv[%d:%d] -a%d' % (encl, disk, ctrl))


def ld_get_num(ctrl):
    'Get the number of logical drives on a controller.'
    try:
        key = 'NumberOfVirtualDrivesConfiguredOnAdapter%d' % ctrl
        return run_and_parse('LDGetNum -a%d' % ctrl)[key]
    except KeyError:
        return 0


def ld_get_info(ctrl, ldrv):
    'Get info about a logical drive on a controller.'
    return run_and_parse('LDInfo -L%d -a%d' % (ldrv, ctrl))


if __name__ == "__main__":
    import pprint

    for ctrl_num in range(adp_count()):
        print('Controler', ctrl_num)
        pprint.pprint(adp_all_info(ctrl_num))

        encs = enc_info(ctrl_num)

        print()

        print('Enclosing:')
        pprint.pprint(encs)

        for enc in encs:
            for disk_num in range(enc['NumberOfPhysicalDrives']):
                print()
                print('Physical disk', disk_num)
                pprint.pprint(pdinfo(ctrl_num, enc['DeviceId'], disk_num))

        for ld_num in range(ld_get_num(ctrl_num)):
            print()
            print('Logical disk', ld_num)
            pprint.pprint(ld_get_info(ctrl_num, ld_num))
