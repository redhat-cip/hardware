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

import unittest

from hardware import cmdb


class TestCmdb(unittest.TestCase):

    def test_update_cmdb_simple(self):
        data = [{'b': 1}]
        var = {'a': 1}
        result = cmdb.update_cmdb(data, var, var, False)
        self.assertTrue(result, cmdb)
        self.assertEqual(data, [{'a': 1, 'b': 1, 'used': 1}])
        self.assertEqual(var, {'a': 1, 'b': 1, 'used': 1})

    def test_update_cmdb_reuse(self):
        data = [{'a': 1, 'used': 1}]
        var = {'a': 1}
        result = cmdb.update_cmdb(data, var, var, False)
        self.assertTrue(result, cmdb)
        self.assertEqual(data, [{'a': 1, 'used': 1}])
        self.assertEqual(var, {'a': 1, 'used': 1})

    def test_update_cmdb_reuse2(self):
        data = [{'a': 1, 'b': 1, 'c': 1, 'used': 1}]
        cmdb_result = [{'a': 1, 'b': 2, 'c': 1, 'used': 1}]
        var = {'a': 1, 'b': 2}
        pref = {'a': 1}
        result = cmdb.update_cmdb(data, var, pref, False)
        self.assertTrue(result, cmdb_result)
        self.assertEqual(data, cmdb_result)
        self.assertEqual(var, {'a': 1, 'b': 2, 'c': 1, 'used': 1})

    def test_update_cmdb_full(self):
        data = [{'a': 2, 'used': 1}]
        var = {'a': 1}
        self.assertRaises(cmdb.CmdbError, cmdb.update_cmdb,
                          data, var, var, False)

    def test_update_cmdb_full2(self):
        data = [{'a': 'ff:ff'}]
        var = {'a': 'FF:FF'}
        self.assertRaises(cmdb.CmdbError, cmdb.update_cmdb,
                          data, var, var, True)


if __name__ == "__main__":
    unittest.main()

# test_cmdb.py ends here
