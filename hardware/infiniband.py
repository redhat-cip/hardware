# Copyright (C) 2013-2015 eNovance SAS <licensing@enovance.com>
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

"""Fetch information about Infiniband cards."""

import re
import sys

from hardware import detect_utils
from hardware.detect_utils import cmd


def ib_card_drv():
    """Return an array of IB devices (ex: ['mlx4_0'])."""
    ret, output = cmd('ibstat -l')
    if ret == 0:
        # Use filter to omit empty item due to trailing newline.
        return list(filter(None, output.split('\n')))

    return []


# {'node_guid': '0x0002c90300ea6840', 'sys_guid': '0x0002c90300ea6843',
#  'fw_ver': '2.11.500',
#   'device_type': 'MT4099',
#   'hw_ver': '0', 'nb_ports': '2'}
def ib_global_info(card_drv):
    """Return global info of a IB card in a python dict.

    :param card_drv: a card device ID (e.g. mlx4_0)
    :returns: a list containing information on the card device
    """
    global_card_info = {}
    ret, global_info = cmd('ibstat %s -s' % card_drv)
    if ret == 0:
        for line in global_info.split('\n'):
            re_dev = re.search('CA type: (.*)', line)
            if re_dev is not None:
                global_card_info['device_type'] = re_dev.group(1)
            re_nb_ports = re.search('Number of ports: (.*)', line)
            if re_nb_ports is not None:
                global_card_info['nb_ports'] = re_nb_ports.group(1)
            re_fw_ver = re.search('Firmware version: (.*)', line)
            if re_fw_ver is not None:
                global_card_info['fw_ver'] = re_fw_ver.group(1)
            re_hw_ver = re.search('Hardware version: (.*)', line)
            if re_hw_ver is not None:
                global_card_info['hw_ver'] = re_hw_ver.group(1)
            re_node_guid = re.search('Node GUID: (.*)', line)
            if re_node_guid is not None:
                global_card_info['node_guid'] = re_node_guid.group(1)
            re_sys_guid = re.search('System image GUID: (.*)', line)
            if re_sys_guid is not None:
                global_card_info['sys_guid'] = re_sys_guid.group(1)
    return global_card_info


# {'base_lid': '0', 'port_guid': '0x0002c90300ea6841', 'rate': '40',
# 'physical_state': 'Down', 'sm_lid': '0', 'state': 'Down', 'lmc': '0'}
def ib_port_info(card_drv, port):
    """Return port infos of a IB card_drv in a python dict.

    :param card_drv: a card device ID (e.g. mlx4_0)
    :param port: the port number (e.g. 1)
    :returns: a list containing information on the port
    """
    port_infos = {}
    ret, port_desc = cmd('ibstat %s %i' % (card_drv, port))
    if ret == 0:
        for line in port_desc.split('\n'):
            re_state = re.search('State: (.*)', line)
            if re_state is not None:
                port_infos['state'] = re_state.group(1)
            re_phy_state = re.search('State: (.*)', line)
            if re_phy_state is not None:
                port_infos['physical_state'] = re_phy_state.group(1)
            re_rate = re.search('Rate: (.*)', line)
            if re_rate is not None:
                port_infos['rate'] = re_rate.group(1)
            re_blid = re.search('Base lid: (.*)', line)
            if re_blid is not None:
                port_infos['base_lid'] = re_blid.group(1)
            re_lmc = re.search('LMC: (.*)', line)
            if re_lmc is not None:
                port_infos['lmc'] = re_lmc.group(1)
            re_smlid = re.search('SM lid: (.*)', line)
            if re_smlid is not None:
                port_infos['sm_lid'] = re_smlid.group(1)
            re_pguid = re.search('Port GUID: (.*)', line)
            if re_pguid is not None:
                port_infos['port_guid'] = re_pguid.group(1)
    return port_infos


def detect():
    """Detect Infiniband devices.

    To detect if an IB device is present, we search for a pci device.
    This pci device shall be from vendor Mellanox (15b3) from class 0280
    Class 280 stands for a Network Controller while ethernet device are 0200.
    """
    hw_lst = []
    status, _ = detect_utils.cmd(
        "lspci -d 15b3: -n|awk '{print $2}'|grep -q '0280'")
    if status != 0:
        sys.stderr.write('Info: No Infiniband device found\n')
        return []

    for ib_card in range(len(ib_card_drv())):
        card_type = ib_card_drv()[ib_card]
        ib_infos = ib_global_info(card_type)
        nb_ports = ib_infos['nb_ports']
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'card_type', card_type))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'device_type', ib_infos['device_type']))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'fw_version', ib_infos['fw_ver']))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'hw_version', ib_infos['hw_ver']))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'nb_ports', nb_ports))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'sys_guid', ib_infos['sys_guid']))
        hw_lst.append(('infiniband', 'card%i' % ib_card,
                       'node_guid', ib_infos['node_guid']))
        for port in range(1, int(nb_ports) + 1):
            ib_port_infos = ib_port_info(card_type, port)
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'state', ib_port_infos['state']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'physical_state',
                           ib_port_infos['physical_state']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'rate', ib_port_infos['rate']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'base_lid', ib_port_infos['base_lid']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'lmc', ib_port_infos['lmc']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'sm_lid', ib_port_infos['sm_lid']))
            hw_lst.append(('infiniband', 'card%i_port%i' % (ib_card, port),
                           'port_guid', ib_port_infos['port_guid']))
    return hw_lst
