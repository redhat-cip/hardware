# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

'''Manage a state file file describing the hardware profiles to test
in the correct order.

A state file is a list of tuples like this:

[('hw1', 3), ('hw2', '*')]

which means try first to match hardware specs from the hw1 hardware
profile and matches only 3 times then try hw2 any number of times.
'''

import errno
import logging
import os
import pprint
import time

from hardware import cmdb
from hardware import matcher

_INVALID_SPECS = [('<unknown>', '<unknown>', '<unknown>', '<unknown>')]

LOG = logging.getLogger('hardware.state')


class StateError(Exception):
    pass


class State(object):

    def __init__(self, data=None, cfg_dir=None, filename=None, lockname=None):
        self._data = data
        self._state_filename = filename
        self._cfg_dir = cfg_dir
        self._lockname = lockname
        self._lock_fd = None

    def load(self, cfg_dir):
        'Load a state file from the given directory'
        self._cfg_dir = cfg_dir
        self._state_filename = os.path.join(cfg_dir, 'state')
        self._validate_lockname()
        self.lock()
        LOG.info('Reading state from %s' % self._state_filename)
        self._data = eval(open(self._state_filename).read(-1))

    def failed_profile(self, prof):
        '''If we get a failure report, let's reincrement the counter

Returns True if the state is modified and needs to be saved.
'''
        LOG.info("Received failure for role %s" % prof)
        idx = 0
        times = '*'
        name = None
        for name, times in self._data:
            if name == prof:
                # Only consider if time in a numeric entry
                if times != '*':
                    self._data[idx] = (name, int(times) + 1)
                    return True
                return False
            idx += 1
        return False

    def save(self):
        'Save the state data'
        if self._state_filename:
            with open(self._state_filename, 'w') as state_file:
                pprint.pprint(self._data, stream=state_file)

    def __getitem__(self, key):
        'Return the value associated with a profile'
        for name, times in self._data:
            if key == name:
                return times
        raise KeyError(key)

    def _load_specs(self, name):
        if self._cfg_dir:
            fname = os.path.join(self._cfg_dir, name + '.specs')
            if os.path.exists(fname):
                return eval(open(fname, 'r').read(-1))

            LOG.info('Specs file %s not found' % fname)

        return _INVALID_SPECS

    def _validate_lockname(self):
        if not self._lockname:
            self._lockname = os.path.join(self._cfg_dir, 'lock')

    def find_match(self, hw_items):
        '''Finds an hardware profile matching the hardware items in the state

If a profiles matches, its count is decremented.

Returns the name of the matching profile.
'''
        idx = 0
        times = '*'
        name = None
        valid_roles = []
        for name, times in self._data:
            LOG.info('testing %s' % name)
            if times == '*' or int(times) > 0:
                valid_roles.append(name)
                specs = self._load_specs(name)
                var = {}
                var2 = {}
                if matcher.match_all(hw_items, specs, var, var2):
                    LOG.info('Specs %s matches' % name)

                    forced = (var2 != {})

                    if var2 == {}:
                        var2 = var

                    if times != '*':
                        self._data[idx] = (name, int(times) - 1)
                        LOG.info('Decrementing %s to %d' %
                                 (name, int(times) - 1))

                    dbase = cmdb.load_cmdb(self._cfg_dir, name)
                    if dbase:
                        if cmdb.update_cmdb(dbase, var, var2, forced):
                            cmdb.save_cmdb(self._cfg_dir, name, dbase)
                        else:
                            idx += 1
                            continue

                    return name, var
            idx += 1
        else:
            if not valid_roles:
                raise StateError('No more role available in %s' %
                                 (self._state_filename,))
            else:
                raise StateError(
                    'Unable to match requirements on the following available '
                    'roles in %s: %s'
                    % (self._cfg_dir, ', '.join(valid_roles)))

    def lock(self):
        '''Lock a file and return a file descriptor.

Need to call unlock to release the lock.
        '''
        self._validate_lockname()
        count = 0
        while True:
            try:
                self._lock_fd = os.open(self._lockname,
                                        os.O_CREAT | os.O_EXCL | os.O_RDWR)
                break
            except OSError as xcpt:
                if xcpt.errno != errno.EEXIST:
                    raise
                if count % 30 == 0:
                    LOG.debug('waiting for lock %s' % self._lockname)
                time.sleep(1)
                count += 1
        return self._lock_fd

    def unlock(self):
        'Called after the lock function to release a lock.'
        if self._lock_fd:
            os.close(self._lock_fd)
            os.unlink(self._lockname)
            self._lock_fd = None

    @staticmethod
    def _get_value(lines, spec, key):
        info = {}
        if (matcher.match_spec(spec, lines, info)
                and key in info
                and info[key][0] != '$'):
            return int(info[key])
        return None

    @staticmethod
    def _get_memory(specs):
        mem = State._get_value(specs, ('memory', 'total', 'size', '$size'),
                               'size')
        if mem:
            return mem / 1024
        return None

    @staticmethod
    def _get_ncpus(specs):
        return State._get_value(specs, ('cpu', 'logical', 'number', '$ncpus'),
                                'ncpus')

    @staticmethod
    def _get_disks(specs):
        disks = []
        info = {}
        while matcher.match_spec(('disk', '$disk', 'size', '$gb'),
                                 specs, info):
            if info['gb'].startswith("gt"):
                size = int(info['gb'][3:-1]) + 1
            elif info['gb'].startswith("ge"):
                size = int(info['gb'][3:-1])
            elif info['gb'].startswith("lt"):
                size = int(info['gb'][3:-1]) - 1
            elif info['gb'].startswith("le"):
                size = int(info['gb'][3:-1])
            else:
                size = info['gb']
            disks_size = "%sGi" % size
            disks.append({"size": disks_size})
            info = {}
        return disks

    @staticmethod
    def _get_nics(specs, dbase):
        nics = []
        info = {}
        eth_names = []
        copy = list(specs)
        # first lookup all the network interface names
        while matcher.match_spec(('network', '$eth', '$key', '$value'),
                                 copy, info):
            if info['eth'] not in eth_names:
                eth_names.append(info['eth'])
            info = {}
        # then lookup if matching by mac address is used to store the
        # mac address
        for name in eth_names:
            if matcher.match_spec(('network', name, 'serial', '$mac'),
                                  specs, info):
                if 'mac' in info:
                    if info['mac'][0:2] == '$$':
                        var = info['mac'][2:]
                        if var in dbase:
                            nics.append({"mac": dbase[var]})
                        else:
                            print('cmdb setting %s not found' % var)
                    else:
                        nics.append({"mac": info['mac']})
                info = {}
        return nics

    def hardware_info(self, hostname):
        '''Get hardware informations for a hostname.

Lookup cmdb to find the correct specs file and extract info from it.
'''
        # step 1: find the name of the profile by looking into the cmdb
        info = None
        for name, _ in self._data:
            cfgdb = cmdb.load_cmdb(self._cfg_dir, name)
            if cfgdb:
                for rec in cfgdb:
                    if 'hostname' in rec and rec['hostname'] == hostname:
                        info = rec
                        break
            if info:
                break
        else:
            return {}

        # step 2: lookup hardware info from the specs file
        specs = self._load_specs(name)
        data = {}

        mem = State._get_memory(specs)
        if mem:
            data['memory'] = mem

        ncpus = State._get_ncpus(specs)
        if ncpus:
            data['ncpus'] = ncpus

        disks = State._get_disks(specs)
        if disks:
            data['disks'] = disks

        nics = State._get_nics(specs, info)
        if nics:
            data['nics'] = nics

        return data
