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

import json
import os
import subprocess
import tempfile
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
        self.block_device_patcher = mock.patch.object(
            disk, '_is_block_device', return_value=True)
        self.block_device_patcher.start()
        self.addCleanup(self.block_device_patcher.stop)
        self.cache_flush_patcher = mock.patch.object(disk, '_flush_disk_cache')
        self.cache_flush_patcher.start()
        self.addCleanup(self.cache_flush_patcher.stop)

    def test_disk_perf_bytes(self, mock_check_output):
        mock_check_output.return_value = FIO_OUTPUT_READ.encode('utf-8')
        disk.disk_perf(self.hw_data)
        self.assertEqual(sorted(DISK_PERF_EXPECTED), sorted(self.hw_data))

    def test_get_disks_name(self, mock_check_output):
        result = disk.get_disks_name(self.hw_data)
        self.assertEqual(sorted(['fake-disk', 'fake-disk2']), sorted(result))

    def test_mounted_device_lookup_includes_backing_disks(self,
                                                          mock_check_output):
        mounts = {
            'filesystems': [{
                'target': '/',
                'source': '/dev/mapper/root[/root]',
                'children': [{
                    'target': '/boot',
                    'source': '/dev/nvme0n1p2',
                }],
            }],
        }
        lsblk_output = {
            '/dev/mapper/root': {
                'blockdevices': [{
                    'name': '/dev/mapper/root',
                    'type': 'crypt',
                    'children': [{
                        'name': '/dev/nvme0n1p3',
                        'type': 'part',
                        'children': [{
                            'name': '/dev/nvme0n1',
                            'type': 'disk',
                        }],
                    }],
                }],
            },
            '/dev/nvme0n1p2': {
                'blockdevices': [{
                    'name': '/dev/nvme0n1p2',
                    'type': 'part',
                    'children': [{
                        'name': '/dev/nvme0n1',
                        'type': 'disk',
                    }],
                }],
            },
            '/dev/sdb1': {
                'blockdevices': [{
                    'name': '/dev/sdb1',
                    'type': 'part',
                    'children': [{
                        'name': '/dev/sdb',
                        'type': 'disk',
                    }],
                }],
            },
        }

        def run(args, **kwargs):
            if args[0] == 'findmnt':
                return subprocess.CompletedProcess(
                    args, 0, json.dumps(mounts), '')
            return subprocess.CompletedProcess(
                args, 0, json.dumps(lsblk_output[args[-1]]), '')

        with mock.patch.object(disk.subprocess, 'run', side_effect=run), \
                mock.patch.object(disk, '_get_swap_device_sources',
                                  return_value={'/dev/sdb1'}):
            self.assertEqual(
                disk._get_mounted_device_names(),
                {'root', 'nvme0n1p2', 'nvme0n1p3', 'nvme0n1',
                 'sdb1', 'sdb'})

    def test_unknown_mount_topology_blocks_destructive_candidates(
            self, mock_check_output):
        with mock.patch.object(disk, '_get_mounted_device_names',
                               return_value=None):
            self.assertTrue(disk.is_booted_storage_device('fake-disk'))
            self.assertEqual(disk.get_disks_name(self.hw_data, True), [])

    @mock.patch.object(disk, 'run_fio')
    @mock.patch.object(disk, '_get_mounted_device_names',
                       return_value={'fake-disk'})
    def test_destructive_benchmark_skips_mounted_devices(
            self, _mounted_devices, run_fio, mock_check_output):
        disk.disk_perf(self.hw_data, destructive=True, running_time=1)

        write_calls = [call for call in run_fio.call_args_list
                       if call.args[2] in ('write', 'randwrite')]
        self.assertEqual(len(write_calls), 4)
        for call in write_calls:
            self.assertNotIn('fake-disk', call.args[1])

    @mock.patch.object(disk, 'run_fio')
    @mock.patch.object(disk, '_get_mounted_device_names', return_value=None)
    def test_destructive_benchmark_skips_all_writes_when_safety_unknown(
            self, _mounted_devices, run_fio, mock_check_output):
        disk.disk_perf(self.hw_data, destructive=True, running_time=1)

        self.assertFalse(any(call.args[2] in ('write', 'randwrite')
                             for call in run_fio.call_args_list))

    def test_run_fio(self, mock_check_output):
        mock_check_output.return_value = FIO_OUTPUT_READ.encode('utf-8')
        hw_data = []
        disks_list = ['fake-disk', 'fake-disk2']
        disk.run_fio(hw_data, disks_list, "read", 123, 10, 5)
        mock_check_output.assert_called_once_with([
            'fio', '--ioengine=libaio', '--invalidate=1', '--ramp_time=5',
            '--iodepth=32', '--runtime=10', '--time_based', '--direct=1',
            '--output-format=json', '--bs=123', '--rw=read',
            '--random_generator=tausworthe64', '--name=MYJOB-fake-disk',
            '--filename=/dev/fake-disk', '--name=MYJOB-fake-disk2',
            '--filename=/dev/fake-disk2'])
        self.assertEqual(sorted(
            [('disk', 'fake-disk', 'simultaneous_read_123_KBps', '123456'),
             ('disk', 'fake-disk', 'simultaneous_read_123_IOps', '123')]),
            sorted(hw_data))

    def test_run_fio_skips_non_block_targets(self, mock_check_output):
        with mock.patch.object(disk, '_is_block_device', return_value=False):
            disk.run_fio([], ['/tmp/not-a-block-device'], 'write', '1M', 1, 0)

        mock_check_output.assert_not_called()

    def test_run_fio_rejects_paths_outside_dev(self, mock_check_output):
        disk.run_fio([], ['/dev/../../tmp/not-a-device'], 'write', '1M', 1, 0)

        mock_check_output.assert_not_called()

    def test_run_fio_preserves_existing_fio_files(self, mock_check_output):
        mock_check_output.return_value = FIO_OUTPUT_READ.encode('utf-8')
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                os.chdir(tmpdir)
                with open('user-config.fio', 'w') as fio_file:
                    fio_file.write('user data')
                with mock.patch.object(disk.os, 'system'):
                    disk.run_fio([], ['fake-disk'], 'read', '1M', 1, 0)
                self.assertTrue(os.path.exists('user-config.fio'))
            finally:
                os.chdir(original_cwd)
