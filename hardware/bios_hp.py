# Copyright (C) 2019 Criteo
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

"""API to the hp-conrep utility to list the bios settings"""

import os
import pprint
import sys
import tempfile
import xml.etree.ElementTree as ET

from hardware.detect_utils import cmd


def get_hp_conrep(hwlst):
    for i in hwlst:
        if i[0:3] == ('system', 'product', 'vendor'):
            if i[3] not in ['HPE', 'HP']:
                return True, ""
    output_file = next(tempfile._get_candidate_names())
    status, output = cmd("hp-conrep --save -f {}".format(output_file))
    if status != 0:
        sys.stderr.write("Unable to run hp-conrep: %s\n" % output)
        return False, ""
    return_value = open(output_file).read()
    os.remove(output_file)
    return True, return_value


def dump_hp_bios(hwlst):
    # handle output injection for testing purpose
    valid, hpconfig = get_hp_conrep(hwlst)
    if not valid:
        return False

    if hpconfig:
        xml = ET.fromstring(hpconfig)
        root = xml.iter("Section")

        for child in root:
            hwlst.append(('hp', 'bios', child.attrib['name'], child.text))

    return True


if __name__ == "__main__":
    hwlst = []
    dump_hp_bios(hwlst)
    pprint.pprint(hwlst)
