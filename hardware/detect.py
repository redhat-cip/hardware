#
# Copyright (C) 2013-2015 eNovance SAS <licensing@enovance.com>
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

"""Main entry point for hardware and system detection routines in eDeploy."""


from __future__ import print_function
import argparse
import fcntl
import json
import os
import pprint
import re
import socket
import struct
from subprocess import PIPE
from subprocess import Popen
import sys
import uuid
import xml.etree.ElementTree as ET

from netaddr import IPNetwork

from hardware import areca
from hardware.benchmark import cpu as bm_cpu
from hardware.benchmark import disk as bm_disk
from hardware.benchmark import mem as bm_mem
from hardware import bios_hp
from hardware import detect_utils
from hardware.detect_utils import cmd
from hardware import diskinfo
from hardware import hpacucli
from hardware import infiniband as ib
from hardware import ipmi
from hardware import megacli
from hardware import rtc

SIOCGIFNETMASK = 0x891b


def size_in_gb(size):
    'Return the size in GB without the unit.'
    ret = size.replace(' ', '')
    if ret[-2:] == 'GB':
        return ret[:-2]

    if ret[-2:] == 'TB':
        # some size are provided in x.yGB
        # we need to compute the size in TB by
        # considering the input as a float to be
        # multiplied by 1000
        return str(int(float(ret[:-2]) * 1000))

    return ret


def detect_hpa(hw_lst):
    'Detect HP RAID controller configuration.'
    disk_count = 0
    try:
        cli = hpacucli.Cli(debug=False)
        if not cli.launch():
            return False
        controllers = cli.ctrl_all_show()
        if not controllers:
            sys.stderr.write("Info: No hpa controller found\n")
            return False

    except hpacucli.Error as expt:
        sys.stderr.write('Info: detect_hpa : %s\n' % expt.value)
        return False

    hw_lst.append(('hpa', "slots", "count", str(len(controllers))))
    global_pdisk_size = 0
    for controller in controllers:
        try:
            slot = 'slot=%d' % controller[0]
            controllers_infos = cli.ctrl_show(slot)
            for controller_info in controllers_infos.keys():
                hw_lst.append(('hpa', slot.replace('=', '_'),
                               controller_info,
                               controllers_infos[controller_info]))
            for _, disks in cli.ctrl_pd_all_show(slot):
                for disk in disks:
                    disk_count += 1
                    hw_lst.append(('disk', disk[0], 'type', disk[1]))
                    hw_lst.append(('disk', disk[0], 'slot',
                                   str(controller[0])))
                    disk_infos = cli.ctrl_pd_disk_show(slot, disk[0])
                    for disk_info in disk_infos.keys():
                        value = disk_infos[disk_info]
                        if disk_info == "size":
                            value = size_in_gb(disk_infos[disk_info])
                            global_pdisk_size = (
                                global_pdisk_size + float(value))
                        hw_lst.append(('disk', disk[0], disk_info,
                                       value))
        except hpacucli.Error as expt:
            sys.stderr.write('Info: detect_hpa : controller %d : %s\n'
                             % (controller[0], expt.value))

    if global_pdisk_size > 0:
        hw_lst.append(('disk', 'hpa', 'size', "%.2f" % global_pdisk_size))

    hw_lst.append(('disk', 'hpa', 'count', str(disk_count)))
    return True


def detect_areca(hw_lst):
    'Detect Areca controller configuration'
    device = areca.sys_info()
    if not device:
        sys.stderr.write('Info: detect_areca: No controller found\n')
        return
    if "ControllerName" not in device.keys():
        sys.stderr.write('Info: detect_areca: Cannot found controller name\n')
        return

    sys.stderr.write('Info: detect_areca: Found %s version %s\n' %
                     (device['ControllerName'], device['FirmwareVersion']))

    areca.disable_password()

    for info in device.keys():
        hw_lst.append(('areca', 'system', info, device[info]))

    adsys = areca.adsys_info()
    for info in adsys.keys():
        hw_lst.append(('areca', 'system', info, adsys[info]))

    cfg = areca.sys_showcfg()
    for info in cfg.keys():
        hw_lst.append(('areca', 'config', info, cfg[info]))

    hw_info = areca.hw_info()
    for info in hw_info.keys():
        hw_lst.append(('areca', 'hardware', info, hw_info[info]))

    pwr_info = areca.hdd_pwr_info()
    for info in pwr_info.keys():
        hw_lst.append(('areca', 'power', info, pwr_info[info]))

    for disk_number in range(1, 255):
        disk_info = areca.disk_info(disk_number)
        # If we don't have info about that disk, let's stop here
        if len(disk_info) < 2:
            break
        # Extracting disk information
        for info in disk_info:
            hw_lst.append(('areca', "disk%d" % disk_number, info,
                           disk_info[info]))


