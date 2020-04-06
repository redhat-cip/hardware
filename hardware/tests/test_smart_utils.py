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

import subprocess
import unittest
from unittest import mock

from hardware import smart_utils
from hardware.tests.results import smart_utils_results
from hardware.tests.utils import sample


class TestSmartUtils(unittest.TestCase):

    def test_read_smart_field(self):
        hwlst = []
        line = 'This is a test line'
        device = 'fake'
        item = 'test'
        title = 'fake_title'
        item_not_in_line = 'not_in_line'
        smart_utils.read_smart_field(hwlst, line, device, item_not_in_line,
                                     title)
        self.assertEqual(hwlst, [])
        smart_utils.read_smart_field(hwlst, line, device, item, title)
        self.assertEqual(hwlst, [('disk', 'fake', 'SMART/fake_title', 'line')])

    def test_read_smart_field_temperature(self):
        hwlst = []
        line = 'Current Drive Temperature:     33 C'
        device = 'fake'
        item = 'Current Drive Temperature:'
        title = 'current_drive_temperature'
        smart_utils.read_smart_field(hwlst, line, device, item, title)
        self.assertEqual(hwlst,
                         [('disk', 'fake',
                           'SMART/current_drive_temperature', '33'),
                          ('disk', 'fake',
                           'SMART/current_drive_temperature_unit', 'C')])

    def test_read_smart_scsi_error_log(self):
        hwlst = []
        lines = [
            'read:   2403332209        0         0  2403332209          0       4059.788           0',  # noqa
            'write:         0        0         0         0          0       8372.602           0',  # noqa
            'verify: 442824963        0         0  442824963          0      51149.136           0'  # noqa
        ]
        for line in lines:
            smart_utils.read_smart_scsi_error_log(hwlst, line, 'fake',
                                                  line.split(':')[0])

        self.assertEqual(hwlst,
                         [('disk', 'fake', 'SMART/read_total_corrected_errors',
                           '2403332209'),
                          ('disk', 'fake', 'SMART/read_gigabytes_processed',
                           '4059.788'),
                          ('disk', 'fake',
                           'SMART/read_total_uncorrected_errors', '0'),
                          ('disk', 'fake',
                           'SMART/write_total_corrected_errors', '0'),
                          ('disk', 'fake', 'SMART/write_gigabytes_processed',
                           '8372.602'),
                          ('disk', 'fake',
                           'SMART/write_total_uncorrected_errors', '0'),
                          ('disk', 'fake',
                           'SMART/verify_total_corrected_errors', '442824963'),
                          ('disk', 'fake', 'SMART/verify_gigabytes_processed',
                           '51149.136'),
                          ('disk', 'fake',
                           'SMART/verify_total_uncorrected_errors', '0')])

    @mock.patch.object(subprocess, 'Popen')
    def test_read_smart_scsi(self, mock_popen):
        hwlst = []
        fake_output = sample('smartctl_scsi', mode='rb').splitlines()
        mock_popen.return_value = mock.Mock(stdout=fake_output)
        smart_utils.read_smart_scsi(hwlst, 'fake')

        self.assertEqual(hwlst, smart_utils_results.READ_SMART_SCSI_RESULT)

    @mock.patch.object(subprocess, 'Popen')
    def test_read_smart_ata(self, mock_popen):
        hwlst = []
        fake_output = sample('smartctl_ata', mode='rb').splitlines()
        mock_popen.return_value = mock.Mock(stdout=fake_output)
        smart_utils.read_smart_ata(hwlst, 'fake')

        self.assertEqual(hwlst, smart_utils_results.READ_SMART_ATA_RESULT)

    @mock.patch.object(subprocess, 'Popen')
    def test_read_smart_ata_hdd(self, mock_popen):
        hwlst = []
        fake_output = sample('smartctl_ata_hdd', mode='rb').splitlines()
        mock_popen.return_value = mock.Mock(stdout=fake_output)
        smart_utils.read_smart_ata(hwlst, 'fake')

        self.assertEqual(hwlst, smart_utils_results.READ_SMART_ATA_HDD_RESULT)

    @mock.patch.object(subprocess, 'Popen')
    def test_read_smart_ata_decode_ignore(self, mock_popen):
        hwlst = []
        fake_output = sample('smartctl_ata_decode_ignore',
                             mode='rb').splitlines()
        mock_popen.return_value = mock.Mock(stdout=fake_output)
        smart_utils.read_smart_ata(hwlst, 'fake')
        self.assertEqual(
            hwlst, smart_utils_results.READ_SMART__ATA_DECODE_IGNORE_RESULT)

    @mock.patch('hardware.smart_utils.read_smart_ata')
    @mock.patch('os.path.exists', return_value=True)
    @mock.patch.object(subprocess, 'Popen')
    def test_read_smart_call_smart_ata(self, mock_popen, mock_os_path_exists,
                                       mock_ata):
        hwlst = []
        fake_output = sample('smartctl_ata', mode='rb').splitlines()
        mock_popen.return_value = mock.Mock(stdout=fake_output)
        smart_utils.read_smart(hwlst, 'fake')

        mock_ata.assert_called()

    @mock.patch('hardware.smart_utils.read_smart_scsi')
    @mock.patch('os.path.exists', return_value=True)
    @mock.patch.object(subprocess, 'Popen')
    def test_read_smart_call_smart_scsi(self, mock_popen, mock_os_path_exists,
                                        mock_scsi):
        hwlst = []
        fake_output = sample('smartctl_scsi', mode='rb').splitlines()
        mock_popen.return_value = mock.Mock(stdout=fake_output)
        smart_utils.read_smart(hwlst, 'fake')

        mock_scsi.assert_called()

    @mock.patch('os.path.exists', return_value=True)
    @mock.patch.object(subprocess, 'Popen')
    def test_read_smart_nvme(self, mock_popen, mock_os_path_exists):
        hwlst = []
        fake_output = sample('smartctl_nvme', mode='rb').splitlines()
        mock_popen.return_value = mock.Mock(stdout=fake_output)
        smart_utils.read_smart_nvme(hwlst, 'fake_nvme')

        self.assertEqual(hwlst, smart_utils_results.READ_SMART_NVME_RESULT)
