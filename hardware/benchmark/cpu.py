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
"""
Benchmark CPU functions.
"""

import subprocess
import sys

from hardware.benchmark import utils


def run_sysbench_cpu(hw_lst, max_time, cpu_count, processor_num=None):
    """Running sysbench cpu stress of a give amount of logical cpu.

    :param hw_lst: The hardware inventory list.
    :param max_time: Limit for total execution time in seconds.
    :param cpu_count: Number of threads to use for the benchmark.
    :param processor_num: The CPU number to be tested, if None it
        will test all CPUs. Defaults to None.

    """
    taskset = ''
    if processor_num is not None:
        sys.stderr.write('Benchmarking CPU %d for %d seconds (%d threads)\n' %
                         (processor_num, max_time, cpu_count))
        taskset = 'taskset %s' % hex(1 << processor_num)
    else:
        sys.stderr.write('Benchmarking all CPUs for '
                         '%d seconds (%d threads)\n' % (max_time, cpu_count))

    cmds = ('%s sysbench --max-time=%d --max-requests=10000000'
            ' --num-threads=%d --test=cpu --cpu-max-prime=15000 run'
            % (taskset, max_time, cpu_count))
    sysbench_cmd = subprocess.Popen(cmds, shell=True, stdout=subprocess.PIPE)

    for line in sysbench_cmd.stdout:
        line = line.decode()
        if "total number of events" in line:
            line_ = line.rstrip('\n').replace(' ', '')
            _, perf = line_.split(':')

            value = str(int(int(perf) / max_time))
            if processor_num is not None:
                hw_lst.append(('cpu',
                               'logical_%d' % processor_num,
                               'loops_per_sec', value))
            else:
                hw_lst.append(('cpu', 'logical', 'loops_per_sec', value))


def search_cpuinfo(processor_num, item):
    """Search for information about a given CPU."""
    cpuinfo = open('/proc/cpuinfo', 'r')
    found = False
    for line in cpuinfo:
        if line.strip():
            values = line.rstrip('\n').split(':')
            if "processor" in values[0] and int(values[1]) == processor_num:
                found = True
            if (item in values[0]) and (found is True):
                return values[1].replace(' ', '')
    cpuinfo.close()
    return None


def get_bogomips(hw_lst, processor_num):
    """Get the number og bogomips of a given CPU."""
    bogo = search_cpuinfo(processor_num, "bogomips")
    if bogo is not None:
        hw_lst.append(('cpu', 'logical_%d' % processor_num, 'bogomips', bogo))


def get_cache_size(hw_lst, processor_num):
    """Get the cache size of a given CPU."""
    cache_size = search_cpuinfo(processor_num, "cache size")
    if cache_size is not None:
        hw_lst.append(('cpu', 'logical_%d' % processor_num,
                       'cache_size', cache_size))


def cpu_perf(hw_lst, max_time=10, burn_test=False):
    """Perform CPU's performance test.

    :param hw_lst: The hardware inventory list.
    :param max_time: Limit for total execution time in seconds.
        Defaults to 10.
    :param burn_test: Boolean value. Whether to perform a burn
        test. Defaults to False.

    """
    logical = utils.get_value(hw_lst, 'cpu', 'logical', 'number')
    physical = utils.get_value(hw_lst, 'cpu', 'physical', 'number')

    # Individual Test aren't useful for burn_test
    if burn_test is False:
        if physical is not None:
            sys.stderr.write('CPU Performance: %d logical '
                             'CPU to test (ETA: %d seconds)\n'
                             % (int(physical),
                                (int(physical) + 1) * max_time))
            for processor_num in utils.get_one_cpu_per_socket(hw_lst):
                get_bogomips(hw_lst, processor_num)
                get_cache_size(hw_lst, processor_num)
                run_sysbench_cpu(hw_lst, max_time, 1, processor_num)
    else:
        sys.stderr.write('CPU Burn: %d logical'
                         ' CPU to test (ETA: %d seconds)\n' % (
                             int(logical), max_time))

    run_sysbench_cpu(hw_lst, max_time, int(logical))