def detect_megacli(hw_lst):
    'Detect LSI MegaRAID controller configuration.'
    ctrl_num = megacli.adp_count()
    disk_count = 0
    global_pdisk_size = 0
    if ctrl_num > 0:
        for ctrl in range(ctrl_num):
            ctrl_info = megacli.adp_all_info(ctrl)
            for entry in ctrl_info.keys():
                hw_lst.append(('megaraid', 'Controller_%d' % (ctrl),
                               '%s' % entry, '%s' % ctrl_info[entry]))

            for enc in megacli.enc_info(ctrl):
                if "Enclosure" in enc.keys():
                    for key in enc.keys():
                        if "ExitCode" in key or "Enclosure" in key:
                            continue
                        hw_lst.append(('megaraid',
                                       'Controller_%d/Enclosure_%s' %
                                       (ctrl, enc["Enclosure"]),
                                       '%s' % key, '%s' % enc[key]))

                for slot_num in range(enc['NumberOfSlots']):
                    disk = 'disk%d' % slot_num
                    info = megacli.pdinfo(ctrl,
                                          enc['DeviceId'],
                                          slot_num)

                    # If no PdType, it means that's not a disk
                    if 'PdType' not in info.keys():
                        continue

                    disk_count += 1
                    hw_lst.append(('pdisk',
                                   disk,
                                   'ctrl',
                                   str(ctrl_num)))
                    hw_lst.append(('pdisk',
                                   disk,
                                   'type',
                                   info['PdType']))
                    hw_lst.append(('pdisk',
                                   disk,
                                   'id',
                                   '%s:%d' % (info['EnclosureDeviceId'],
                                              slot_num)))
                    disk_size = size_in_gb("%s %s" %
                                           (info['CoercedSize'].split()[0],
                                            info['CoercedSize'].split()[1]))
                    global_pdisk_size = global_pdisk_size + float(disk_size)
                    hw_lst.append(('pdisk',
                                   disk,
                                   'size',
                                   disk_size))

                    for key in info.keys():
                        ignore_list = ['PdType', 'EnclosureDeviceId',
                                       'CoercedSize', 'ExitCode']
                        if key not in ignore_list:
                            if "DriveTemperature" in key:
                                if "C" in str(info[key].split()[0]):
                                    pdisk = info[key].split()[0].split("C")[0]
                                    hw_lst.append(('pdisk', disk, key,
                                                   str(pdisk).strip()))
                                    hw_lst.append(('pdisk', disk,
                                                   "%s_units" % key,
                                                   "Celsius"))
                                else:
                                    hw_lst.append(('pdisk', disk, key,
                                                   str(info[key]).strip()))

                            elif "InquiryData" in key:
                                count = 0
                                for mystring in info[key].split():
                                    hw_lst.append(('pdisk', disk,
                                                   "%s[%d]" % (key, count),
                                                   str(mystring.strip())))
                                    count = count + 1

                            else:
                                hw_lst.append(('pdisk', disk, key,
                                               str(info[key]).strip()))

                if global_pdisk_size > 0:
                    hw_lst.append(('pdisk',
                                   'all',
                                   'size',
                                   "%.2f" % global_pdisk_size))

                for ld_num in range(megacli.ld_get_num(ctrl)):
                    disk = 'disk%d' % ld_num
                    info = megacli.ld_get_info(ctrl, ld_num)
                    ignore_list = ['Size']

                    for item in info.keys():
                        if item not in ignore_list:
                            hw_lst.append(('ldisk',
                                           disk,
                                           item,
                                           str(info[item])))
                    if 'Size' in info:
                        hw_lst.append(('ldisk',
                                       disk,
                                       'Size',
                                       size_in_gb(info['Size'])))
        hw_lst.append(('disk', 'megaraid', 'count', str(disk_count)))
        return True
    else:
        return False


