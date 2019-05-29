#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Author: Erwan Velu <erwan.velu@enovance.com>
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
import platform
import subprocess
import sys


def cmd(cmdline):
    'Equivalent of commands.getstatusoutput'
    try:
        return 0, subprocess.check_output(cmdline,
                                          shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as excpt:
        return excpt.returncode, excpt.output


def output_lines(cmdline):
    "Run a shell command and returns the output as lines."
    proc = subprocess.Popen(cmdline, shell=True, stdout=subprocess.PIPE,
                            universal_newlines=True)
    stdout = proc.communicate()[0]
    return stdout.splitlines()


def parse_lldtool(hw_lst, interface_name, lines):
    content = ""
    header = ""
    sub_header = ""
    for line in lines:
        if line.startswith('\t'):
            content = line.strip().strip('\n').strip('\t').replace("/", "_")
        else:
            header = line
            header = line.strip().strip('\n').strip('\t').replace("/", "_")
            header = header.replace(" TLV", "")
            content = ""
            sub_header = ""
        if header and content:
            if ":" in content:
                line = content.split(":")
                if (len(line) == 2) and (line[1] == ''):
                    sub_header = line[0].strip().strip('\n').strip('\t')
                    sub_header = sub_header.replace("/", "_")
                    sub_header = sub_header.replace(" TLV:", "")
                    header = header + "/" + sub_header
                    continue
                else:
                    left = line[0].strip().strip('\n').strip('\t')
                    left = left.replace("/", "_")
                    right = content.replace(left + ":", "").strip().strip('\n')
                    right = right.strip('\t').replace("/", "_")
                    # If we never had this sub_header for this header
                    # let's add one
                    if left != sub_header:
                        sub_header = left
                        header = header + "/" + sub_header
                    content = right
            hw_lst.append(('lldp', interface_name, header, content))

    return hw_lst


def get_lld_status(hw_lst, interface_name):
    return parse_lldtool(hw_lst, interface_name,
                         output_lines("lldptool -t -n -i %s" % interface_name))


def parse_ethtool(hw_lst, interface_name, lines):
    content = ""
    header = ""
    sub_header = ""
    original_header = ""
    for line in lines:
        if interface_name in line:
            continue
        data = line.split(":")
        line = line.strip('\n')
        if line.startswith('\t'):
            sub_header = data[0].replace('\t', '').strip()
            header = "%s/%s" % (original_header, sub_header)
        else:
            header = data[0]
            original_header = header

        header = header.replace('\t', '').strip()
        content = ''.join(data[1:]).replace('\t', '').strip()
        if not content:
            continue
        hw_lst.append(('network', interface_name, header, content))

    return hw_lst


def get_ethtool_status(hw_lst, interface_name):
    parse_ethtool(hw_lst, interface_name,
                  output_lines("ethtool -a %s" % interface_name))
    parse_ethtool(hw_lst, interface_name,
                  output_lines("ethtool -k %s" % interface_name))


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def get_ddr_timing(hw_):
    'Report the DDR timings'
    sys.stderr.write('Reporting DDR Timings\n')
    found = False
    ddrprocess = subprocess.Popen('ddr-timings-%s' % platform.machine(),
                                  shell=True, stdout=subprocess.PIPE)
# DDR   tCL   tRCD  tRP   tRAS  tRRD  tRFC  tWR   tWTPr tRTPr tFAW  B2B
# 0 |  11    15    15    31     7   511    11    31    15    63    31

    for line in ddrprocess.stdout:
        if 'is a Triple' in line:
            hw_.append(('memory', 'DDR', 'type', '3'))
            continue

        if 'is a Dual' in line:
            hw_.append(('memory', 'DDR', 'type', '2'))
            continue

        if 'is a Single' in line:
            hw_.append(('memory', 'DDR', 'type', '1'))
            continue

        if 'is a Zero' in line:
            hw_.append(('memory', 'DDR', 'type', '0'))
            continue

        if "DDR" in line:
            found = True
            continue

        if found is True:
            (ddr_channel, tCL, tRCD, tRP, tRAS,
             tRRD, tRFC, tWR, tWTPr,
             tRTPr, tFAW, B2B) = line.rstrip('\n').replace('|', ' ').split()
            ddr_channel = ddr_channel.replace('#', '')
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tCL', tCL))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRCD', tRCD))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRP', tRP))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRAS', tRAS))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRRD', tRRD))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRFC', tRFC))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tWR', tWR))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tWTPr', tWTPr))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tRTPr', tRTPr))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'tFAW', tFAW))
            hw_.append(('memory', 'DDR_%s' % ddr_channel, 'B2B', B2B))


def parse_ipmi_sdr(hrdw, output):
    for line in output:
        items = line.split("|")
        if len(items) < 3:
            continue

        if "Not Readable" in line:
            hrdw.append(('ipmi', items[0].strip(), 'value', 'Not Readable'))
            continue

        hrdw.append(('ipmi', items[0].strip(), 'value',
                     '%s' % items[1].split()[0].strip()))
        units = ""
        for unit in items[1].split()[1:]:
            units = "%s %s" % (units, unit.strip())
        units = units.strip()
        if units:
            hrdw.append(('ipmi', items[0].strip(), 'unit', units))


def ipmi_sdr(hrdw):
    ipmi_cmd = subprocess.Popen("ipmitool -I open sdr",
                                shell=True,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)
    parse_ipmi_sdr(hrdw, ipmi_cmd.stdout)
