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

    def test_clean_str(self):
        self.assertEqual(detect_utils.clean_str(b'\x8f' * 4), u'\ufffd' * 4)

    def test_clean_tuples(self):
        self.assertEqual(
            detect_utils.clean_tuples([(b'\x8f' * 4, b'\x8f' * 4,
                                        b'h\xc3\xa9llo', 1)]),
            [(u'\ufffd' * 4, u'\ufffd' * 4, u'h\xe9llo', 1)])

    @mock.patch.object(subprocess, 'Popen')
    @mock.patch('os.uname', return_value=('', '', '', '', 'x86_64'))
    def test_get_uuid_x86_64(self, mock_uname, mock_popen):
        # This is more complex and 'magic' than I'd like :/
        process_mock = mock.Mock()
        attrs = {'communicate.return_value': ('83462C81-52BA-11CB-870F', '')}
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        hw_list = []
        system_uuid = detect_utils.get_uuid(hw_list)
        mock_popen.assert_has_calls([
            mock.call("dmidecode -t 1 | grep UUID | " "awk '{print $2}'",
                      shell=True, stdout=subprocess.PIPE,
                      universal_newlines=True)])
        self.assertEqual('83462C81-52BA-11CB-870F', system_uuid)

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    @mock.patch('os.access', return_value=True)
    def test_get_uuid_ppc64le_ok_generate(self, mock_access, mock_uname):
        expected_uuid = 'a2724b67-c27e-5e5f-aa2b-3089a2bd8f41'
        fileobj = mock.mock_open(read_data=expected_uuid)
        with mock.patch('builtins.open', fileobj, create=True):
            uuid = detect_utils.get_uuid([])
        self.assertEqual(expected_uuid, uuid)

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    def test_get_uuid_ppc64le_ok_read(self, mock_uname):
        hw_list = [('sys_cls', 'sys_type', 'vendor', 'IBM'),
                   ('sys_cls', 'sys_type', 'serial', '1234567A')]
        self.assertEqual('a2724b67-c27e-5e5f-aa2b-3089a2bd8f41',
                         detect_utils.get_uuid(hw_list))

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    def test_get_uuid_ppc64le_missing_serial(self, mock_uname):
        hw_list = [('sys_cls', 'sys_type', 'vendor', 'IBM')]
        self.assertIsNone(detect_utils.get_uuid(hw_list))

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    def test_get_uuid_ppc64le_missing_vendor(self, mock_uname):
        hw_list = [('sys_cls', 'sys_type', 'serial', '1234567A')]
        self.assertIsNone(detect_utils.get_uuid(hw_list))

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    def test_get_uuid_ppc64le_no_hw_list(self, mock_uname):
        hw_list = []
        self.assertIsNone(detect_utils.get_uuid(hw_list))