def detect_disks(hw_lst):
    'Detect disks.'
    names = diskinfo.disknames()
    sizes = diskinfo.disksizes(names)
    disks = [name for name, size in sizes.items() if size > 0]
    hw_lst.append(('disk', 'logical', 'count', str(len(disks))))
    for name in disks:
        hw_lst.append(('disk', name, 'size', str(sizes[name])))
        item_list = ['device/vendor', 'device/model', 'device/rev',
                     'queue/optimal_io_size', 'queue/physical_block_size',
                     'queue/rotational', 'queue/nr_requests']
        for my_item in item_list:
            try:
                with open('/sys/block/%s/%s' % (name, my_item), 'r') as dev:
                    hw_lst.append(('disk', name, my_item.split('/')[1],
                                   dev.readline().rstrip('\n').strip()))
            except Exception as excpt:
                sys.stderr.write(
                    'Failed at getting disk information '
                    'at /sys/block/%s/device/%s: %s\n' % (name,
                                                          my_item,
                                                          str(excpt)))

        try:
            with open('/sys/block/%s/queue/scheduler' % name, 'r') as dev:
                s_line = dev.readline().rstrip('\n').strip()
                sched = re.findall(r'\[(.*?)\]', s_line)
                if sched:
                    hw_lst.append(('disk', name, 'scheduler', sched[0]))

        except Exception:
            sys.stderr.write('Cannot extract scheduler for disk %s' % name)

        # WCE & RCD from sysfs
        # https://www.kernel.org/doc/Documentation/scsi/sd-parameters.txt
        my_item = '/sys/block/{0}/device'.format(name)
        try:
            _link_info = os.readlink(my_item)
            _scsi_addr = _link_info.rsplit('/', 1)[1]
            my_item = ('/sys/block/{0}/device' +
                       '/scsi_disk/{1}/cache_type').format(name, _scsi_addr)
            with open(my_item, 'r') as cache_info:
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
        except Exception as excpt:
            sys.stderr.write(
                'Failed at getting disk information '
                'at %s: %s\n' % (my_item, str(excpt)))

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

        detect_utils.read_SMART(hw_lst, "/dev/%s" % name)


def modprobe(module):
    'Load a kernel module using modprobe.'
    status, _ = cmd('modprobe %s' % module)
    if status == 0:
        sys.stderr.write('Info: Probing %s failed\n' % module)


def detect_ipmi(hw_lst):
    'Detect IPMI interfaces.'
    modprobe("ipmi_smb")
    modprobe("ipmi_si")
    modprobe("ipmi_devintf")
    if (os.path.exists('/dev/ipmi0') or os.path.exists('/dev/ipmi/0') or
            os.path.exists('/dev/ipmidev/0')):
        for channel in range(0, 16):
            status, _ = cmd('ipmitool channel info %d 2>&1 | grep -sq Volatile'
                            % channel)
            if status == 0:
                hw_lst.append(('system', 'ipmi', 'channel', '%s' % channel))
                break
        status, output = cmd('ipmitool lan print')
        if status == 0:
            ipmi.parse_lan_info(output, hw_lst)

        return True

    # do we need a fake ipmi device for testing purpose ?
    status, _ = cmd('grep -qi FAKEIPMI /proc/cmdline')
    if status == 0:
        # Yes ! So let's create a fake entry
        hw_lst.append(('system', 'ipmi-fake', 'channel', '0'))
        sys.stderr.write('Info: Added fake IPMI device\n')
        return True

    sys.stderr.write('Info: No IPMI device found\n')
    return False


def get_cidr(netmask):
    'Convert a netmask to a CIDR.'
    binary_str = ''
    for octet in netmask.split('.'):
        binary_str += bin(int(octet))[2:].zfill(8)
    return str(len(binary_str.rstrip('0')))


