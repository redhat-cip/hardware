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

import fcntl
import socket
import unittest

import mock

from hardware import detect
from hardware import detect_utils
from hardware.tests.utils import sample


class Keeper:
    def __init__(self, fname, rets):
        self.rets = rets
        self.fname = fname

    def fake(self, arg):
        if len(self.rets) == 0:
            raise Exception('Invalid call to %s(%s)' % (self.fname, arg))
#         else:
#             print('Call to %s(%s)' % (self.fname, arg))
        ret = self.rets[0]
        self.rets = self.rets[1:]
        return ret


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

    def _save_functions(self, nbproc, nbphys):
        # replace the call to nproc by a fake result
        self.save = detect_utils.cmd
        self.output_lines = detect_utils.output_lines
        self.saved_ntoa = socket.inet_ntoa
        self.saved_ioctl = fcntl.ioctl
        self.saved_get_uuid = detect.get_uuid
        self.saved_lld_status = detect_utils.get_lld_status
        self.saved_ethtool_status = detect_utils.get_ethtool_status

        def fake(x):
            return (0, nbproc)

        def fake_ntoa(arg):
            return '255.255.255.0'

        def fake_ioctl(arg, arg2, arg3):
            return []

        def fake_get_uuid():
            return '83462C81-52BA-11CB-870F'

        def fake_lld_status(arg, arg1):
            return []

        def fake_ethtool_status(arg, arg1):
            return []

        detect_utils.cmd = fake
        keeper = Keeper('detect.output_lines',
                        [('Ubuntu', ),
                         ('Ubuntu 14.04 LTS', ),
                         ('3.13.0-24-generic', ),
                         ('x86_64', ),
                         ('BOOT_IMAGE=/boot/vmlinuz', )])
        detect_utils.output_lines = mock.MagicMock(side_effect=keeper.fake)
        socket.inet_ntoa = fake_ntoa
        fcntl.ioctl = fake_ioctl
        detect.get_uuid = fake_get_uuid
        detect_utils.get_lld_status = fake_lld_status
        detect_utils.get_ethtool_status = fake_ethtool_status

    def test_ipmi_sdr(self):
        hw = []
        detect_utils.parse_ipmi_sdr(hw, IPMI_SDR.split("\n"))
        self.assertEqual(hw, [('ipmi', 'UID Light', 'value', '0x00'),
                              ('ipmi', 'Sys. Health LED', 'value', '0x00'),
                              ('ipmi', 'Power Supply 1', 'value', '90'),
                              ('ipmi', 'Power Supply 1', 'unit', 'Watts'),
                              ('ipmi', 'Power Supply 2', 'value', '65'),
                              ('ipmi', 'Power Supply 2', 'unit', 'Watts'),
                              ('ipmi', 'Power Supplies', 'value', '0x00'),
                              ('ipmi', 'Fan 1', 'value', '33.32'),
                              ('ipmi', 'Fan 1', 'unit', 'percent'),
                              ('ipmi', 'Fan 2', 'value', '39.20'),
                              ('ipmi', 'Fan 2', 'unit', 'percent'),
                              ('ipmi', 'Fan 3', 'value', '39.20'),
                              ('ipmi', 'Fan 3', 'unit', 'percent'),
                              ('ipmi', 'Fan 4', 'value', '29.40'),
                              ('ipmi', 'Fan 4', 'unit', 'percent'),
                              ('ipmi', 'Fan 5', 'value', '24.70'),
                              ('ipmi', 'Fan 5', 'unit', 'percent'),
                              ('ipmi', 'Fan 6', 'value', '13.72'),
                              ('ipmi', 'Fan 6', 'unit', 'percent'),
                              ('ipmi', 'Fans', 'value', '0x00'),
                              ('ipmi', 'Temp 1', 'value', '20'),
                              ('ipmi', 'Temp 1', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 2', 'value', '40'),
                              ('ipmi', 'Temp 2', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 3', 'value', '40'),
                              ('ipmi', 'Temp 3', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 4', 'value', '28'),
                              ('ipmi', 'Temp 4', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 5', 'value', '28'),
                              ('ipmi', 'Temp 5', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 6', 'value', '34'),
                              ('ipmi', 'Temp 6', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 7', 'value', '33'),
                              ('ipmi', 'Temp 7', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 8', 'value', '39'),
                              ('ipmi', 'Temp 8', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 9', 'value', '33'),
                              ('ipmi', 'Temp 9', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 10', 'value', '39'),
                              ('ipmi', 'Temp 10', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 11', 'value', '29'),
                              ('ipmi', 'Temp 11', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 12', 'value', '40'),
                              ('ipmi', 'Temp 12', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 13', 'value', '28'),
                              ('ipmi', 'Temp 13', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 14', 'value', '31'),
                              ('ipmi', 'Temp 14', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 15', 'value', '29'),
                              ('ipmi', 'Temp 15', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 16', 'value', '25'),
                              ('ipmi', 'Temp 16', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 17', 'value', '27'),
                              ('ipmi', 'Temp 17', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 18', 'value', 'disabled'),
                              ('ipmi', 'Temp 19', 'value', '22'),
                              ('ipmi', 'Temp 19', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 20', 'value', '28'),
                              ('ipmi', 'Temp 20', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 21', 'value', '28'),
                              ('ipmi', 'Temp 21', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 22', 'value', '28'),
                              ('ipmi', 'Temp 22', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 23', 'value', '33'),
                              ('ipmi', 'Temp 23', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 24', 'value', '30'),
                              ('ipmi', 'Temp 24', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 25', 'value', '30'),
                              ('ipmi', 'Temp 25', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 26', 'value', '31'),
                              ('ipmi', 'Temp 26', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 27', 'value', 'disabled'),
                              ('ipmi', 'Temp 28', 'value', '26'),
                              ('ipmi', 'Temp 28', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 29', 'value', '35'),
                              ('ipmi', 'Temp 29', 'unit', 'degrees C'),
                              ('ipmi', 'Temp 30', 'value', '58'),
                              ('ipmi', 'Temp 30', 'unit', 'degrees C'),
                              ('ipmi', 'Memory', 'value', '0x00'),
                              ('ipmi', 'Power Meter', 'value', '170'),
                              ('ipmi', 'Power Meter', 'unit', 'Watts'),
                              ('ipmi', 'Cntlr 1 Bay 1', 'value', '0x01'),
                              ('ipmi', 'Cntlr 1 Bay 2', 'value', '0x01'),
                              ('ipmi', 'Cntlr 1 Bay 3', 'value', '0x00'),
                              ('ipmi', 'Cntlr 1 Bay 4', 'value', '0x01'),
                              ('ipmi', 'Cntlr 2 Bay 5', 'value', '0x00'),
                              ('ipmi', 'Cntlr 2 Bay 6', 'value', '0x00'),
                              ('ipmi', 'Cntlr 2 Bay 7', 'value', '0x01'),
                              ('ipmi', 'Cntlr 2 Bay 8', 'value', '0x01')])

    def test_parse_dmesg(self):
        hw = []
        detect.parse_dmesg(hw, sample('dmesg'))
        self.assertEqual(hw, [('ahci', '0000:00:1f.2:', 'flags',
                               '64bit apst clo ems led '
                               'ncq part pio slum sntf')])

    def _restore_functions(self):
        detect.cmd = self.save
        detect.output_lines = self.output_lines
        socket.inet_ntoa = self.saved_ntoa
        fcntl.ioctl = self.saved_ioctl
        detect.get_uuid = self.saved_get_uuid
        detect_utils.get_lld_status = self.saved_lld_status
        detect_utils.get_ethtool_status = self.saved_ethtool_status

    def test_detect_system_3(self):
        l = []
        self._save_functions("4", 2)
        detect.detect_system(l, sample('lshw3'))
        self._restore_functions()
        self.assertEqual(
            l,
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
             ('cpu', 'physical_0', 'physid', '3'),
             ('cpu', 'physical_0', 'product',
              'Dual-Core AMD Opteron(tm) Processor 8218'),
             ('cpu', 'physical_0', 'vendor', 'Advanced Micro Devices [AMD]'),
             ('cpu', 'physical_0', 'version', 'AMD'),
             ('cpu', 'physical_0', 'frequency', '1000000000'),
             ('cpu', 'physical_0', 'clock', '200000000'),
             ('cpu', 'physical_0', 'flags',
              'fpu fpu_exception wp vme de pse tsc msr pae mce cx8 apic '
              'sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht '
              'syscall nx mmxext fxsr_opt rdtscp x86-64 3dnowext 3dnow '
              'rep_good nopl extd_apicid pni cx16 lahf_lm cmp_legacy svm '
              'extapic cr8_legacy cpufreq'),
             ('cpu', 'physical_1', 'physid', '4'),
             ('cpu', 'physical_1', 'product',
              'Dual-Core AMD Opteron(tm) Processor 8218'),
             ('cpu', 'physical_1', 'vendor', 'Advanced Micro Devices [AMD]'),
             ('cpu', 'physical_1', 'version', 'AMD'),
             ('cpu', 'physical_1', 'frequency', '1000000000'),
             ('cpu', 'physical_1', 'clock', '200000000'),
             ('cpu', 'physical_1', 'flags',
              'fpu fpu_exception wp vme de pse tsc msr pae mce cx8 apic sep '
              'mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht '
              'syscall nx mmxext fxsr_opt rdtscp x86-64 3dnowext 3dnow '
              'rep_good nopl extd_apicid pni cx16 lahf_lm cmp_legacy svm '
              'extapic cr8_legacy cpufreq'),
             ('cpu', 'physical', 'number', '2'),
             ('cpu', 'logical', 'number', '4'),
             ('system', 'os', 'vendor', 'Ubuntu'),
             ('system', 'os', 'version', 'Ubuntu 14.04 LTS'),
             ('system', 'kernel', 'version', '3.13.0-24-generic'),
             ('system', 'kernel', 'arch', 'x86_64'),
             ('system', 'kernel', 'cmdline', 'BOOT_IMAGE=/boot/vmlinuz'),
             ]
            )

    def test_detect_system_2(self):
        l = []
        self._save_functions("4", 1)
        detect.detect_system(l, sample('lshw2'))
        self._restore_functions()
        self.assertEqual(
            l,
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
             ('cpu', 'physical_0', 'physid', '1'),
             ('cpu', 'physical_0', 'product',
              'Intel(R) Core(TM) i5-3320M CPU @ 2.60GHz'),
             ('cpu', 'physical_0', 'vendor', 'Intel Corp.'),
             ('cpu', 'physical_0', 'version',
              'Intel(R) Core(TM) i5-3320M CPU @ 2.60GHz'),
             ('cpu', 'physical_0', 'frequency', '2601000000'),
             ('cpu', 'physical_0', 'clock', '100000000'),
             ('cpu', 'physical_0', 'cores', '2'),
             ('cpu', 'physical_0', 'enabled_cores', '2'),
             ('cpu', 'physical_0', 'threads', '4'),
             ('cpu', 'physical_0', 'flags',
              'x86-64 fpu fpu_exception wp vme de pse tsc msr pae mce cx8 '
              'apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr '
              'sse sse2 ss ht tm pbe syscall nx rdtscp constant_tsc '
              'arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc '
              'aperfmperf eagerfpu pni pclmulqdq dtes64 monitor ds_cpl vmx '
              'smx est tm2 ssse3 cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic '
              'popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm '
              'ida arat epb xsaveopt pln pts dtherm tpr_shadow vnmi '
              'flexpriority ept vpid fsgsbase smep erms cpufreq'),
             ('cpu', 'physical', 'number', '1'),
             ('cpu', 'logical', 'number', '4'),
             ('system', 'os', 'vendor', 'Ubuntu'),
             ('system', 'os', 'version', 'Ubuntu 14.04 LTS'),
             ('system', 'kernel', 'version', '3.13.0-24-generic'),
             ('system', 'kernel', 'arch', 'x86_64'),
             ('system', 'kernel', 'cmdline', 'BOOT_IMAGE=/boot/vmlinuz'),
             ]
            )

    def test_detect_system(self):
        self.maxDiff = None
        l = []
        self._save_functions("7", 4)
        detect.detect_system(l, sample('lshw'))
        self._restore_functions()
        self.assertEqual(
            l,
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
             ('cpu', 'physical_0', 'physid', '0'),
             ('cpu', 'physical_0', 'product',
              'Intel(R) Core(TM) i7-3667U CPU @ 2.00GHz'),
             ('cpu', 'physical_0', 'vendor', 'Intel Corp.'),
             ('cpu', 'physical_0', 'version',
              'Intel(R) Core(TM) i7-3667U CPU @ 2.00GHz'),
             ('cpu', 'physical_0', 'frequency', '800000000'),
             ('cpu', 'physical_0', 'clock', '25000000'),
             ('cpu', 'physical_0', 'flags',
              'fpu fpu_exception wp vme de pse tsc msr pae mce cx8 apic sep '
              'mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 '
              'ss ht tm pbe syscall nx rdtscp x86-64 constant_tsc '
              'arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc '
              'aperfmperf eagerfpu pni pclmulqdq dtes64 monitor ds_cpl vmx '
              'smx est tm2 ssse3 cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic '
              'popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm '
              'ida arat xsaveopt pln pts dtherm tpr_shadow vnmi flexpriority '
              'ept vpid fsgsbase smep erms cpufreq'),
             ('cpu', 'physical_1', 'physid', '5'),
             ('cpu', 'physical_1', 'vendor', 'Intel(R) Corporation'),
             ('cpu', 'physical_1', 'version',
              'Intel(R) Core(TM) i7-3667U CPU @ 2.00GHz'),
             ('cpu', 'physical_1', 'frequency', '800000000'),
             ('cpu', 'physical_1', 'clock', '25000000'),
             ('cpu', 'physical_1', 'flags', 'cpufreq'),
             ('cpu', 'physical_2', 'physid', 'a'),
             ('cpu', 'physical_2', 'vendor', 'Intel(R) Corporation'),
             ('cpu', 'physical_2', 'version',
              'Intel(R) Core(TM) i7-3667U CPU @ 2.00GHz'),
             ('cpu', 'physical_2', 'frequency', '800000000'),
             ('cpu', 'physical_2', 'clock', '25000000'),
             ('cpu', 'physical_2', 'flags', 'cpufreq'),
             ('cpu', 'physical_3', 'physid', 'f'),
             ('cpu', 'physical_3', 'vendor', 'Intel(R) Corporation'),
             ('cpu', 'physical_3', 'version',
              'Intel(R) Core(TM) i7-3667U CPU @ 2.00GHz'),
             ('cpu', 'physical_3', 'frequency', '800000000'),
             ('cpu', 'physical_3', 'clock', '25000000'),
             ('cpu', 'physical_3', 'flags', 'cpufreq'),
             ('cpu', 'physical', 'number', '4'),
             ('cpu', 'logical', 'number', '7'),
             ('system', 'os', 'vendor', 'Ubuntu'),
             ('system', 'os', 'version', 'Ubuntu 14.04 LTS'),
             ('system', 'kernel', 'version', '3.13.0-24-generic'),
             ('system', 'kernel', 'arch', 'x86_64'),
             ('system', 'kernel', 'cmdline', 'BOOT_IMAGE=/boot/vmlinuz'),
             ]
            )

IPMI_SDR = '''UID Light        | 0x00              | ok
Sys. Health LED  | 0x00              | ok
Power Supply 1   | 90 Watts          | ok
Power Supply 2   | 65 Watts          | ok
Power Supplies   | 0x00              | ok
Fan 1            | 33.32 percent     | ok
Fan 2            | 39.20 percent     | ok
Fan 3            | 39.20 percent     | ok
Fan 4            | 29.40 percent     | ok
Fan 5            | 24.70 percent     | ok
Fan 6            | 13.72 percent     | ok
Fans             | 0x00              | ok
Temp 1           | 20 degrees C      | ok
Temp 2           | 40 degrees C      | ok
Temp 3           | 40 degrees C      | ok
Temp 4           | 28 degrees C      | ok
Temp 5           | 28 degrees C      | ok
Temp 6           | 34 degrees C      | ok
Temp 7           | 33 degrees C      | ok
Temp 8           | 39 degrees C      | ok
Temp 9           | 33 degrees C      | ok
Temp 10          | 39 degrees C      | ok
Temp 11          | 29 degrees C      | ok
Temp 12          | 40 degrees C      | ok
Temp 13          | 28 degrees C      | ok
Temp 14          | 31 degrees C      | ok
Temp 15          | 29 degrees C      | ok
Temp 16          | 25 degrees C      | ok
Temp 17          | 27 degrees C      | ok
Temp 18          | disabled          | ns
Temp 19          | 22 degrees C      | ok
Temp 20          | 28 degrees C      | ok
Temp 21          | 28 degrees C      | ok
Temp 22          | 28 degrees C      | ok
Temp 23          | 33 degrees C      | ok
Temp 24          | 30 degrees C      | ok
Temp 25          | 30 degrees C      | ok
Temp 26          | 31 degrees C      | ok
Temp 27          | disabled          | ns
Temp 28          | 26 degrees C      | ok
Temp 29          | 35 degrees C      | ok
Temp 30          | 58 degrees C      | ok
Memory           | 0x00              | ok
Power Meter      | 170 Watts         | ok
Cntlr 1 Bay 1    | 0x01              | ok
Cntlr 1 Bay 2    | 0x01              | ok
Cntlr 1 Bay 3    | 0x00              | ok
Cntlr 1 Bay 4    | 0x01              | ok
Cntlr 2 Bay 5    | 0x00              | ok
Cntlr 2 Bay 6    | 0x00              | ok
Cntlr 2 Bay 7    | 0x01              | ok
Cntlr 2 Bay 8    | 0x01              | ok
'''
