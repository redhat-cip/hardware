# -*- coding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import subprocess
import unittest
from unittest import mock

from hardware.benchmark import disk


FIO_OUTPUT_READ = """MYJOB-fake-disk: (groupid=0, jobs=1): err= 0: pid=5427:
  read : io=123456KB, bw=123456KB/s, iops=123, runt= 10304msec"""

DISK_PERF_EXPECTED = [
    ('disk', 'fake-disk', 'size', '10'),
    ('disk', 'fake-disk2', 'size', '15'),
    ('disk', 'fake-disk', 'standalone_read_1M_KBps', '123456'),
    ('disk', 'fake-disk', 'standalone_read_1M_IOps', '123'),
    ('disk', 'fake-disk', 'standalone_randread_4k_KBps', '123456'),
    ('disk', 'fake-disk', 'standalone_randread_4k_IOps', '123'),
    ('disk', 'fake-disk', 'standalone_read_1M_KBps', '123456'),
    ('disk', 'fake-disk', 'standalone_read_1M_IOps', '123'),
    ('disk', 'fake-disk', 'standalone_randread_4k_KBps', '123456'),
    ('disk', 'fake-disk', 'standalone_randread_4k_IOps', '123'),
    ('disk', 'fake-disk', 'simultaneous_read_1M_KBps', '123456'),
    ('disk', 'fake-disk', 'simultaneous_read_1M_IOps', '123'),
    ('disk', 'fake-disk', 'simultaneous_randread_4k_KBps', '123456'),
    ('disk', 'fake-disk', 'simultaneous_randread_4k_IOps', '123'),
]


@mock.patch.object(subprocess, 'Popen')
class TestBenchmarkDisk(unittest.TestCase):

    def setUp(self):
        super(TestBenchmarkDisk, self).setUp()
        self.hw_data = [('disk', 'fake-disk', 'size', '10'),
                        ('disk', 'fake-disk2', 'size', '15')]

    def test_disk_perf_bytes(self, mock_popen):
        mock_popen.return_value = mock.Mock(
            stdout=FIO_OUTPUT_READ.encode().splitlines())
        disk.disk_perf(self.hw_data)
        self.assertEqual(sorted(DISK_PERF_EXPECTED), sorted(self.hw_data))

    def test_get_disks_name(self, mock_popen):
        result = disk.get_disks_name(self.hw_data)
        self.assertEqual(sorted(['fake-disk', 'fake-disk2']), sorted(result))

    def test_run_fio(self, mock_popen):
        mock_popen.return_value = mock.Mock(
            stdout=FIO_OUTPUT_READ.encode().splitlines())
        hw_data = []
        disks_list = ['fake-disk', 'fake-disk2']
        disk.run_fio(hw_data, disks_list, "read", 123, 10, 5)
        self.assertEqual(sorted(
            [('disk', 'fake-disk', 'simultaneous_read_123_KBps', '123456'),
             ('disk', 'fake-disk', 'simultaneous_read_123_IOps', '123')]),
            sorted(hw_data))