def detect_infiniband(hw_lst):
    '''Detect Infiniband devinces.

To detect if an IB device is present, we search for a pci device.
This pci device shall be from vendor Mellanox (15b3) form class 0280
Class 280 stands for a Network Controller while ethernet device are 0200.
'''
    status, _ = cmd("lspci -d 15b3: -n|awk '{print $2}'|grep -q '0280'")
    if status != 0:
        sys.stderr.write('Info: No Infiniband device found\n')
        return False

    for ib_card in range(len(ib.ib_card_drv())):
        card_type = ib.ib_card_drv()[ib_card]
        ib_infos = ib.ib_global_info(card_type)
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
            ib_port_infos = ib.ib_port_info(card_type, port)
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
    return True


def _get_uuid_x86_64():
    'Get uuid from dmidecode'
    uuid_cmd = Popen("dmidecode -t 1 | grep UUID | "
                     "awk '{print $2}'",
                     shell=True,
                     stdout=PIPE,
                     universal_newlines=True)
    stdout = uuid_cmd.communicate()[0]
    return stdout.rstrip()


def _get_uuid_ppc64le(hw_lst):
    vendor = None
    serial = None
    for (_, _, sys_subtype, value) in hw_lst:
        if sys_subtype == 'vendor':
            vendor = value
        if sys_subtype == 'serial':
            serial = value

    system_uuid = None
    system_uuid_fname = '/sys/firmware/devicetree/base/system-uuid'
    if os.access(system_uuid_fname, os.R_OK):
        with open(system_uuid_fname) as uuidfile:
            system_uuid = uuidfile.read().rstrip(' \t\r\n\0')
    elif vendor and serial:
        root = uuid.UUID(bytes=b'\x00' * 16)
        vendor_uuid = uuid.uuid5(root, vendor)
        system_uuid = str(uuid.uuid5(vendor_uuid, serial))

    return system_uuid


def get_uuid(hw_lst):
    if os.uname()[4] == 'ppc64le':
        return _get_uuid_ppc64le(hw_lst)
    return _get_uuid_x86_64()


def _get_value(hw_lst, *vect):
    for i in hw_lst:
        if i[0:3] == vect:
            return i[3]
    return ''


