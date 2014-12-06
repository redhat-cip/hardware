#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

import unittest

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

if __name__ == "__main__":
    unittest.main()

# test_state.py ends here
