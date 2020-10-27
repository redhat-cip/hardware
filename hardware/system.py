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

import fcntl
import ipaddress
import re
import socket
import struct
import sys
import xml.etree.ElementTree as ET

from hardware import detect_utils


SIOCGIFNETMASK = 0x891b


def detect(output=None):
    """Detect system characteristics from the output of lshw."""

    hw_lst = []

    def _find_element(xml, xml_spec, sys_subtype,
                      sys_type='product', sys_cls='system',
                      attrib=None, transform=None):
        """Lookup an xml element and populate hw_lst when found."""
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
        status, output = detect_utils.cmd('lshw -xml')
    if status == 0:
        mobo_id = ''
        nic_id = ''
        xml = ET.fromstring(output)
        _find_element(xml, "./node/serial", 'serial')
        _find_element(xml, "./node/product", 'name')
        _find_element(xml, "./node/vendor", 'vendor')
        _find_element(xml, "./node/version", 'version')
        uuid = detect_utils.get_uuid(hw_lst)

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
                _find_element(elt, 'product', 'name', 'motherboard', 'system')
                _find_element(elt, 'vendor', 'vendor', 'motherboard', 'system')
                _find_element(elt, 'version', 'version', 'motherboard',
                              'system')
                _find_element(elt, 'serial', 'serial', 'motherboard', 'system')
                mobo_id = detect_utils.get_value(hw_lst, 'system',
                                                 'motherboard', 'serial')

        for elt in xml.findall(".//node[@id='firmware']"):
            name = elt.find('physid')
            if name is not None:
                _find_element(elt, 'version', 'version', 'bios', 'firmware')
                _find_element(elt, 'date', 'date', 'bios', 'firmware')
                _find_element(elt, 'vendor', 'vendor', 'bios', 'firmware')

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
                _find_element(elt, 'size', 'size', 'total', 'memory')
                for bank_list in elt.findall(".//node[@id]"):
                    if 'bank:' in bank_list.get('id'):
                        bank_count = bank_count + 1
                        for bank in elt.findall(".//node[@id='%s']" %
                                                (bank_list.get('id'))):
                            bank_id = bank_list.get('id').replace(
                                "bank:", "bank" + location + ":")
                            _find_element(bank, 'size', 'size',
                                          bank_id, 'memory')
                            _find_element(bank, 'clock', 'clock',
                                          bank_id, 'memory')
                            _find_element(bank, 'description', 'description',
                                          bank_id, 'memory')
                            _find_element(bank, 'vendor', 'vendor',
                                          bank_id, 'memory')
                            _find_element(bank, 'product', 'product',
                                          bank_id, 'memory')
                            _find_element(bank, 'serial', 'serial',
                                          bank_id, 'memory')
                            _find_element(bank, 'slot', 'slot',
                                          bank_id, 'memory')
        if bank_count > 0:
            hw_lst.append(('memory', 'banks', 'count', str(bank_count)))

        for elt in xml.findall(".//node[@class='network']"):
            name = elt.find('logicalname')
            if name is not None:
                _find_element(elt, 'businfo', 'businfo', name.text, 'network')
                _find_element(elt, 'vendor', 'vendor', name.text, 'network')
                _find_element(elt, 'product', 'product', name.text, 'network')
                _find_element(elt, "configuration/setting[@id='firmware']",
                              'firmware', name.text, 'network', 'value')
                _find_element(elt, 'size', 'size', name.text, 'network')
                ipv4 = _find_element(elt, "configuration/setting[@id='ip']",
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
                        cidr = detect_utils.get_cidr(netmask)
                        hw_lst.append(
                            ('network', name.text, 'ipv4-cidr', cidr))
                        net = (ipaddress.IPv4Interface('%s/%s' % (ipv4, cidr))
                               .network.network_address)
                        hw_lst.append(
                            ('network', name.text, 'ipv4-network', str(net)))
                    except Exception as excpt:
                        sys.stderr.write('unable to get info for %s: %s\n'
                                         % (name.text, str(excpt)))

                _find_element(elt, "configuration/setting[@id='link']", 'link',
                              name.text, 'network', 'value')
                _find_element(elt, "configuration/setting[@id='driver']",
                              'driver', name.text, 'network', 'value')
                _find_element(elt, "configuration/setting[@id='duplex']",
                              'duplex', name.text, 'network', 'value')
                _find_element(elt, "configuration/setting[@id='speed']",
                              'speed', name.text, 'network', 'value')
                _find_element(elt, "configuration/setting[@id='latency']",
                              'latency', name.text, 'network', 'value')
                _find_element(elt,
                              "configuration/setting[@id='autonegotiation']",
                              'autonegotiation', name.text, 'network', 'value')

                # lshw is not able to get the complete mac addr for ib
                # devices Let's workaround it with an ip command.
                if name.text.startswith('ib'):
                    cmds = "ip addr show %s | grep link | awk '{print $2}'"
                    status_ip, output_ip = detect_utils.cmd(cmds % name.text)
                    if status_ip == 0:
                        hw_lst.append(('network',
                                       name.text,
                                       'serial',
                                       output_ip.split('\n')[0].lower()))
                else:
                    _find_element(elt, 'serial', 'serial', name.text,
                                  'network', transform=lambda x: x.lower())

                if not nic_id:
                    nic_id = detect_utils.get_value(
                        hw_lst, 'network', name.text, 'serial')
                    nic_id = nic_id.replace(':', '')

                detect_utils.get_ethtool_status(hw_lst, name.text)
                detect_utils.get_lld_status(hw_lst, name.text)

        detect_utils.fix_bad_serial(hw_lst, uuid, mobo_id, nic_id)

    else:
        sys.stderr.write("Unable to run lshw: %s\n" % output)
        return []

    detect_utils.get_cpus(hw_lst)

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
    return hw_lst