def detect_system(hw_lst, output=None):
    'Detect system characteristics from the output of lshw.'

    def find_element(xml, xml_spec, sys_subtype,
                     sys_type='product', sys_cls='system',
                     attrib=None, transform=None):
        'Lookup an xml element and populate hw_lst when found.'
        elt = xml.findall(xml_spec)
        if len(elt) >= 1:
            if attrib:
                txt = elt[0].attrib[attrib]
            else:
                txt = elt[0].text
            if transform:
                txt = transform(txt)
            hw_lst.append((sys_cls, sys_type, sys_subtype, txt))
            return txt
        return None

    # handle output injection for testing purpose
    if output:
        status = 0
    else:
        status, output = cmd('lshw -xml')
    if status == 0:
        mobo_id = ''
        nic_id = ''
        xml = ET.fromstring(output)
        find_element(xml, "./node/serial", 'serial')
        find_element(xml, "./node/product", 'name')
        find_element(xml, "./node/vendor", 'vendor')
        find_element(xml, "./node/version", 'version')
        uuid = get_uuid(hw_lst)

        if uuid:
            # If we have an uuid, we shall check if it's part of a
            # known list of broken uuid
            # If so let's delete the uuid instead of reporting a stupid thing
            if uuid in ['Not']:
                uuid = ''
            else:
                hw_lst.append(('system', 'product', 'uuid', uuid))

        for elt in xml.findall(".//node[@id='core']"):
            name = elt.find('physid')
            if name is not None:
                find_element(elt, 'product', 'name', 'motherboard', 'system')
                find_element(elt, 'vendor', 'vendor', 'motherboard', 'system')
                find_element(elt, 'version', 'version', 'motherboard',
                             'system')
                find_element(elt, 'serial', 'serial', 'motherboard', 'system')
                mobo_id = _get_value(hw_lst, 'system', 'motherboard', 'serial')

        for elt in xml.findall(".//node[@id='firmware']"):
            name = elt.find('physid')
            if name is not None:
                find_element(elt, 'version', 'version', 'bios', 'firmware')
                find_element(elt, 'date', 'date', 'bios', 'firmware')
                find_element(elt, 'vendor', 'vendor', 'bios', 'firmware')

        bank_count = 0
        for elt in xml.findall(".//node[@class='memory']"):
            if not elt.attrib['id'].startswith('memory'):
                continue
            try:
                location = re.search('memory(:.*)', elt.attrib['id']).group(1)
            except AttributeError:
                location = ''
            name = elt.find('physid')
            if name is not None:
                find_element(elt, 'size', 'size', 'total', 'memory')
                for bank_list in elt.findall(".//node[@id]"):
                    if 'bank:' in bank_list.get('id'):
                        bank_count = bank_count + 1
                        for bank in elt.findall(".//node[@id='%s']" %
                                                (bank_list.get('id'))):
                            bank_id = bank_list.get('id').replace("bank:",
                                                                  "bank" +
                                                                  location +
                                                                  ":")
                            find_element(bank, 'size', 'size',
                                         bank_id, 'memory')
                            find_element(bank, 'clock', 'clock',
                                         bank_id, 'memory')
                            find_element(bank, 'description', 'description',
                                         bank_id, 'memory')
                            find_element(bank, 'vendor', 'vendor',
                                         bank_id, 'memory')
                            find_element(bank, 'product', 'product',
                                         bank_id, 'memory')
                            find_element(bank, 'serial', 'serial',
                                         bank_id, 'memory')
                            find_element(bank, 'slot', 'slot',
                                         bank_id, 'memory')
        if bank_count > 0:
            hw_lst.append(('memory', 'banks', 'count', str(bank_count)))

        for elt in xml.findall(".//node[@class='network']"):
            name = elt.find('logicalname')
            if name is not None:
                find_element(elt, 'businfo', 'businfo', name.text, 'network')
                find_element(elt, 'vendor', 'vendor', name.text, 'network')
                find_element(elt, 'product', 'product', name.text, 'network')
                find_element(elt, "configuration/setting[@id='firmware']",
                             'firmware', name.text, 'network', 'value')
                find_element(elt, 'size', 'size', name.text, 'network')
                ipv4 = find_element(elt, "configuration/setting[@id='ip']",
                                    'ipv4',
                                    name.text, 'network', 'value')
                if ipv4 is not None:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    try:
                        netmask = socket.inet_ntoa(
                            fcntl.ioctl(
                                sock, SIOCGIFNETMASK,
                                struct.pack('256s',
                                            name.text.encode('utf-8')))[20:24])
                        hw_lst.append(
                            ('network', name.text, 'ipv4-netmask', netmask))
                        cidr = get_cidr(netmask)
                        hw_lst.append(
                            ('network', name.text, 'ipv4-cidr', cidr))
                        hw_lst.append(
                            ('network', name.text, 'ipv4-network',
                             "%s" % IPNetwork('%s/%s' % (ipv4, cidr)).network))
                    except Exception as excpt:
                        sys.stderr.write('unable to get info for %s: %s\n'
                                         % (name.text, str(excpt)))

                find_element(elt, "configuration/setting[@id='link']", 'link',
                             name.text, 'network', 'value')
                find_element(elt, "configuration/setting[@id='driver']",
                             'driver', name.text, 'network', 'value')
                find_element(elt, "configuration/setting[@id='duplex']",
                             'duplex', name.text, 'network', 'value')
                find_element(elt, "configuration/setting[@id='speed']",
                             'speed', name.text, 'network', 'value')
                find_element(elt, "configuration/setting[@id='latency']",
                             'latency', name.text, 'network', 'value')
                find_element(elt,
                             "configuration/setting[@id='autonegotiation']",
                             'autonegotiation', name.text, 'network', 'value')

                # lshw is not able to get the complete mac addr for ib
                # devices Let's workaround it with an ip command.
                if name.text.startswith('ib'):
                    cmds = "ip addr show %s | grep link | awk '{print $2}'"
                    status_ip, output_ip = cmd(cmds % name.text)
                    if status_ip == 0:
                        hw_lst.append(('network',
                                       name.text,
                                       'serial',
                                       output_ip.split('\n')[0].lower()))
                else:
                    find_element(elt, 'serial', 'serial', name.text, 'network',
                                 transform=lambda x: x.lower())

                if not nic_id:
                    nic_id = _get_value(hw_lst, 'network',
                                        name.text, 'serial')
                    nic_id = nic_id.replace(':', '')

                detect_utils.get_ethtool_status(hw_lst, name.text)
                detect_utils.get_lld_status(hw_lst, name.text)

        fix_bad_serial(hw_lst, uuid, mobo_id, nic_id)

    else:
        sys.stderr.write("Unable to run lshw: %s\n" % output)
        return False

    get_cpus(hw_lst)

    osvendor_cmd = detect_utils.output_lines("lsb_release -is")
    for line in osvendor_cmd:
        hw_lst.append(('system', 'os', 'vendor', line.rstrip('\n').strip()))

    osinfo_cmd = detect_utils.output_lines("lsb_release -ds | tr -d '\"'")
    for line in osinfo_cmd:
        hw_lst.append(('system', 'os', 'version', line.rstrip('\n').strip()))

    uname_cmd = detect_utils.output_lines("uname -r")
    for line in uname_cmd:
        hw_lst.append(('system', 'kernel', 'version',
                       line.rstrip('\n').strip()))

    arch_cmd = detect_utils.output_lines("uname -i")
    for line in arch_cmd:
        hw_lst.append(('system', 'kernel', 'arch', line.rstrip('\n').strip()))

    cmdline_cmd = detect_utils.output_lines("cat /proc/cmdline")
    for line in cmdline_cmd:
        hw_lst.append(('system', 'kernel', 'cmdline',
                       line.rstrip('\n').strip()))
    return True


