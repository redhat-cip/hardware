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
from unittest import mock

from hardware import system
from hardware.tests.results import system_results
from hardware.tests.utils import sample


@mock.patch('hardware.detect_utils.get_ethtool_status',
            lambda *args, **kwargs: [])
@mock.patch('socket.inet_ntoa', lambda *args, **kwargs: '255.255.255.0')
@mock.patch('fcntl.ioctl', lambda *args, **kwargs: [])
@mock.patch('hardware.detect_utils.get_lld_status',
            lambda *args, **kwargs: [])
class TestSystem(unittest.TestCase):

    @mock.patch('hardware.detect_utils.cmd', return_value=(0, 4))
    @mock.patch('hardware.detect_utils.get_uuid',
                return_value='83462C81-52BA-11CB-870F')
    @mock.patch('hardware.detect_utils.get_cpus', return_value='[]')
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    ('Ubuntu',),
                    ('Ubuntu 14.04 LTS',),
                    ('3.13.0-24-generic',),
                    ('x86_64',),
                    ('BOOT_IMAGE=/boot/vmlinuz',)])
    def test_detect_system_3(self, mock_cmd, mock_get_uuid, mock_get_cpus,
                             mock_output_lines):
        result = system.detect(sample('lshw3'))
        self.assertEqual(result, system_results.DETECT_SYSTEM3_RESULT)

    @mock.patch('hardware.detect_utils.cmd', return_value=(0, 4))
    @mock.patch('hardware.detect_utils.get_uuid',
                return_value='83462C81-52BA-11CB-870F')
    @mock.patch('hardware.detect_utils.get_cpus', return_value='[]')
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    ('Ubuntu',),
                    ('Ubuntu 14.04 LTS',),
                    ('3.13.0-24-generic',),
                    ('x86_64',),
                    ('BOOT_IMAGE=/boot/vmlinuz',)])
    def test_detect_system_2(self, mock_cmd, mock_get_uuid, mock_get_cpus,
                             mock_output_lines):
        result = system.detect(sample('lshw2'))
        self.assertEqual(result, system_results.DETECT_SYSTEM2_RESULT)

    @mock.patch('hardware.detect_utils.cmd', return_value=(0, 7))
    @mock.patch('hardware.detect_utils.get_uuid',
                return_value='83462C81-52BA-11CB-870F')
    @mock.patch('hardware.detect_utils.get_cpus', return_value='[]')
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    ('Ubuntu',),
                    ('Ubuntu 14.04 LTS',),
                    ('3.13.0-24-generic',),
                    ('x86_64',),
                    ('BOOT_IMAGE=/boot/vmlinuz',)])
    def test_detect_system(self, mock_cmd, mock_get_uuid, mock_get_cpus,
                           mock_output_lines):
        result = system.detect(sample('lshw'))
        self.assertEqual(result, system_results.DETECT_SYSTEM_RESULT)
