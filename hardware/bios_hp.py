#
# Copyright (C) 2019 Criteo
#
# Author: Erwan Velu <e.velu@criteo.com>
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

'''API to the hp-conrep utility to list the bios settings
'''

from __future__ import print_function
import tempfile
import os
import xml.etree.ElementTree as ET
from hardware.detect_utils import cmd
import pprint
import sys


def dump_hp_bios(hw_lst, output=None):
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
        root = ET.fromstring(output)
    else:
        output_file = next(tempfile._get_candidate_names())
        status, output = cmd("hp-conrep --save -f {}".format(output_file))
        if status != 0:
            sys.stderr.write("Unable to run hp-conrep: %s\n" % output)
            return False
        xml = ET.parse(output_file)
        os.remove(output_file)
        root = xml.getroot().iter("Section")

    for child in root:
        hw_lst.append(('hp', 'bios', child.attrib['name'], child.text))

    return True


if __name__ == "__main__":
    hw_lst = []
    dump_hp_bios(hw_lst)
    pprint.pprint(hw_lst)