def _from_file(fname, mapping=None, default=None):
    file_exists = os.path.exists(fname)
    value = None
    if file_exists:
        with open(fname) as f:
            value = f.readline().rstrip('\n')
        if mapping:
            value = mapping.get(value, default)
    return (file_exists, value)


def get_cpus(hw_lst):
    def _maybe_int(v):
        try:
            base = 10
            if 'x' in v:
                base = 16
            v = int(v, base)
        except Exception:
            pass
        return v

    # Extracting lspcu information
    lscpu = {}
    output = detect_utils.output_lines('LANG=en_US.UTF-8 lscpu')

    for line in output:
        if ':' in line:
            item, value = line.split(':')
            lscpu[item.strip(':')] = value.strip()

    # Extracting lspcu -x information
    lscpux = {}
    output = detect_utils.output_lines('LANG=en_US.UTF-8 lscpu -x')

    for line in output:
        if ':' in line:
            item, value = line.split(':')
            lscpux[item.strip(':')] = value.strip()

    hw_lst.append(("cpu", "physical", "number", int(lscpu["Socket(s)"])))
    for processor in range(int(lscpu["Socket(s)"])):
        ptag = "physical_{}".format(processor)
        (exists, value) = _from_file("/sys/devices/system/cpu/cpufreq/boost",
                                     mapping={'1': 'enabled'},
                                     default='disabled')
        if exists:
            hw_lst.append(('cpu', ptag, 'boost', value))

        for (t_key, d_key, conv) in [('vendor', 'Vendor ID', None),
                                     ('product', 'Model name', None),
                                     ('cores', 'Core(s) per socket', int),
                                     ('threads', None, None),
                                     ('family', 'CPU family', int),
                                     ('model', 'Model', _maybe_int),
                                     ('stepping', 'Stepping', _maybe_int),
                                     ('l1d cache', 'L1d cache', None),
                                     ('l1i cache', 'L1i cache', None),
                                     ('l2 cache', 'L2 cache', None),
                                     ('l3 cache', 'L3 cache', None),
                                     ('min_Mhz', 'CPU min MHz', float),
                                     ('max_Mhz', 'CPU max MHz', float),
                                     ('current_Mhz', 'CPU MHz', float),
                                     ('flags', 'Flags', None)]:
            value = None
            if d_key in lscpu:
                value = lscpu[d_key]
                if conv:
                    value = conv(value)
            elif t_key == 'threads':
                value = (int(lscpu.get('Thread(s) per core', 1)) *
                         int(lscpu.get('Core(s) per socket', 1)))
            if value is not None:
                hw_lst.append(('cpu', ptag, t_key, value))

    hw_lst.append(('cpu', 'logical', 'number', int(lscpu['CPU(s)'])))
    # Governors could be different on logical cpus
    for cpu in range(int(lscpu['CPU(s)'])):
        ltag = "logical_{}".format(cpu)
        (exists, value) = _from_file(("/sys/devices/system/cpu/cpufreq/"
                                      "policy{}/scaling_governor".format(cpu)))
        if exists:
            hw_lst.append(('cpu', ltag, "governor", value))

    # Extracting numa nodes
    hw_lst.append(('numa', 'nodes', 'count', int(lscpu['NUMA node(s)'])))

    # Allow for sparse numa nodes.
    numa_nodes = []
    for key in lscpux:
        match = re.match('NUMA node(\d+) CPU\(s\)', key)
        if match:
            numa_nodes.append((key, int(match.groups()[0])))
    # NOTE(tonyb): Explictly sort the list as prior to python 3.7? keys() did
    # not have a predictable ordering and there maybe consumers of hw_lst rely
    # on that.
    numa_nodes.sort(key=lambda t: t[1])
    for (key, node_id) in numa_nodes:
        ntag = 'node_{}'.format(node_id)
        cpus = lscpu[key]
        # lscpu -x provides the cpu mask
        cpu_mask = lscpux[key]
        total_cpus = 0
        min_cpu = None
        max_cpu = None

        # It's possible to have a NUMA node without any CPUs
        if cpus:
            for item in cpus.split(','):
                # lscpu report numa nodes like 0-5,48-53
                if "-" in item:
                    max_cpu = int(item.split("-")[1])
                    min_cpu = int(item.split("-")[0])
                    total_cpus = total_cpus + max_cpu - min_cpu + 1
                else:
                    # or like 0,1
                    if min_cpu is None:
                        min_cpu = int(item)
                    else:
                        max_cpu = int(item)
                        total_cpus = total_cpus + max_cpu - min_cpu + 1

        # total_cpus = 12 for "0-5,48-53"
        hw_lst.append(('numa', ntag, 'cpu_count', total_cpus))
        hw_lst.append(('numa', ntag, 'cpu_mask', cpu_mask))


