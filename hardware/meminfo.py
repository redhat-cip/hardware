# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

import platform
import subprocess
import sys


def get_ddr_timing():
    """Report the DDR timings"""
    ddr_timing = []

    sys.stderr.write('Reporting DDR Timings\n')
    found = False
    ddrprocess = subprocess.Popen('ddr-timings-%s' % platform.machine(),
                                  shell=True, stdout=subprocess.PIPE)
# DDR   tCL   tRCD  tRP   tRAS  tRRD  tRFC  tWR   tWTPr tRTPr tFAW  B2B
# 0 |  11    15    15    31     7   511    11    31    15    63    31

    for line in ddrprocess.stdout:
        if 'is a Triple' in line:
            ddr_timing.append(('memory', 'DDR', 'type', '3'))
            continue

        if 'is a Dual' in line:
            ddr_timing.append(('memory', 'DDR', 'type', '2'))
            continue

        if 'is a Single' in line:
            ddr_timing.append(('memory', 'DDR', 'type', '1'))
            continue

        if 'is a Zero' in line:
            ddr_timing.append(('memory', 'DDR', 'type', '0'))
            continue

        if "DDR" in line:
            found = True
            continue

        if found:
            (ddr_channel, tCL, tRCD, tRP, tRAS,
             tRRD, tRFC, tWR, tWTPr,
             tRTPr, tFAW, B2B) = line.rstrip('\n').replace('|', ' ').split()
            ddr_channel = ddr_channel.replace('#', '')
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'tCL', tCL))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'tRCD', tRCD))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'tRP', tRP))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'tRAS', tRAS))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'tRRD', tRRD))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'tRFC', tRFC))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'tWR', tWR))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel,
                               'tWTPr', tWTPr))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'tRTPr',
                               tRTPr))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'tFAW', tFAW))
            ddr_timing.append(('memory', 'DDR_%s' % ddr_channel, 'B2B', B2B))

    return ddr_timing
