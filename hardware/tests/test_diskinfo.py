# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
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

import sys
import unittest
from unittest import mock

from hardware import diskinfo

if sys.version_info.major == 3:
    builtin_module_name = 'builtins'
    long = int
else:
    builtin_module_name = '__builtin__'


class TestDiskinfo(unittest.TestCase):

    def test_sizeingb(self):
        return self.assertEqual(diskinfo.sizeingb(977105060), 500)

    def test_parse_hdparm_output(self):
        return self.assertEqual(
            diskinfo.parse_hdparm_output(
                '\n/dev/sda:\n Timing buffered disk reads: 1436 MB '
                'in  3.00 seconds = 478.22 MB/sec'),
            478.22)

    def test_parse_hdparm_output2(self):
        return self.assertEqual(
            diskinfo.parse_hdparm_output(
                '\n/dev/sdc:\n Timing buffered disk reads:  30 MB '
                'in  3.01 seconds =   9.97 MB/sec\n'),
            9.97)

    @mock.patch('{}.open'.format(builtin_module_name), create=True)
    @mock.patch('os.path.exists', return_value=True)
    def test_get_disk_info(self, mock_os_path_exists, mock_open):
        fake_disk_values = ['Cyberdyne Systems', 'T1000', '0x00', '0',
                            '512', '0', '1023', '[none]']
        mock_open.side_effect = [
            mock.mock_open(read_data=fake_value).return_value
            for fake_value in fake_disk_values]
        hw = []
        sizes = {'fake': 100}
        diskinfo.get_disk_info('fake', sizes, hw)
        self.assertEqual(hw, [('disk', 'fake', 'size', '100'),
                              ('disk', 'fake', 'vendor', 'Cyberdyne Systems'),
                              ('disk', 'fake', 'model', 'T1000'),
                              ('disk', 'fake', 'rev', '0x00'),
                              ('disk', 'fake', 'optimal_io_size', '0'),
                              ('disk', 'fake', 'physical_block_size', '512'),
                              ('disk', 'fake', 'rotational', '0'),
                              ('disk', 'fake', 'nr_requests', '1023'),
                              ('disk', 'fake', 'scheduler', 'none')])


if __name__ == "__main__":
    unittest.main()