def fix_bad_serial(hw_lst, uuid, mobo_id, nic_id):
    'Fix bad serial number'
    # Let's manage a quirk list of stupid serial numbers TYAN
    # or Supermicro are known to provide dirty serial numbers
    # In that case, let's use another serial
    for i in hw_lst:
        if i[0:3] == ('system', 'product', 'serial'):
            # Does the current serial number is part of the quirk list
            if i[3] in ['0123456789', '0000000000']:

                # Let's delete the stupid SN and use the another ID instead
                # Items are ordered by level of confidence
                new_serial = ''

                if uuid:
                    new_serial = uuid
                elif mobo_id:
                    new_serial = mobo_id
                elif nic_id:
                    new_serial = nic_id

                if new_serial:
                    hw_lst.remove(i)
                    hw_lst.append(('system', 'product', 'serial',
                                   new_serial))

                break


def read_hwmon(hwlst, entry, sensor, label_name, appendix, processor_num,
               entry_name):
    try:
        hwmon = "%s_%s" % (sensor, appendix)
        filename = "/sys/devices/platform/%s/%s" % (entry, hwmon)
        if not os.path.isfile(filename):
            if len(hwmon) > 16:
                # Some kernels are shortening the filename to 17 chars
                # Let's try to find if we are in this case
                filename = "/sys/devices/platform/%s/%s" % (entry, hwmon[:16])
                if not os.path.isfile(filename):
                    sys.stderr.write("read_hwmon: No entry found for %s/%s\n" %
                                     (label_name, entry_name))
                    return
            else:
                sys.stderr.write("read_hwmon: No entry found for %s/%s\n" %
                                 (label_name, entry_name))
                return

        value = open(filename, 'r').readline().strip()
        hwlst.append(('cpu', 'physical_%d' % processor_num, "%s/%s" %
                      (label_name, entry_name), value))
    except Exception:
        pass


