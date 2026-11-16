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
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def get_hp_conrep(hrdw):
    for i in hrdw:
        if i[0:3] == ('system', 'product', 'vendor'):
            if i[3] not in ['HPE', 'HP']:
                return True, ""

    with tempfile.TemporaryDirectory(prefix='hardware-hp-conrep-') as tmpdir:
        output_file = os.path.join(tmpdir, 'conrep.xml')
        try:
            result = subprocess.run(
                ['hp-conrep', '--save', '-f', output_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except OSError as exc:
            sys.stderr.write('Unable to run hp-conrep: %s\n' % exc)
            return False, ""

        if result.returncode != 0:
            error = result.stderr or result.stdout or (
                'exit status %d' % result.returncode)
            sys.stderr.write('Unable to run hp-conrep: %s\n' % error)
            return False, ""

        try:
            with open(output_file, 'r', encoding='utf-8') as conrep_file:
                return True, conrep_file.read()
        except OSError as exc:
            sys.stderr.write('Unable to read hp-conrep output: %s\n' % exc)
            return False, ""


def dump_hp_bios(hrdw):
    hwlst = []

    # handle output injection for testing purpose
    valid, hpconfig = get_hp_conrep(hrdw)
    if not valid:
        return hwlst

    if hpconfig:
        try:
            xml = ET.fromstring(hpconfig)
        except ET.ParseError as exc:
            sys.stderr.write('Unable to parse hp-conrep output: %s\n' % exc)
            return hwlst
        root = xml.iter("Section")

        for child in root:
            hwlst.append(('hp', 'bios', child.attrib['name'], child.text))

    return hwlst
