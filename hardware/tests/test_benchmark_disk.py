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


FIO_OUTPUT_READ = """{
    "jobs": [
        {
        "jobname": "MYJOB-fake-disk",
        "groupid": 0,
        "error": 0,
        "read": {
            "io_bytes": 126418944,
            "io_kbytes": 123456,
            "bw_bytes": 126418944,
            "bw": 123456,
            "iops": 123,
            "runtime": 10304
            },
        "write": {
            "io_bytes": 0,
            "io_kbytes": 0,
            "bw_bytes": 0,
            "bw": 0,
            "iops": 0,
            "runtime": 0
            }
        }
        ]
    }"""

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


@mock.patch.object(subprocess, 'check_output')
class TestBenchmarkDisk(unittest.TestCase):

    def setUp(self):
        super(TestBenchmarkDisk, self).setUp()
        self.hw_data = [('disk', 'fake-disk', 'size', '10'),
                        ('disk', 'fake-disk2', 'size', '15')]

    def test_disk_perf_bytes(self, mock_check_output):
        mock_check_output.return_value = FIO_OUTPUT_READ.encode('utf-8')
        disk.disk_perf(self.hw_data)
        self.assertEqual(sorted(DISK_PERF_EXPECTED), sorted(self.hw_data))

    def test_get_disks_name(self, mock_check_output):
        result = disk.get_disks_name(self.hw_data)
        self.assertEqual(sorted(['fake-disk', 'fake-disk2']), sorted(result))

    def test_run_fio(self, mock_check_output):
        mock_check_output.return_value = FIO_OUTPUT_READ.encode('utf-8')
        hw_data = []
        disks_list = ['fake-disk', 'fake-disk2']
        disk.run_fio(hw_data, disks_list, "read", 123, 10, 5)
        self.assertEqual(sorted(
            [('disk', 'fake-disk', 'simultaneous_read_123_KBps', '123456'),
             ('disk', 'fake-disk', 'simultaneous_read_123_IOps', '123')]),
            sorted(hw_data))
