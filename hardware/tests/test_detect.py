# Copyright (C) 2013-2014 eNovance SAS <licensing@enovance.com>
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
from unittest import mock

from hardware import detect
from hardware.tests.utils import sample


@mock.patch('hardware.detect_utils.get_ethtool_status',
            lambda *args, **kwargs: [])
@mock.patch('socket.inet_ntoa', lambda *args, **kwargs: '255.255.255.0')
@mock.patch('fcntl.ioctl', lambda *args, **kwargs: [])
@mock.patch('hardware.detect_utils.get_lld_status',
            lambda *args, **kwargs: [])
class TestDetect(unittest.TestCase):

    @mock.patch('hardware.detect_utils.cmd',
                return_value=(0, sample('dmesg')),
                autospec=True)
    def test_parse_dmesg(self, mock_cmd):
        hw = []
        detect.parse_dmesg(hw)
        self.assertEqual(hw, [('ahci', '0000:00:1f.2:', 'flags',
                               '64bit apst clo ems led '
                               'ncq part pio slum sntf')])

    @mock.patch.object(detect, 'Popen')
    @mock.patch('os.environ.copy')
    def test_detect_auxv_x86_succeed(self, mock_environ_copy, mock_popen):
        test_data = {
            'AT_HWCAP': ('hwcap', 'bfebfbff'),
            'AT_HWCAP2': ('hwcap2', '0x0'),
            'AT_PAGESZ': ('pagesz', '4096'),
            'AT_FLAGS': ('flags', '0x0'),
            'AT_PLATFORM': ('platform', 'x86_64'),
        }

        process_mock = mock.Mock()
        attrs = {'communicate.return_value': (
            sample('auxv_x86').encode('utf-8'), None)}
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        hw = []
        detect.detect_auxv(hw)

        # NOTE(mrda): x86 doesn't have AUXV_OPT_FLAGS
        for k in detect.AUXV_FLAGS:
            t = ('hw', 'auxv', test_data[k][0], test_data[k][1])
            self.assertTrue(t in hw)

    @mock.patch.object(detect, 'Popen')
    @mock.patch('os.environ.copy')
    def test_detect_auxv_ppc8_succeed(self, mock_environ_copy, mock_popen):
        test_data = {
            'AT_HWCAP': ('hwcap',
                         'true_le archpmu vsx arch_2_06 dfp ic_snoop smt '
                         'mmu fpu altivec ppc64 ppc32'),
            'AT_HWCAP2': ('hwcap2', 'htm-nosc vcrypto tar isel ebb dscr '
                          'htm arch_2_07'),
            'AT_PAGESZ': ('pagesz', '65536'),
            'AT_FLAGS': ('flags', '0x0'),
            'AT_PLATFORM': ('platform', 'power8'),
            'AT_BASE_PLATFORM': ('base_platform', 'power8'),
        }

        process_mock = mock.Mock()
        attrs = {'communicate.return_value': (
            sample('auxv_ppc8').encode('utf-8'), None)}
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        hw = []
        detect.detect_auxv(hw)

        ppc_flags = detect.AUXV_FLAGS + detect.AUXV_OPT_FLAGS
        for k in ppc_flags:
            t = ('hw', 'auxv', test_data[k][0], test_data[k][1])
            self.assertTrue(t in hw)
