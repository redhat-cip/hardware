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

from hardware.benchmark import cpu
from hardware.benchmark import utils


SYSBENCH_OUTPUT = """Test execution summary:
    total time:                          10.0012s
    total number of events:              1234
    total time taken by event execution: 9.9994
    per-request statistics:
         min:                                  1.53ms
         avg:                                  1.70ms
         max:                                  5.02ms
         approx.  95 percentile:               2.29ms

Threads fairness:
    events (avg/stddev):           5893.0000/0.00
    execution time (avg/stddev):   9.9994/0.00"""


@mock.patch.object(cpu, 'search_cpuinfo')
@mock.patch.object(utils, 'get_one_cpu_per_socket')
@mock.patch.object(subprocess, 'Popen')
class TestBenchmarkCPU(unittest.TestCase):

    def setUp(self):
        super(TestBenchmarkCPU, self).setUp()
        self.hw_data = [('cpu', 'logical', 'number', 2),
                        ('cpu', 'physical', 'number', 2)]

    def test_cpu_perf(self, mock_popen, mock_cpu_socket, mock_search_info):
        mock_cpu_socket.return_value = range(2)
        mock_search_info.side_effect = ('fake-bogomips1', 'fake-cache1',
                                        'fake-bogomips2', 'fake-cache2')
        cpu.cpu_perf(self.hw_data)
        expected = [
            ('cpu', 'logical', 'number', 2),
            ('cpu', 'physical', 'number', 2),
            ('cpu', 'logical_0', 'bogomips', 'fake-bogomips1'),
            ('cpu', 'logical_0', 'cache_size', 'fake-cache1'),
            ('cpu', 'logical_1', 'bogomips', 'fake-bogomips2'),
            ('cpu', 'logical_1', 'cache_size', 'fake-cache2')
        ]
        self.assertEqual(sorted(expected), sorted(self.hw_data))
        expected = [mock.call(0, "bogomips"),
                    mock.call(0, "cache size"),
                    mock.call(1, "bogomips"),
                    mock.call(1, "cache size")]
        mock_search_info.assert_has_calls(expected)

    def test_get_bogomips(self, mock_popen, mock_cpu_socket, mock_search_info):
        mock_search_info.return_value = 'fake-bogomips'
        hw_data = []
        cpu.get_bogomips(hw_data, 0)

        self.assertEqual([('cpu', 'logical_0', 'bogomips', 'fake-bogomips')],
                         hw_data)
        mock_search_info.assert_called_once_with(0, 'bogomips')

    def test_get_cache_size(self, mock_popen, mock_cpu_socket,
                            mock_search_info):
        mock_search_info.return_value = 'fake-cache'
        hw_data = []
        cpu.get_cache_size(hw_data, 0)
        self.assertEqual([('cpu', 'logical_0', 'cache_size', 'fake-cache')],
                         hw_data)
        mock_search_info.assert_called_once_with(0, 'cache size')

    def test_run_sysbench_cpu_bytes(self, mock_popen, mock_cpu_socket,
                                    mock_search_info):
        mock_popen.return_value = mock.Mock(
            stdout=SYSBENCH_OUTPUT.encode().splitlines())
        hw_data = []
        cpu.run_sysbench_cpu(hw_data, 10, 1)
        mock_popen.assert_called_once_with(' sysbench --max-time=10 '
                                           '--max-requests=10000000 '
                                           '--num-threads=1 --test=cpu '
                                           '--cpu-max-prime=15000 run',
                                           shell=True, stdout=subprocess.PIPE)
        self.assertEqual([('cpu', 'logical', 'loops_per_sec', '123')], hw_data)
