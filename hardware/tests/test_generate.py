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

from hardware import generate


class TestGenerate(unittest.TestCase):

    def test_is_included_same(self):
        a = {'a': 1}
        self.assertTrue(generate.is_included(a, a))

    def test_is_included_different(self):
        a = {'a': 1}
        b = {'a': 2}
        self.assertTrue(not generate.is_included(a, b))

    def test_is_included_more(self):
        a = {'a': 1, 'b': 2}
        b = {'a': 1, 'b': 2, 'c': 3}
        self.assertTrue(generate.is_included(a, b))

    def test_generate_ips(self):
        model = '192.168.1.10-12'
        self.assertEqual(list(generate._generate_values(model)),
                         ['192.168.1.10',
                          '192.168.1.11',
                          '192.168.1.12'])

    def test_generate_names(self):
        model = 'host10-12'
        self.assertEqual(list(generate._generate_values(model)),
                         ['host10', 'host11', 'host12'])

    def test_generate_nothing(self):
        model = 'host'
        result = generate._generate_values(model)
        self.assertEqual(result.next(),
                         'host')

    def test_generate_range(self):
        self.assertEqual(list(generate._generate_range('10-12')),
                         ['10', '11', '12'])

    def test_generate_range_zero(self):
        self.assertEqual(list(generate._generate_range('001-003')),
                         ['001', '002', '003'])

    def test_generate_range_colon(self):
        self.assertEqual(list(generate._generate_range('1-3:10-12')),
                         ['1', '2', '3', '10', '11', '12'])

    def test_generate_range_colon_reverse(self):
        self.assertEqual(list(generate._generate_range('100-100:94-90')),
                         ['100', '94', '93', '92', '91', '90'])

    def test_generate_range_invalid(self):
        self.assertEqual(list(generate._generate_range('D7-H.1.0.0')),
                         ['D7-H.1.0.0'])

    def test_generate(self):
        model = {'gw': '192.168.1.1',
                 'ip': '192.168.1.10-12',
                 'hostname': 'host10-12'}
        self.assertEqual(
            generate.generate(model),
            [{'gw': '192.168.1.1', 'ip': '192.168.1.10', 'hostname': 'host10'},
             {'gw': '192.168.1.1', 'ip': '192.168.1.11', 'hostname': 'host11'},
             {'gw': '192.168.1.1', 'ip': '192.168.1.12', 'hostname': 'host12'}]
            )

    def test_generate_with_zeros(self):
        model = {'gw': '192.168.1.1',
                 'ip': '192.168.1.1-6',
                 'hostname': 'ceph001-006'}
        self.assertEqual(
            generate.generate(model),
            [{'gw': '192.168.1.1', 'ip': '192.168.1.1', 'hostname': 'ceph001'},
             {'gw': '192.168.1.1', 'ip': '192.168.1.2', 'hostname': 'ceph002'},
             {'gw': '192.168.1.1', 'ip': '192.168.1.3', 'hostname': 'ceph003'},
             {'gw': '192.168.1.1', 'ip': '192.168.1.4', 'hostname': 'ceph004'},
             {'gw': '192.168.1.1', 'ip': '192.168.1.5', 'hostname': 'ceph005'},
             {'gw': '192.168.1.1', 'ip': '192.168.1.6', 'hostname': 'ceph006'},
             ]
            )

    def test_generate_253(self):
        result = generate.generate({'hostname': '10.0.1-2.2-254'})
        self.assertEqual(
            len(result),
            2 * 253,
            result)

    def test_generate_invalid(self):
        result = generate.generate({'hostname': '10.0.1-2.2-254',
                                    'version': 'D7-H.1.0.0'})
        self.assertEqual(
            len(result),
            2 * 253,
            result)

    def test_generate_list(self):
        result = generate.generate({'hostname': ('hosta', 'hostb', 'hostc')})
        self.assertEqual(
            result,
            [{'hostname': 'hosta'},
             {'hostname': 'hostb'},
             {'hostname': 'hostc'}]
            )

    def test_generate_none(self):
        model = {'gateway': '10.66.6.1',
                 'ip': '10.66.6.100',
                 'netmask': '255.255.255.0',
                 'gateway-ipmi': '10.66.6.1',
                 'ip-ipmi': '10.66.6.110',
                 'netmask-ipmi': '255.255.255.0',
                 'hostname': 'hp-grid'
                 }
        result = generate.generate(model)
        self.assertEqual(result, [model])

if __name__ == "__main__":
    unittest.main()

# test_generate.py ends here
