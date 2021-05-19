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

import unittest

from hardware import ipmi
from hardware.tests.results import ipmi_results
from hardware.tests.utils import sample


class TestIpmi(unittest.TestCase):
    def test_parse_ipmi_sdr(self):
        hw = ipmi.parse_ipmi_sdr(sample('parse_ipmi_sdr').split('\n'))
        self.assertEqual(hw, ipmi_results.IPMI_SDR_RESULT)

    def test_parse_lan_info(self):
        res = []
        ipmi.parse_lan_info(sample('ipmi_lan_info'), res)
        self.assertEqual(len(res), 19)
