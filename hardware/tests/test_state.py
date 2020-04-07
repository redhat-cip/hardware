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

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from hardware import state


class TestState(unittest.TestCase):

    def test_failed_profile(self):
        obj = state.State(data=[('hw', 2)])
        self.assertTrue(obj.failed_profile('hw'))
        self.assertEqual(obj['hw'], 3)

    def test_failed_profile_times(self):
        obj = state.State(data=[('hw', '*')])
        self.assertFalse(obj.failed_profile('hw'))

    def test_getitem_not_found(self):
        obj = state.State(data=[])
        self.assertRaises(KeyError, obj.__getitem__, 'toto')

    def test_find_match_empty(self):
        obj = state.State(data=[], cfg_dir='/tmp')
        self.assertRaises(state.StateError, obj.find_match, [])

    def test_find_match(self):
        obj = state.State(data=[('hw', 2)], cfg_dir='/nowhere')
        items = [('a', 'b', 'c', 'd')]
        obj._load_specs = lambda x: items
        self.assertEqual(obj.find_match(items), ('hw', {}))

    def test_lock(self):
        tmpdir = tempfile.mkdtemp()
        obj = state.State(data=[], cfg_dir=tmpdir)
        obj.lock()
        self.assertTrue(os.path.exists(obj._lockname), obj._lockname)
        obj.unlock()
        shutil.rmtree(tmpdir)

    @patch('hardware.cmdb.load_cmdb',
           return_value=[{'hostname': 'node1',
                          'm': 'dd:ee:ff'}])
    @patch('hardware.state.State._load_specs',
           return_value=[('disk', '$disk1', 'size', '20'),
                         ('disk', '$disk2', 'size', 'gt(20)'),
                         ('disk', '$disk3', 'size', 'ge(20)'),
                         ('disk', '$disk4', 'size', 'lt(20)'),
                         ('disk', '$disk5', 'size', 'le(20)'),
                         ('network', '$eth', 'serial', '$$m'),
                         ('network', '$eth2', 'serial', 'aa:bb:cc'),
                         ('network', '$eth3', 'serial', '$$m2'),
                         ('network', '$eth4', 'link', 'yes'),
                         ('memory', 'total', 'size', '8388608'),
                         ('cpu', 'logical', 'number', '4')])
    def test_hardware_info(self, *args):
        obj = state.State(data=[('hw1', '*')])
        data = obj.hardware_info('node1')
        self.assertEqual(data, {'disks': [{'size': '20Gi'},
                                          {'size': '21Gi'},
                                          {'size': '20Gi'},
                                          {'size': '19Gi'},
                                          {'size': '20Gi'}],
                                'nics': [{'mac': 'dd:ee:ff'},
                                         {'mac': 'aa:bb:cc'}],
                                'memory': 8192,
                                'ncpus': 4})

    @patch('hardware.cmdb.load_cmdb',
           return_value=[{'hostname': 'node1'}])
    @patch('hardware.state.State._load_specs',
           return_value=[])
    def test_hardware_info_empty(self, *args):
        obj = state.State(data=[('hw1', '*')])
        data = obj.hardware_info('node1')
        self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()

# test_state.py ends here
