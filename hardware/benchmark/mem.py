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
Benchmark Memory functions.
"""

import re
import subprocess
import sys

from hardware.benchmark import utils


def get_available_memory():
    """Return the total amount of available memory, in bytes."""
    with open('/proc/meminfo', 'r') as meminfo:
        for line in meminfo:
            if line.startswith('MemFree:'):
                return int(line.split()[1]) * 1024
    return -1


def check_mem_size(block_size, cpu_count):
    """Check if a test can run with a given block size and cpu count."""
    dsplit = re.compile(r'\d+')
    ssplit = re.compile(r'[A-Z]+')
    unit = ssplit.findall(block_size)
    unit_in_bytes = 1
    if unit[0] == 'K':
        unit_in_bytes = 1024
    elif unit[0] == 'M':
        unit_in_bytes = 1024 * 1024
    elif unit[0] == 'G':
        unit_in_bytes = 1024 * 1024 * 1024

    size_in_bytes = (unit_in_bytes * int(dsplit.findall(block_size)[0])
                     * cpu_count)
    if size_in_bytes > get_available_memory():
        return False

    return True


def run_sysbench_memory_threaded(hw_lst, max_time, block_size, cpu_count,
                                 processor_num=None):
    """Running memtest on a processor."""
    check_mem = check_mem_size(block_size, cpu_count)
    taskset = ''
    if processor_num is not None:
        if check_mem is False:
            msg = ("Avoid Benchmarking memory @%s "
                   "from CPU %d, not enough memory\n")
            sys.stderr.write(msg % (block_size, processor_num))
            return

        sys.stderr.write('Benchmarking memory @%s from CPU %d'
                         ' for %d seconds (%d threads)\n' %
                         (block_size, processor_num, max_time, cpu_count))
        taskset = 'taskset %s' % hex(1 << processor_num)
    else:
        if check_mem is False:
            msg = ("Avoid Benchmarking memory @%s "
                   "from all CPUs, not enough memory\n")
            sys.stderr.write(msg % block_size)
            return
        sys.stderr.write('Benchmarking memory @%s from all CPUs '
                         'for %d seconds (%d threads)\n'
                         % (block_size, max_time, cpu_count))

    _cmd = ('%s sysbench --max-time=%d --max-requests=100000000 '
            '--num-threads=%d --test=memory --memory-block-size=%s run')
    sysbench_cmd = subprocess.Popen(_cmd % (taskset, max_time,
                                            cpu_count, block_size),
                                    shell=True, stdout=subprocess.PIPE)

    for line in sysbench_cmd.stdout:
        line = line.decode()
        if "transferred" in line:
            _, right = line.rstrip('\n').replace(' ', '').split('(')
            perf, _ = right.split('.')
            if processor_num is not None:
                hw_lst.append(('cpu',
                               'logical_%d' % processor_num,
                               'bandwidth_%s' % block_size,
                               perf))
            else:
                hw_lst.append(('cpu', 'logical',
                               'threaded_bandwidth_%s' % block_size,
                               perf))


def run_sysbench_memory_forked(hw_lst, max_time, block_size, cpu_count):
    """Running forked memtest on a processor."""
    if check_mem_size(block_size, cpu_count) is False:
        cmd = ('Avoid benchmarking memory @%s from all'
               ' CPUs (%d forked processes), not enough memory\n')
        sys.stderr.write(cmd % (block_size, cpu_count))
        return
    sys.stderr.write('Benchmarking memory @%s from all CPUs'
                     ' for %d seconds (%d forked processes)\n'
                     % (block_size, max_time, cpu_count))
    sysbench_cmd = '('
    for _ in range(cpu_count):
        _cmd = ('sysbench --max-time=%d --max-requests=100000000 '
                '--num-threads=1 --test=memory --memory-block-size=%s run &')
        sysbench_cmd += _cmd % (max_time, block_size)

    sysbench_cmd.rstrip('&')
    sysbench_cmd += ')'

    global_perf = 0
    process = subprocess.Popen(
        sysbench_cmd, shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
        line = line.decode()
        if "transferred" in line:
            _, right = line.rstrip('\n').replace(' ', '').split('(')
            perf, _ = right.split('.')
            global_perf += int(perf)

    hw_lst.append(('cpu', 'logical', 'forked_bandwidth_%s' %
                   (block_size), str(global_perf)))


def mem_perf(hw_lst, max_time=5):
    """Report the memory performance."""
    all_cpu_testing_time = 5
    block_size_list = ['1K', '4K', '1M', '16M', '128M', '1G', '2G']
    logical = utils.get_value(hw_lst, 'cpu', 'logical', 'number')
    physical = utils.get_value(hw_lst, 'cpu', 'physical', 'number')
    if physical:
        eta = int(physical) * len(block_size_list) * max_time
        eta += 2 * (all_cpu_testing_time * len(block_size_list))
        sys.stderr.write('Memory Performance: %d logical CPU'
                         ' to test (ETA: %d seconds)\n'
                         % (int(physical), int(eta)))
        for cpu_nb in utils.get_one_cpu_per_socket(hw_lst):
            for block_size in block_size_list:
                run_sysbench_memory_threaded(hw_lst, max_time,
                                             block_size, 1, cpu_nb)

        # There is not need to test fork vs thread
        #  if only a single logical cpu is present
        if int(logical) > 1:
            for block_size in block_size_list:
                run_sysbench_memory_threaded(hw_lst, all_cpu_testing_time,
                                             block_size, int(logical))

            for block_size in block_size_list:
                run_sysbench_memory_forked(hw_lst, all_cpu_testing_time,
                                           block_size, int(logical))
