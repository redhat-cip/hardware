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

    def test_load_cmdb_valid_file(self):
        """Test loading a valid CMDB file with safe parsing."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create a valid CMDB file
            valid_data = [{'hostname': 'test1', 'mac': 'aa:bb:cc'},
                          {'hostname': 'test2', 'used': 1}]
            cmdb_file = os.path.join(tmpdir, 'test.cmdb')
            with open(cmdb_file, 'w') as f:
                import pprint
                pprint.pprint(valid_data, stream=f)

            result = cmdb.load_cmdb(tmpdir, 'test')
            self.assertEqual(result, valid_data)
        finally:
            shutil.rmtree(tmpdir)

    def test_load_cmdb_invalid_file_syntax(self):
        """Test that invalid Python syntax in CMDB file returns None."""
        tmpdir = tempfile.mkdtemp()
        try:
            cmdb_file = os.path.join(tmpdir, 'test.cmdb')
            # Create an invalid CMDB file with syntax errors
            with open(cmdb_file, 'w') as f:
                f.write('[{"hostname": "test1", "mac":}]')  # Missing value

            result = cmdb.load_cmdb(tmpdir, 'test')
            self.assertIsNone(result)
        finally:
            shutil.rmtree(tmpdir)

    def test_load_cmdb_malicious_file(self):
        """Test that malicious code in CMDB file cannot be executed."""
        tmpdir = tempfile.mkdtemp()
        try:
            cmdb_file = os.path.join(tmpdir, 'test.cmdb')
            # Create a CMDB file with malicious code
            malicious_code = '__import__("os").system("echo CMDB_BREACH")'
            with open(cmdb_file, 'w') as f:
                # Write malicious data that would be executed with eval()
                exploit_entry = (f'{{"hostname": "test1", '
                                 f'"exploit": {malicious_code}}}')
                f.write(f'[{exploit_entry}]')

            result = cmdb.load_cmdb(tmpdir, 'test')
            # Should return None instead of executing malicious code
            self.assertIsNone(result)
        finally:
            shutil.rmtree(tmpdir)

    def test_load_cmdb_nonexistent_file(self):
        """Test loading nonexistent CMDB file returns None."""
        result = cmdb.load_cmdb('/nonexistent/directory', 'test')
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

# test_cmdb.py ends here
