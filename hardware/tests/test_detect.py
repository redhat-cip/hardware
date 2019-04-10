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
                    sample('lscpux').split('\n'),
                ]
                )
    def test_get_cpus(self, mock_output_lines, mock_os_path_exists):
        hw = []

        detect.get_cpus(hw)

        self.assertEqual(hw, [('cpu', 'physical', 'number', 2),
                              ('cpu', 'physical_0', 'vendor', 'AuthenticAMD'),
                              ('cpu', 'physical_0', 'product',
                               'AMD EPYC 7451 24-Core Processor'),
                              ('cpu', 'physical_0', 'cores', 24),
                              ('cpu', 'physical_0', 'threads', 48),
                              ('cpu', 'physical_0', 'family', 23),
                              ('cpu', 'physical_0', 'model', 1),
                              ('cpu', 'physical_0', 'stepping', 2),
                              ('cpu', 'physical_0', 'l1d cache', '32K'),
                              ('cpu', 'physical_0', 'l1i cache', '64K'),
                              ('cpu', 'physical_0', 'l2 cache', '512K'),
                              ('cpu', 'physical_0', 'l3 cache', '8192K'),
                              ('cpu', 'physical_0', 'min_Mhz', 1200.0),
                              ('cpu', 'physical_0', 'max_Mhz', 2300.0),
                              ('cpu', 'physical_0', 'current_Mhz', 1197.549),
                              ('cpu', 'physical_0', 'flags',
                               'fpu vme de pse tsc msr pae mce cx8 apic sep mtrr '
                               'pge mca cmov pat pse36 clflush mmx fxsr sse sse2 '
                               'ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp '
                               'lm constant_tsc rep_good nopl nonstop_tsc '
                               'cpuid extd_apicid amd_dcm aperfmperf pni pclmulqdq monitor '
                               'ssse3 fma cx16 sse4_1 sse4_2 movbe popcnt aes '
                               'xsave avx f16c rdrand lahf_lm cmp_legacy svm '
                               'extapic cr8_legacy abm sse4a misalignsse '
                               '3dnowprefetch osvw skinit wdt tce topoext '
                               'perfctr_core perfctr_nb bpext perfctr_llc '
                               'mwaitx cpb hw_pstate ssbd ibpb vmmcall '
                               'fsgsbase bmi1 avx2 smep bmi2 rdseed adx smap '
                               'clflushopt sha_ni xsaveopt xsavec xgetbv1 '
                               'xsaves clzero irperf xsaveerptr arat npt lbrv '
                               'svm_lock nrip_save tsc_scale vmcb_clean '
                               'flushbyasid decodeassists pausefilter '
                               'pfthreshold avic v_vmsave_vmload vgif '
                               'overflow_recov succor smca'),
                              ('cpu', 'physical_1', 'vendor', 'AuthenticAMD'),
                              ('cpu', 'physical_1', 'product',
                               'AMD EPYC 7451 24-Core Processor'),
                              ('cpu', 'physical_1', 'cores', 24),
                              ('cpu', 'physical_1', 'threads', 48),
                              ('cpu', 'physical_1', 'family', 23),
                              ('cpu', 'physical_1', 'model', 1),
                              ('cpu', 'physical_1', 'stepping', 2),
                              ('cpu', 'physical_1', 'l1d cache', '32K'),
                              ('cpu', 'physical_1', 'l1i cache', '64K'),
                              ('cpu', 'physical_1', 'l2 cache', '512K'),
                              ('cpu', 'physical_1', 'l3 cache', '8192K'),
                              ('cpu', 'physical_1', 'min_Mhz', 1200.0),
                              ('cpu', 'physical_1', 'max_Mhz', 2300.0),
                              ('cpu', 'physical_1', 'current_Mhz', 1197.549),
                              ('cpu', 'physical_1', 'flags',
                               'fpu vme de pse tsc msr pae mce cx8 apic sep mtrr '
                               'pge mca cmov pat pse36 clflush mmx fxsr sse sse2 '
                               'ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp '
                               'lm constant_tsc rep_good nopl nonstop_tsc '
                               'cpuid extd_apicid amd_dcm aperfmperf pni pclmulqdq monitor '
                               'ssse3 fma cx16 sse4_1 sse4_2 movbe popcnt aes '
                               'xsave avx f16c rdrand lahf_lm cmp_legacy svm '
                               'extapic cr8_legacy abm sse4a misalignsse '
                               '3dnowprefetch osvw skinit wdt tce topoext '
                               'perfctr_core perfctr_nb bpext perfctr_llc '
                               'mwaitx cpb hw_pstate ssbd ibpb vmmcall '
                               'fsgsbase bmi1 avx2 smep bmi2 rdseed adx smap '
                               'clflushopt sha_ni xsaveopt xsavec xgetbv1 '
                               'xsaves clzero irperf xsaveerptr arat npt lbrv '
                               'svm_lock nrip_save tsc_scale vmcb_clean '
                               'flushbyasid decodeassists pausefilter '
                               'pfthreshold avic v_vmsave_vmload vgif '
                               'overflow_recov succor smca'),
                              ('cpu', 'logical', 'number', 1),
                              ('numa', 'nodes', 'count', 8),
                              ('numa', 'node_0', 'cpu_count', 12),
                              ('numa', 'node_0', 'cpu_mask', '0x3f00000000003f'),
                              ('numa', 'node_1', 'cpu_count', 12),
                              ('numa', 'node_1', 'cpu_mask', '0xfc0000000000fc0'),
                              ('numa', 'node_2', 'cpu_count', 12),
                              ('numa', 'node_2', 'cpu_mask', '0x3f00000000003f000'),
                              ('numa', 'node_3', 'cpu_count', 12),
                              ('numa', 'node_3', 'cpu_mask',
                               '0xfc0000000000fc0000'),
                              ('numa', 'node_4', 'cpu_count', 12),
                              ('numa', 'node_4', 'cpu_mask',
                               '0x3f00000000003f000000'),
                              ('numa', 'node_5', 'cpu_count', 12),
                              ('numa', 'node_5', 'cpu_mask',
                               '0xfc0000000000fc0000000'),
                              ('numa', 'node_6', 'cpu_count', 12),
                              ('numa', 'node_6', 'cpu_mask',
                               '0x3f00000000003f000000000'),
                              ('numa', 'node_7', 'cpu_count', 12),
                              ('numa', 'node_7', 'cpu_mask',
                               '0xfc0000000000fc0000000000'),
                              ])
        calls = []
        # Once per socket
        for i in range(2):
            calls.append(mock.call('/sys/devices/system/cpu/cpufreq/boost'))
        # Once per processor
        for i in range(1):
            f = ('/sys/devices/system/cpu/cpufreq/policy%d/scaling_governor' %
                 (i))
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
                    ('powersave',),
                ]
                )
    def test_get_cpus_vm(self, mock_output_lines, mock_os_path_exists):
        hw = []
        detect.get_cpus(hw)
        self.assertEqual(hw, [('cpu', 'physical', 'number', 1),
                              ('cpu', 'physical_0', 'vendor', 'GenuineIntel'),
                              ('cpu', 'physical_0', 'product',
                               'Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz'),
                              ('cpu', 'physical_0', 'cores', 2),
                              ('cpu', 'physical_0', 'threads', 2),
                              ('cpu', 'physical_0', 'family', 6),
                              ('cpu', 'physical_0', 'model', 142),
                              ('cpu', 'physical_0', 'stepping', 10),
                              ('cpu', 'physical_0', 'l1d cache', '32K'),
                              ('cpu', 'physical_0', 'l1i cache', '32K'),
                              ('cpu', 'physical_0', 'l2 cache', '256K'),
                              ('cpu', 'physical_0', 'l3 cache', '8192K'),
                              ('cpu', 'physical_0', 'current_Mhz', 2112.002),
                              ('cpu', 'physical_0', 'flags',
                               'fpu vme de pse tsc msr pae mce cx8 apic sep '
                               'mtrr pge mca cmov pat pse36 clflush mmx fxsr '
                               'sse sse2 ht syscall nx rdtscp lm constant_tsc '
                               'rep_good nopl xtopology nonstop_tsc pni '
                               'pclmulqdq ssse3 cx16 pcid sse4_1 sse4_2 x2apic '
                               'movbe popcnt aes xsave avx rdrand hypervisor '
                               'lahf_lm abm 3dnowprefetch fsgsbase avx2 '
                               'invpcid rdseed clflushopt'),
                              ('cpu', 'logical', 'number', 2),
                              ('numa', 'nodes', 'count', 1),
                              ('numa', 'node_0', 'cpu_count', 2),
                              ('numa', 'node_0', 'cpu_mask', '0x3')
                              ])
        calls = []
        # Once per socket
        for i in range(1):
            calls.append(mock.call('/sys/devices/system/cpu/cpufreq/boost'))
        # Once per processor
        for i in range(2):
            f = ('/sys/devices/system/cpu/cpufreq/policy%d/scaling_governor' %
                 (i))
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
                    ('powersave',),
                ]
                )
    def test_get_cpus_aarch64(self, mock_output_lines, mock_os_path_exists):
        self.maxDiff = None
        hw = []
        detect.get_cpus(hw)
        self.assertEqual(hw, [('cpu', 'physical', 'number', 4),
                              ('cpu', 'physical_0', 'vendor', 'APM'),
                              ('cpu', 'physical_0', 'product', 'X-Gene'),
                              ('cpu', 'physical_0', 'cores', 2),
                              ('cpu', 'physical_0', 'threads', 2),
                              ('cpu', 'physical_0', 'model', 0),
                              ('cpu', 'physical_0', 'stepping', 0),
                              ('cpu', 'physical_0', 'l1d cache', 'unknown size'),
                              ('cpu', 'physical_0', 'l1i cache', 'unknown size'),
                              ('cpu', 'physical_0', 'l2 cache', 'unknown size'),
                              ('cpu', 'physical_0', 'flags', 'fp asimd evtstrm cpuid'),
                              ('cpu', 'physical_1', 'vendor', 'APM'),
                              ('cpu', 'physical_1', 'product', 'X-Gene'),
                              ('cpu', 'physical_1', 'cores', 2),
                              ('cpu', 'physical_1', 'threads', 2),
                              ('cpu', 'physical_1', 'model', 0),
                              ('cpu', 'physical_1', 'stepping', 0),
                              ('cpu', 'physical_1', 'l1d cache', 'unknown size'),
                              ('cpu', 'physical_1', 'l1i cache', 'unknown size'),
                              ('cpu', 'physical_1', 'l2 cache', 'unknown size'),
                              ('cpu', 'physical_1', 'flags', 'fp asimd evtstrm cpuid'),
                              ('cpu', 'physical_2', 'vendor', 'APM'),
                              ('cpu', 'physical_2', 'product', 'X-Gene'),
                              ('cpu', 'physical_2', 'cores', 2),
                              ('cpu', 'physical_2', 'threads', 2),
                              ('cpu', 'physical_2', 'model', 0),
                              ('cpu', 'physical_2', 'stepping', 0),
                              ('cpu', 'physical_2', 'l1d cache', 'unknown size'),
                              ('cpu', 'physical_2', 'l1i cache', 'unknown size'),
                              ('cpu', 'physical_2', 'l2 cache', 'unknown size'),
                              ('cpu', 'physical_2', 'flags', 'fp asimd evtstrm cpuid'),
                              ('cpu', 'physical_3', 'vendor', 'APM'),
                              ('cpu', 'physical_3', 'product', 'X-Gene'),
                              ('cpu', 'physical_3', 'cores', 2),
                              ('cpu', 'physical_3', 'threads', 2),
                              ('cpu', 'physical_3', 'model', 0),
                              ('cpu', 'physical_3', 'stepping', 0),
                              ('cpu', 'physical_3', 'l1d cache', 'unknown size'),
                              ('cpu', 'physical_3', 'l1i cache', 'unknown size'),
                              ('cpu', 'physical_3', 'l2 cache', 'unknown size'),
                              ('cpu', 'physical_3', 'flags', 'fp asimd evtstrm cpuid'),
                              ('cpu', 'logical', 'number', 8),
                              ('numa', 'nodes', 'count', 1),
                              ('numa', 'node_0', 'cpu_count', 8),
                              ('numa', 'node_0', 'cpu_mask', 'ff')])
        calls = []
        # Once per socket
        for i in range(4):
            calls.append(mock.call('/sys/devices/system/cpu/cpufreq/boost'))
        # Once per processor
        for i in range(8):
            f = ('/sys/devices/system/cpu/cpufreq/policy%d/scaling_governor' %
                 (i))
            calls.append(mock.call(f))
        # NOTE(tonyb): We can't use assert_has_calls() because it's too
        # permissive.  We want an exact match
        self.assertEqual(calls, mock_os_path_exists.mock_calls)

    @mock.patch('os.path.exists', return_value=False)
    @mock.patch('hardware.detect_utils.output_lines',
                side_effect=[
                    sample('lscpu_ppc64le').split('\n'),
                    sample('lscpux_ppc64le').split('\n'),
                ]
                )
    def test_get_cpus_ppc64le(self, mock_output_lines, mock_os_path_exists):
        hw = []
        detect.get_cpus(hw)
        self.assertEqual(hw, [('cpu', 'physical', 'number', 2),
                              ('cpu', 'physical_0', 'product', 'POWER9, altivec supported'),
                              ('cpu', 'physical_0', 'cores', 18),
                              ('cpu', 'physical_0', 'threads', 72),
                              ('cpu', 'physical_0', 'model', '2.2 (pvr 004e 1202)'),
                              ('cpu', 'physical_0', 'l1d cache', '32K'),
                              ('cpu', 'physical_0', 'l1i cache', '32K'),
                              ('cpu', 'physical_0', 'l2 cache', '512K'),
                              ('cpu', 'physical_0', 'l3 cache', '10240K'),
                              ('cpu', 'physical_0', 'min_Mhz', 2300.0),
                              ('cpu', 'physical_0', 'max_Mhz', 3800.0),
                              ('cpu', 'physical_1', 'product', 'POWER9, altivec supported'),
                              ('cpu', 'physical_1', 'cores', 18),
                              ('cpu', 'physical_1', 'threads', 72),
                              ('cpu', 'physical_1', 'model', '2.2 (pvr 004e 1202)'),
                              ('cpu', 'physical_1', 'l1d cache', '32K'),
                              ('cpu', 'physical_1', 'l1i cache', '32K'),
                              ('cpu', 'physical_1', 'l2 cache', '512K'),
                              ('cpu', 'physical_1', 'l3 cache', '10240K'),
                              ('cpu', 'physical_1', 'min_Mhz', 2300.0),
                              ('cpu', 'physical_1', 'max_Mhz', 3800.0),
                              ('cpu', 'logical', 'number', 144),
                              ('numa', 'nodes', 'count', 6),
                              ('numa', 'node_0', 'cpu_count', 72),
                              ('numa', 'node_0', 'cpu_mask', 'ffffffffffffffffff'),
                              ('numa', 'node_8', 'cpu_count', 72),
                              ('numa', 'node_8', 'cpu_mask', 'ffffffffffffffffff000000000000000000'),
                              ('numa', 'node_252', 'cpu_count', 0),
                              ('numa', 'node_252', 'cpu_mask', '0'),
                              ('numa', 'node_253', 'cpu_count', 0),
                              ('numa', 'node_253', 'cpu_mask', '0'),
                              ('numa', 'node_254', 'cpu_count', 0),
                              ('numa', 'node_254', 'cpu_mask', '0'),
                              ('numa', 'node_255', 'cpu_count', 0),
                              ('numa', 'node_255', 'cpu_mask', '0')])
        calls = []
        # Once per socket
        for i in range(2):
            calls.append(mock.call('/sys/devices/system/cpu/cpufreq/boost'))
        # Once per processor
        for i in range(144):
            f = ('/sys/devices/system/cpu/cpufreq/policy%d/scaling_governor' %
                 (i))
            calls.append(mock.call(f))
        # NOTE(tonyb): We can't use assert_has_calls() because it's too
        # permissive.  We want an exact match
        self.assertEqual(calls, mock_os_path_exists.mock_calls)

    def test_parse_dmesg(self):
        hw = []
        detect.parse_dmesg(hw, sample('dmesg'))
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
                    ('BOOT_IMAGE=/boot/vmlinuz',)
                ])
    def test_detect_system_3(self, mock_cmd, mock_get_uuid, mock_get_cpus, mock_output_lines):
        result = []
        detect.detect_system(result, sample('lshw3'))
        self.assertEqual(
            result,
            [('system', 'product', 'serial', 'Empty'),
             ('system', 'product', 'name', 'S2915'),
             ('system', 'product', 'vendor', 'Tyan Computer Corporation'),
             ('system', 'product', 'version', 'REFERENCE'),
             ('system', 'product', 'uuid', '83462C81-52BA-11CB-870F'),
             ('system', 'motherboard', 'name', 'S2915'),
             ('system', 'motherboard', 'vendor', 'Tyan Computer Corporation'),
             ('system', 'motherboard', 'version', 'REFERENCE'),
             ('system', 'motherboard', 'serial', 'Empty'),
             ('firmware', 'bios', 'version', 'v3.00.2915 (10/10/2008)'),
             ('firmware', 'bios', 'vendor', 'Phoenix Technologies Ltd.'),
             ('memory', 'total', 'size', '4294967296'),
             ('memory', 'bank:0:0', 'description', 'DIMM Synchronous [empty]'),
             ('memory', 'bank:0:0', 'slot', 'C0_DIMM0'),
             ('memory', 'bank:0:1', 'description', 'DIMM Synchronous [empty]'),
             ('memory', 'bank:0:1', 'slot', 'C0_DIMM1'),
             ('memory', 'bank:0:2', 'size', '1073741824'),
             ('memory', 'bank:0:2', 'description', 'DIMM Synchronous'),
             ('memory', 'bank:0:2', 'slot', 'C0_DIMM2'),
             ('memory', 'bank:0:3', 'size', '1073741824'),
             ('memory', 'bank:0:3', 'description', 'DIMM Synchronous'),
             ('memory', 'bank:0:3', 'slot', 'C0_DIMM3'),
             ('memory', 'bank:0:4', 'description', 'DIMM Synchronous [empty]'),
             ('memory', 'bank:0:4', 'slot', 'C0_DIMM0'),
             ('memory', 'bank:0:5', 'description', 'DIMM Synchronous [empty]'),
             ('memory', 'bank:0:5', 'slot', 'C1_DIMM1'),
             ('memory', 'bank:0:6', 'size', '1073741824'),
             ('memory', 'bank:0:6', 'description', 'DIMM Synchronous'),
             ('memory', 'bank:0:6', 'slot', 'C1_DIMM2'),
             ('memory', 'bank:0:7', 'size', '1073741824'),
             ('memory', 'bank:0:7', 'description', 'DIMM Synchronous'),
             ('memory', 'bank:0:7', 'slot', 'C1_DIMM3'),
             ('memory', 'banks', 'count', '8'),
             ('system', 'os', 'vendor', 'Ubuntu'),
             ('system', 'os', 'version', 'Ubuntu 14.04 LTS'),
             ('system', 'kernel', 'version', '3.13.0-24-generic'),
             ('system', 'kernel', 'arch', 'x86_64'),
             ('system', 'kernel', 'cmdline', 'BOOT_IMAGE=/boot/vmlinuz'),
             ]
        )

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
                    ('BOOT_IMAGE=/boot/vmlinuz',)
                ])
    def test_detect_system_2(self, mock_cmd, mock_get_uuid, mock_get_cpus, mock_output_lines):
        result = []
        detect.detect_system(result, sample('lshw2'))
        self.assertEqual(
            result,
            [('system', 'product', 'serial', 'PB4F20N'),
             ('system', 'product', 'name', '2347GF8 (LENOVO_MT_2347)'),
             ('system', 'product', 'vendor', 'LENOVO'),
             ('system', 'product', 'version', 'ThinkPad T430'),
             ('system', 'product', 'uuid', '83462C81-52BA-11CB-870F'),
             ('system', 'motherboard', 'name', '2347GF8'),
             ('system', 'motherboard', 'vendor', 'LENOVO'),
             ('system', 'motherboard', 'version', 'Not Defined'),
             ('system', 'motherboard', 'serial', '1ZLMB31B1G6'),
             ('firmware', 'bios', 'version', 'G1ET73WW (2.09 )'),
             ('firmware', 'bios', 'date', '10/19/2012'),
             ('firmware', 'bios', 'vendor', 'LENOVO'),
             ('memory', 'total', 'size', '8589934592'),
             ('memory', 'bank:0', 'size', '4294967296'),
             ('memory', 'bank:0', 'clock', '1600000000'),
             ('memory', 'bank:0', 'description',
              'SODIMM DDR3 Synchrone 1600 MHz (0,6 ns)'),
             ('memory', 'bank:0', 'vendor', 'Samsung'),
             ('memory', 'bank:0', 'product', 'M471B5273CH0-CK0'),
             ('memory', 'bank:0', 'serial', '1222BCCE'),
             ('memory', 'bank:0', 'slot', 'ChannelA-DIMM0'),
             ('memory', 'bank:1', 'size', '4294967296'),
             ('memory', 'bank:1', 'clock', '1600000000'),
             ('memory', 'bank:1', 'description',
              'SODIMM DDR3 Synchrone 1600 MHz (0,6 ns)'),
             ('memory', 'bank:1', 'vendor', 'Samsung'),
             ('memory', 'bank:1', 'product', 'M471B5273CH0-CK0'),
             ('memory', 'bank:1', 'serial', '1222BCA2'),
             ('memory', 'bank:1', 'slot', 'ChannelB-DIMM0'),
             ('memory', 'banks', 'count', '2'),
             ('network', 'eth0', 'businfo', 'pci@0000:00:19.0'),
             ('network', 'eth0', 'vendor', 'Intel Corporation'),
             ('network', 'eth0', 'product',
              '82579LM Gigabit Network Connection'),
             ('network', 'eth0', 'firmware', '0.13-3'),
             ('network', 'eth0', 'link', 'no'),
             ('network', 'eth0', 'driver', 'e1000e'),
             ('network', 'eth0', 'latency', '0'),
             ('network', 'eth0', 'autonegotiation', 'on'),
             ('network', 'eth0', 'serial', '00:21:cc:d9:bf:26'),
             ('network', 'wlan0', 'businfo', 'pci@0000:03:00.0'),
             ('network', 'wlan0', 'vendor', 'Intel Corporation'),
             ('network', 'wlan0', 'product',
              'Centrino Advanced-N 6205 [Taylor Peak]'),
             ('network', 'wlan0', 'firmware', '18.168.6.1'),
             ('network', 'wlan0', 'ipv4', '192.168.1.185'),
             ('network', 'wlan0', 'ipv4-netmask', '255.255.255.0'),
             ('network', 'wlan0', 'ipv4-cidr', '24'),
             ('network', 'wlan0', 'ipv4-network', '192.168.1.0'),
             ('network', 'wlan0', 'link', 'yes'),
             ('network', 'wlan0', 'driver', 'iwlwifi'),
             ('network', 'wlan0', 'latency', '0'),
             ('network', 'wlan0', 'serial', '84:3a:4b:33:62:82'),
             ('network', 'wwan0', 'firmware',
              'Mobile Broadband Network Device'),
             ('network', 'wwan0', 'link', 'no'),
             ('network', 'wwan0', 'driver', 'cdc_ncm'),
             ('network', 'wwan0', 'serial', '02:15:e0:ec:01:00'),
             ('system', 'os', 'vendor', 'Ubuntu'),
             ('system', 'os', 'version', 'Ubuntu 14.04 LTS'),
             ('system', 'kernel', 'version', '3.13.0-24-generic'),
             ('system', 'kernel', 'arch', 'x86_64'),
             ('system', 'kernel', 'cmdline', 'BOOT_IMAGE=/boot/vmlinuz'),
             ]
        )

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
    def test_detect_system(self, mock_cmd, mock_get_uuid, mock_get_cpus, mock_output_lines):
        result = []
        detect.detect_system(result, sample('lshw'))
        self.assertEqual(
            result,
            [('system', 'product', 'serial', 'C02JR02WF57J'),
             ('system', 'product', 'name', 'MacBookAir5,2 (System SKU#)'),
             ('system', 'product', 'vendor', 'Apple Inc.'),
             ('system', 'product', 'version', '1.0'),
             ('system', 'product', 'uuid', '83462C81-52BA-11CB-870F'),
             ('system', 'motherboard', 'name', 'Mac-2E6FAB96566FE58C'),
             ('system', 'motherboard', 'vendor', 'Apple Inc.'),
             ('system', 'motherboard', 'version', 'MacBookAir5,2'),
             ('system', 'motherboard', 'serial', 'C02245301ZFF25WAT'),
             ('firmware', 'bios', 'version', 'MBA51.88Z.00EF.B01.1207271122'),
             ('firmware', 'bios', 'date', '07/27/2012'),
             ('firmware', 'bios', 'vendor', 'Apple Inc.'),
             ('memory', 'total', 'size', '8589934592'),
             ('memory', 'bank:0', 'size', '4294967296'),
             ('memory', 'bank:0', 'clock', '1600000000'),
             ('memory', 'bank:0', 'description',
              'SODIMM DDR3 Synchronous 1600 MHz (0,6 ns)'),
             ('memory', 'bank:0', 'vendor',
              'Hynix Semiconductor (Hyundai Electronics)'),
             ('memory', 'bank:0', 'product', 'HMT451S6MFR8A-PB'),
             ('memory', 'bank:0', 'serial', '0x00000000'),
             ('memory', 'bank:0', 'slot', 'DIMM0'),
             ('memory', 'bank:1', 'size', '4294967296'),
             ('memory', 'bank:1', 'clock', '1600000000'),
             ('memory', 'bank:1', 'description',
              'SODIMM DDR3 Synchronous 1600 MHz (0,6 ns)'),
             ('memory', 'bank:1', 'vendor',
              'Hynix Semiconductor (Hyundai Electronics)'),
             ('memory', 'bank:1', 'product', 'HMT451S6MFR8A-PB'),
             ('memory', 'bank:1', 'serial', '0x00000000'),
             ('memory', 'bank:1', 'slot', 'DIMM0'),
             ('memory', 'banks', 'count', '2'),
             ('network', 'vnet0', 'size', '10000000'),
             ('network', 'vnet0', 'link', 'yes'),
             ('network', 'vnet0', 'driver', 'tun'),
             ('network', 'vnet0', 'duplex', 'full'),
             ('network', 'vnet0', 'speed', '10Mbit/s'),
             ('network', 'vnet0', 'autonegotiation', 'off'),
             ('network', 'vnet0', 'serial', 'fe:54:00:c1:1a:f7'),
             ('network', 'tap0', 'size', '10000000'),
             ('network', 'tap0', 'ipv4', '10.152.18.103'),
             ('network', 'tap0', 'ipv4-netmask', '255.255.255.0'),
             ('network', 'tap0', 'ipv4-cidr', '24'),
             ('network', 'tap0', 'ipv4-network', '10.152.18.0'),
             ('network', 'tap0', 'link', 'yes'),
             ('network', 'tap0', 'driver', 'tun'),
             ('network', 'tap0', 'duplex', 'full'),
             ('network', 'tap0', 'speed', '10Mbit/s'),
             ('network', 'tap0', 'autonegotiation', 'off'),
             ('network', 'tap0', 'serial', 'e2:66:69:22:be:fb'),
             ('network', 'wlan0', 'firmware', 'N/A'),
             ('network', 'wlan0', 'ipv4', '192.168.12.13'),
             ('network', 'wlan0', 'ipv4-netmask', '255.255.255.0'),
             ('network', 'wlan0', 'ipv4-cidr', '24'),
             ('network', 'wlan0', 'ipv4-network', '192.168.12.0'),
             ('network', 'wlan0', 'link', 'yes'),
             ('network', 'wlan0', 'driver', 'brcmsmac'),
             ('network', 'wlan0', 'serial', '00:88:65:35:2b:50'),
             ('system', 'os', 'vendor', 'Ubuntu'),
             ('system', 'os', 'version', 'Ubuntu 14.04 LTS'),
             ('system', 'kernel', 'version', '3.13.0-24-generic'),
             ('system', 'kernel', 'arch', 'x86_64'),
             ('system', 'kernel', 'cmdline', 'BOOT_IMAGE=/boot/vmlinuz'),
             ]
        )

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
