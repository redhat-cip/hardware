#
# Copyright (C) 2013-2014 eNovance SAS <licensing@enovance.com>
#
# Author: Frederic Lepied <frederic.lepied@enovance.com>
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

import mock

from hardware import detect
from hardware.tests.results import detect_results
from hardware.tests.utils import sample


@mock.patch('hardware.detect_utils.get_ethtool_status',
            lambda *args, **kwargs: [])
@mock.patch('socket.inet_ntoa', lambda *args, **kwargs: '255.255.255.0')
@mock.patch('fcntl.ioctl', lambda *args, **kwargs: [])
@mock.patch('hardware.detect_utils.get_lld_status',
            lambda *args, **kwargs: [])
class TestDetect(unittest.TestCase):

    def test_size_in_gb(self):
        self.assertEqual(detect.size_in_gb('100 GB'), '100')

    def test_size_in_tb(self):
        self.assertEqual(detect.size_in_gb('100TB'), '100000')

    def test_size_in_dottb(self):
        self.assertEqual(detect.size_in_gb('3.4601 TB'), '3460')

    def test_size_in_nothing(self):
        self.assertEqual(detect.size_in_gb('100'), '100')

    def test_get_cidr(self):
        self.assertEqual(detect.get_cidr('255.255.0.0'), '16')

    @mock.patch('os.path.exists', return_value=False)
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    sample('lscpu').split('\n'),
                    sample('lscpux').split('\n')])
    def test_get_cpus(self, mock_output_lines, mock_os_path_exists):
        hw = []
        detect.get_cpus(hw)
        self.assertEqual(hw, detect_results.GET_CPUS_RESULT)
        calls = []
        # Once per socket
        for i in range(2):
            calls.append(mock.call('/sys/devices/system/cpu/cpufreq/boost'))
        # Once per processor
        for i in range(1):
            f = ('/sys/devices/system/cpu/cpufreq/policy%d/scaling_governor' %
                 i)
            calls.append(mock.call(f))
        # NOTE(tonyb): We can't use assert_has_calls() because it's too
        # permissive.  We want an exact match
        self.assertEqual(calls, mock_os_path_exists.mock_calls)

    @mock.patch('os.path.exists', return_value=False)
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    sample('lscpu-vm').split('\n'),
                    sample('lscpu-vmx').split('\n'),
                    ('powersave',),
                    ('powersave',)])
    def test_get_cpus_vm(self, mock_output_lines, mock_os_path_exists):
        hw = []
        detect.get_cpus(hw)
        self.assertEqual(hw, detect_results.GET_CPUS_VM_RESULT)
        calls = []
        # Once per socket
        for i in range(1):
            calls.append(mock.call('/sys/devices/system/cpu/cpufreq/boost'))
        # Once per processor
        for i in range(2):
            f = ('/sys/devices/system/cpu/cpufreq/policy%d/scaling_governor' %
                 i)
            calls.append(mock.call(f))
        # NOTE(tonyb): We can't use assert_has_calls() because it's too
        # permissive.  We want an exact match
        self.assertEqual(calls, mock_os_path_exists.mock_calls)

    @mock.patch('os.path.exists', return_value=False)
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    sample('lscpu_aarch64').split('\n'),
                    sample('lscpux_aarch64').split('\n'),
                    ('powersave',),
                    ('powersave',)])
    def test_get_cpus_aarch64(self, mock_output_lines, mock_os_path_exists):
        self.maxDiff = None
        hw = []
        detect.get_cpus(hw)
        self.assertEqual(hw, detect_results.GET_CPUS_AARCH64_RESULT)
        calls = []
        # Once per socket
        for i in range(4):
            calls.append(mock.call('/sys/devices/system/cpu/cpufreq/boost'))
        # Once per processor
        for i in range(8):
            f = ('/sys/devices/system/cpu/cpufreq/policy%d/scaling_governor' %
                 i)
            calls.append(mock.call(f))
        # NOTE(tonyb): We can't use assert_has_calls() because it's too
        # permissive.  We want an exact match
        self.assertEqual(calls, mock_os_path_exists.mock_calls)

    @mock.patch('os.path.exists', return_value=False)
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    sample('lscpu_ppc64le').split('\n'),
                    sample('lscpux_ppc64le').split('\n')])
    def test_get_cpus_ppc64le(self, mock_output_lines, mock_os_path_exists):
        hw = []
        detect.get_cpus(hw)
        self.assertEqual(hw, detect_results.GET_CPUS_PPC64LE)
        calls = []
        # Once per socket
        for i in range(2):
            calls.append(mock.call('/sys/devices/system/cpu/cpufreq/boost'))
        # Once per processor
        for i in range(144):
            f = ('/sys/devices/system/cpu/cpufreq/policy%d/scaling_governor' %
                 i)
            calls.append(mock.call(f))
        # NOTE(tonyb): We can't use assert_has_calls() because it's too
        # permissive.  We want an exact match
        self.assertEqual(calls, mock_os_path_exists.mock_calls)

    @mock.patch('hardware.detect.cmd',
                return_value=(0, sample('dmesg')),
                autospec=True)
    def test_parse_dmesg(self, mock_cmd):
        hw = []
        detect.parse_dmesg(hw)
        self.assertEqual(hw, [('ahci', '0000:00:1f.2:', 'flags',
                               '64bit apst clo ems led '
                               'ncq part pio slum sntf')])

    @mock.patch('hardware.detect_utils.cmd', return_value=(0, 4))
    @mock.patch('hardware.detect.get_uuid',
                return_value='83462C81-52BA-11CB-870F')
    @mock.patch('hardware.detect.get_cpus', return_value='[]')
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    ('Ubuntu',),
                    ('Ubuntu 14.04 LTS',),
                    ('3.13.0-24-generic',),
                    ('x86_64',),
                    ('BOOT_IMAGE=/boot/vmlinuz',)])
    def test_detect_system_3(self, mock_cmd, mock_get_uuid, mock_get_cpus,
                             mock_output_lines):
        result = []
        detect.detect_system(result, sample('lshw3'))
        self.assertEqual(result, detect_results.DETECT_SYSTEM3_RESULT)

    @mock.patch('hardware.detect_utils.cmd', return_value=(0, 4))
    @mock.patch('hardware.detect.get_uuid',
                return_value='83462C81-52BA-11CB-870F')
    @mock.patch('hardware.detect.get_cpus', return_value='[]')
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    ('Ubuntu',),
                    ('Ubuntu 14.04 LTS',),
                    ('3.13.0-24-generic',),
                    ('x86_64',),
                    ('BOOT_IMAGE=/boot/vmlinuz',)])
    def test_detect_system_2(self, mock_cmd, mock_get_uuid, mock_get_cpus,
                             mock_output_lines):
        result = []
        detect.detect_system(result, sample('lshw2'))
        self.assertEqual(result, detect_results.DETECT_SYSTEM2_RESULT)

    @mock.patch('hardware.detect_utils.cmd', return_value=(0, 7))
    @mock.patch('hardware.detect.get_uuid',
                return_value='83462C81-52BA-11CB-870F')
    @mock.patch('hardware.detect.get_cpus', return_value='[]')
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    ('Ubuntu',),
                    ('Ubuntu 14.04 LTS',),
                    ('3.13.0-24-generic',),
                    ('x86_64',),
                    ('BOOT_IMAGE=/boot/vmlinuz',)
                ])
    def test_detect_system(self, mock_cmd, mock_get_uuid, mock_get_cpus,
                           mock_output_lines):
        result = []
        detect.detect_system(result, sample('lshw'))
        self.assertEqual(result, detect_results.DETECT_SYSTEM_RESULT)

    def test_get_value(self):
        self.assertEqual(detect._get_value([('a', 'b', 'c', 'd')],
                                           'a', 'b', 'c'), 'd')

    def test_fix_bad_serial_zero(self):
        hwl = [('system', 'product', 'serial', '0000000000')]
        detect.fix_bad_serial(hwl, 'uuid', '', '')
        self.assertEqual(detect._get_value(hwl, 'system', 'product', 'serial'),
                         'uuid')

    def test_fix_bad_serial_mobo(self):
        hwl = [('system', 'product', 'serial', '0123456789')]
        detect.fix_bad_serial(hwl, '', 'mobo', '')
        self.assertEqual(detect._get_value(hwl, 'system', 'product', 'serial'),
                         'mobo')

    def test_clean_str(self):
        self.assertEqual(detect.clean_str(b'\x8f' * 4), u'\ufffd' * 4)

    def test_clean_tuples(self):
        self.assertEqual(
            detect.clean_tuples([(b'\x8f' * 4, b'\x8f' * 4,
                                  b'h\xc3\xa9llo', 1)]),
            [(u'\ufffd' * 4, u'\ufffd' * 4, u'h\xe9llo', 1)])

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

    @mock.patch.object(detect, 'Popen')
    @mock.patch('os.uname', return_value=('', '', '', '', 'x86_64'))
    def test_get_uuid_x86_64(self, mock_uname, mock_popen):
        # This is more complex and 'magic' than I'd like :/
        process_mock = mock.Mock()
        attrs = {'communicate.return_value': ('83462C81-52BA-11CB-870F', '')}
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock

        hw_list = []
        system_uuid = detect.get_uuid(hw_list)
        mock_popen.assert_has_calls([
            mock.call("dmidecode -t 1 | grep UUID | " "awk '{print $2}'",
                      shell=True, stdout=detect.PIPE,
                      universal_newlines=True)])
        self.assertEqual('83462C81-52BA-11CB-870F', system_uuid)

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    @mock.patch('os.access', return_value=True)
    def test_get_uuid_ppc64le_ok_generate(self, mock_access, mock_uname):
        expected_uuid = 'a2724b67-c27e-5e5f-aa2b-3089a2bd8f41'
        fileobj = mock.mock_open(read_data=expected_uuid)
        with mock.patch('six.moves.builtins.open', fileobj, create=True):
            uuid = detect.get_uuid([])
        self.assertEqual(expected_uuid, uuid)

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    def test_get_uuid_ppc64le_ok_read(self, mock_uname):
        hw_list = [('sys_cls', 'sys_type', 'vendor', 'IBM'),
                   ('sys_cls', 'sys_type', 'serial', '1234567A')]
        self.assertEqual('a2724b67-c27e-5e5f-aa2b-3089a2bd8f41',
                         detect.get_uuid(hw_list))

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    def test_get_uuid_ppc64le_missing_serial(self, mock_uname):
        hw_list = [('sys_cls', 'sys_type', 'vendor', 'IBM')]
        self.assertIsNone(detect.get_uuid(hw_list))

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    def test_get_uuid_ppc64le_missing_vendor(self, mock_uname):
        hw_list = [('sys_cls', 'sys_type', 'serial', '1234567A')]
        self.assertIsNone(detect.get_uuid(hw_list))

    @mock.patch('os.uname', return_value=('', '', '', '', 'ppc64le'))
    def test_get_uuid_ppc64le_no_hw_list(self, mock_uname):
        hw_list = []
        self.assertIsNone(detect.get_uuid(hw_list))