def detect_temperatures(hwlst):
    for entry in os.listdir("/sys/devices/platform/"):
        if entry.startswith("coretemp."):
            processor_num = int(entry.split(".")[1])
            for label in os.listdir("/sys/devices/platform/%s" % entry):
                if label.startswith("temp") and label.endswith("_label"):
                    sensor = label.split("_")[0]
                    try:
                        with open("/sys/devices/platform/%s/%s_label" %
                                  (entry, sensor), 'r') as fsensor:
                            label_name = fsensor.readline()
                            label_name = label_name.strip().replace(" ", "_")
                    except Exception:
                        sys.stderr.write("detect_temperatures: "
                                         "Cannot open label on %s/%s\n" %
                                         (entry, sensor))
                        continue

                    read_hwmon(hwlst, entry, sensor, label_name, "input",
                               processor_num, "temperature")
                    read_hwmon(hwlst, entry, sensor, label_name, "max",
                               processor_num, "max")
                    read_hwmon(hwlst, entry, sensor, label_name, "crit",
                               processor_num, "critical")
                    read_hwmon(hwlst, entry, sensor, label_name, "crit_alarm",
                               processor_num, "critical_alarm")


def detect_rtc_clock(hw_lst):
    hw_lst.append(('system', 'rtc', 'utc', rtc.get_rtc()))


def parse_ahci(hrdw, words):
    if len(words) < 4:
        return
    if "flags" in words[2]:
        flags = ""
        for flag in sorted(words[3:]):
            flags = "%s %s" % (flags, flag)
        hrdw.append(('ahci', words[1], "flags", flags.strip()))


def parse_dmesg(hrdw, output):
    for line in output.split('\n'):
        words = line.strip().split(" ")

        if words[0].startswith("[") and words[0].endswith("]"):
            words = words[1:]

        if not words:
            continue

        if "ahci" in words[0]:
            parse_ahci(hrdw, words)


def clean_str(val):
    'Cleanup a bad string (invalid UTF-8 encoding)'
    if isinstance(val, bytes):
        val = val.decode('UTF-8', 'replace')
    return val


def clean_tuples(lst):
    'Clean a list of tuples from bad UTF-8 strings'
    return [tuple([clean_str(val) for val in elt]) for elt in lst]


def _main(options):
    'Command line entry point.'
    hrdw = []
    detect_areca(hrdw)
    detect_hpa(hrdw)
    detect_megacli(hrdw)
    detect_disks(hrdw)
    if not detect_system(hrdw):
        sys.exit(1)
    detect_ipmi(hrdw)
    detect_infiniband(hrdw)
    detect_temperatures(hrdw)
    detect_utils.get_ddr_timing(hrdw)
    detect_utils.ipmi_sdr(hrdw)
    detect_rtc_clock(hrdw)
    _, output = cmd("dmesg")
    parse_dmesg(hrdw, output)
    bios_hp.dump_hp_bios(hrdw)

    if "benchmark_cpu" in options:
        bm_cpu.cpu_perf(hrdw)

    if "benchmark_mem" in options:
        bm_mem.mem_perf(hrdw)

    if "benchmark_disk" in options:
        bm_disk.disk_perf(hrdw,
                          destructive=options['benchmark_disk_destructive'])

    hrdw = clean_tuples(hrdw)

    if "human" in options.keys():
        pprint.pprint(hrdw)
    else:
        print(json.dumps(hrdw))


def main():
    os.environ["LANG"] = "en_US.UTF-8"
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--human',
                        help='Print output in human readable format',
                        action='store_true',
                        default=False)
    parser.add_argument('--benchmark', '-b',
                        help=('Run benchmark for specific components. '
                              'Valid components are: disk, cpu, mem'),
                        metavar='component',
                        nargs='+')
    parser.add_argument('--benchmark-disk-destructive',
                        help=('If specified make the disk component benchmark '
                              'to be destructive'),
                        action='store_true',
                        default=False)

    options = {}
    args = parser.parse_args()
    if args.human:
        options["human"] = True
    if args.benchmark:
        invalid_opts = []
        for opt in args.benchmark:
            opt_ = opt.lower()
            if opt_ == 'cpu':
                options['benchmark_cpu'] = True
            elif opt_ == 'mem':
                options['benchmark_mem'] = True
            elif opt_ == 'disk':
                options['benchmark_disk'] = True
                options['benchmark_disk_destructive'] = (
                    args.benchmark_disk_destructive)
            else:
                invalid_opts.append(opt)

        if invalid_opts:
            print('"%s" is/are not valid benchmark component(s). Check '
                  '--help to see the list of acceptable values' %
                  ', '.join(invalid_opts))
            sys.exit(1)

    _main(options)
