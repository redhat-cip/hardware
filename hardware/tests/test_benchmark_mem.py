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

from hardware.benchmark import mem
from hardware.benchmark import utils


SYSBENCH_OUTPUT = """Operations performed: 1957354 (391412.04 ops/sec)

1911.48 MB transferred (382.24 MB/sec)


Test execution summary:
    total time:                          5.0008s
    total number of events:              1957354
    total time taken by event execution: 3.0686
    per-request statistics:
         min:                                  0.00ms
         avg:                                  0.00ms
         max:                                  0.23ms
         approx.  95 percentile:               0.00ms

Threads fairness:
    events (avg/stddev):           1957354.0000/0.00
    execution time (avg/stddev):   3.0686/0.00"""

EXPECTED_RESULT = [
    ('cpu', 'logical', 'number', 2),
    ('cpu', 'physical', 'number', 2),
    ('cpu', 'logical_0', 'bandwidth_1K', '382'),
    ('cpu', 'logical_0', 'bandwidth_4K', '382'),
    ('cpu', 'logical_0', 'bandwidth_1M', '382'),
    ('cpu', 'logical_0', 'bandwidth_16M', '382'),
    ('cpu', 'logical_0', 'bandwidth_128M', '382'),
    ('cpu', 'logical_0', 'bandwidth_1G', '382'),
    ('cpu', 'logical_0', 'bandwidth_2G', '382'),
    ('cpu', 'logical_1', 'bandwidth_1K', '382'),
    ('cpu', 'logical_1', 'bandwidth_4K', '382'),
    ('cpu', 'logical_1', 'bandwidth_1M', '382'),
    ('cpu', 'logical_1', 'bandwidth_16M', '382'),
    ('cpu', 'logical_1', 'bandwidth_128M', '382'),
    ('cpu', 'logical_1', 'bandwidth_1G', '382'),
    ('cpu', 'logical_1', 'bandwidth_2G', '382'),
    ('cpu', 'logical', 'threaded_bandwidth_1K', '382'),
    ('cpu', 'logical', 'threaded_bandwidth_4K', '382'),
    ('cpu', 'logical', 'threaded_bandwidth_1M', '382'),
    ('cpu', 'logical', 'threaded_bandwidth_16M', '382'),
    ('cpu', 'logical', 'threaded_bandwidth_128M', '382'),
    ('cpu', 'logical', 'threaded_bandwidth_1G', '382'),
    ('cpu', 'logical', 'threaded_bandwidth_2G', '382'),
    ('cpu', 'logical', 'forked_bandwidth_1K', '382'),
    ('cpu', 'logical', 'forked_bandwidth_4K', '382'),
    ('cpu', 'logical', 'forked_bandwidth_1M', '382'),
    ('cpu', 'logical', 'forked_bandwidth_16M', '382'),
    ('cpu', 'logical', 'forked_bandwidth_128M', '382'),
    ('cpu', 'logical', 'forked_bandwidth_1G', '382'),
    ('cpu', 'logical', 'forked_bandwidth_2G', '382')
]


@mock.patch.object(mem, 'get_available_memory')
@mock.patch.object(utils, 'get_one_cpu_per_socket')
@mock.patch.object(subprocess, 'Popen')
class TestBenchmarkMem(unittest.TestCase):

    def setUp(self):
        super(TestBenchmarkMem, self).setUp()
        self.hw_data = [('cpu', 'logical', 'number', 2),
                        ('cpu', 'physical', 'number', 2)]

    def test_mem_perf_bytes(self, mock_popen, mock_cpu_socket,
                            mock_get_memory):
        mock_get_memory.return_value = 123456789012
        mock_popen.return_value = mock.Mock(
            stdout=SYSBENCH_OUTPUT.encode().splitlines())
        mock_cpu_socket.return_value = range(2)
        mem.mem_perf(self.hw_data)

        expected = EXPECTED_RESULT
        self.assertEqual(sorted(expected), sorted(self.hw_data))

    def test_check_mem_size(self, mock_popen, mock_cpu_socket,
                            mock_get_memory):
        block_size_list = ('1K', '4K', '1M', '16M', '128M', '1G', '2G')

        mock_get_memory.return_value = 123456789012
        for block_size in block_size_list:
            self.assertTrue(mem.check_mem_size(block_size, 2))

        # Low memory
        mock_get_memory.return_value = 1
        for block_size in block_size_list:
            self.assertFalse(mem.check_mem_size(block_size, 2))

    def test_run_sysbench_memory_forked_bytes(self, mock_popen,
                                              mock_cpu_socket,
                                              mock_get_memory):
        mock_get_memory.return_value = 123456789012
        mock_popen.return_value = mock.Mock(
            stdout=SYSBENCH_OUTPUT.encode().splitlines())

        hw_data = []
        mem.run_sysbench_memory_forked(hw_data, 10, '1K', 2)
        self.assertEqual([('cpu', 'logical', 'forked_bandwidth_1K', '382')],
                         hw_data)

    def test_run_sysbench_memory_threaded_bytes(self, mock_popen,
                                                mock_cpu_socket,
                                                mock_get_memory):
        mock_get_memory.return_value = 123456789012
        mock_popen.return_value = mock.Mock(
            stdout=SYSBENCH_OUTPUT.encode().splitlines())

        hw_data = []
        mem.run_sysbench_memory_threaded(hw_data, 10, '1K', 2)
        self.assertEqual([('cpu', 'logical', 'threaded_bandwidth_1K', '382')],
                         hw_data)
