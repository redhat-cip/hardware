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

from hardware import detect_utils
from hardware.tests.results import parse_ipmi_sdr
from hardware.tests.utils import sample


class TestDetectUtils(unittest.TestCase):

    def test_parse_ipmi_sdr(self):
        hw = []
        detect_utils.parse_ipmi_sdr(hw, sample('parse_ipmi_sdr').split('\n'))
        self.assertEqual(hw, parse_ipmi_sdr.get_ipmi_sdr_result())
