# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
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

"""Set of functions to manage IPMI."""

import os
import re
import subprocess
import sys

from hardware import detect_utils


LINE_REGEXP = re.compile(r'^([^:]+[^ ])\s*:\s*(.*[^ ])\s*$')


def setup_user(channel, username, password):
    """Setup an IPMI user."""
    sys.stderr.write('Info: ipmi_setup_user: Setting user="%s", '
                     'password="%s" on channel %s\n' %
                     (username, password, channel))
    detect_utils.cmd('ipmitool user set name 1 %s' % username)
    detect_utils.cmd('ipmitool user set password 1 %s' % password)
    detect_utils.cmd('ipmitool user priv 1 4 %s' % channel)
    detect_utils.cmd('ipmitool user enable')
    state, _ = detect_utils.cmd('ipmitool user test 1 16 %s' % password)
    if state == 0:
        sys.stderr.write('Info: ipmi_setup_user: Setting user successful !\n')

    sys.stderr.write('Err: ipmi_setup_user: Setting user failed !\n')
    return False


def restart_bmc():
    """Restart a BMC card."""
    sys.stderr.write('Info: Restarting IPMI BMC\n')
    detect_utils.cmd('ipmitool bmc reset cold')


def setup_network(channel, ipv4, netmask, gateway, vlan_id=-1):
    """Define the network of an IPMI interface."""
    sys.stderr.write('Info: ipmi_setup_network: Setting network ip="%s", '
                     'netmask="%s", gateway="%s", vland_id="%d" on '
                     'channel %s\n' %
                     (ipv4,
                      netmask,
                      gateway,
                      vlan_id,
                      channel))
    # NOTE (leseb): assuming you're missing an argument
    # and this already happened
    # ipmitool always returns 0 and prompt the valid values...
    detect_utils.cmd('ipmitool lan set %s ipsrc static' % channel)
    detect_utils.cmd('ipmitool lan set %s ipaddr %s' % (channel, ipv4))
    detect_utils.cmd('ipmitool lan set %s netmask %s' % (channel, netmask))
    detect_utils.cmd(
        'ipmitool lan set %s defgw ipaddr %s' % (channel, gateway))
    detect_utils.cmd('ipmitool lan set %s arp respond on' % channel)

    if vlan_id >= 0:
        detect_utils.cmd('ipmitool lan set %s vlan id %d' % (channel, vlan_id))
    else:
        detect_utils.cmd('ipmitool lan set %s vlan id off' % channel)

    # We need to restart the bmc to insure the setup is properly done
    restart_bmc()


def parse_lan_info(output, lst):
    """Parse the output of ipmi lan info and turns add it to the hw list."""
    for line in output.split('\n'):
        res = LINE_REGEXP.search(line)
        if res:
            lst.append(('ipmi', 'lan',
                        '-'.join([s.lower() for s in res.group(1).split(' ')]),
                        res.group(2)))
    return lst


def parse_ipmi_sdr(output):
    """Parse the output of the sdr info retrieved with ipmitool"""
    hrdw = []

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

    return hrdw


def get_ipmi_sdr():
    ipmi_cmd = subprocess.Popen("ipmitool -I open sdr",
                                shell=True,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)

    return parse_ipmi_sdr(ipmi_cmd.stdout)


def detect():
    """Detect IPMI interfaces."""

    hw_lst = []

    detect_utils.modprobe("ipmi_smb")
    detect_utils.modprobe("ipmi_si")
    detect_utils.modprobe("ipmi_devintf")
    if (os.path.exists('/dev/ipmi0')
            or os.path.exists('/dev/ipmi/0')
            or os.path.exists('/dev/ipmidev/0')):
        for channel in range(0, 16):
            status, _ = detect_utils.cmd(
                'ipmitool channel info %d 2>&1 | grep -sq Volatile' % channel)
            if status == 0:
                hw_lst.append(('system', 'ipmi', 'channel', '%s' % channel))
                break
        status, output = detect_utils.cmd('ipmitool lan print')
        if status == 0:
            parse_lan_info(output, hw_lst)

        return hw_lst

    # do we need a fake ipmi device for testing purpose ?
    status, _ = detect_utils.cmd(
        'grep -qi FAKEIPMI /proc/detect_utils.cmdline')
    if status == 0:
        # Yes ! So let's create a fake entry
        hw_lst.append(('system', 'ipmi-fake', 'channel', '0'))
        sys.stderr.write('Info: Added fake IPMI device\n')
        return hw_lst

    sys.stderr.write('Info: No IPMI device found\n')
    return hw_lst
