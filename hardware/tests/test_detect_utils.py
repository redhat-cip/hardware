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
from hardware.tests.results import detect_utils_results
from hardware.tests.utils import sample


class TestDetectUtils(unittest.TestCase):

    def test_parse_ipmi_sdr(self):
        hw = []
        detect_utils.parse_ipmi_sdr(hw, sample('parse_ipmi_sdr').split('\n'))
        self.assertEqual(hw, detect_utils_results.IPMI_SDR_RESULT)

    def test_size_in_gb(self):
        self.assertEqual(detect_utils.size_in_gb('100 GB'), '100')

    def test_size_in_tb(self):
        self.assertEqual(detect_utils.size_in_gb('100TB'), '100000')

    def test_size_in_dottb(self):
        self.assertEqual(detect_utils.size_in_gb('3.4601 TB'), '3460')

    def test_size_in_nothing(self):
        self.assertEqual(detect_utils.size_in_gb('100'), '100')
