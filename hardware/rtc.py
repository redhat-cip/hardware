# Copyright (C) 2014-2015 Red Hat Inc.
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

import logging
import re
import subprocess

LOG = logging.getLogger('hardware.rtc')


def get_rtc():
    cmd = ['timedatectl', 'status', '--no-pager']
    try:
        stdout = subprocess.check_output(cmd).decode("utf-8")
    except OSError:
        LOG.warning('Unable to determine RTC timezone (no timedatectl)')
        return 'unknown'
    except subprocess.CalledProcessError as excpt:
        LOG.warning('RTC timezone command failed - %s' % excpt.output)
        return 'unknown'
    if stdout:
        match = re.search(r'RTC in local TZ: ([a-z]+)$', stdout)
        if match:
            LOG.info('Is RTC set to UTC: %s' % match.group(1))
            return match.group(1)
        LOG.warning('Unable to determine RTC timezone (no match)')
    else:
        LOG.warning('Unable to determine RTC timezone (no output)')
    return 'unknown'


def detect_rtc_clock():
    hw_lst = []
    hw_lst.append(('system', 'rtc', 'utc', get_rtc()))
    return hw_lst
