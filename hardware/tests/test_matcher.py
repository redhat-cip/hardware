# Copyright (C) 2013-2015 eNovance SAS <licensing@enovance.com>
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

from hardware import matcher


class TestMatcher(unittest.TestCase):

    def test_equal(self):
        lines = [('system', 'product', 'serial', 'CZJ31402CD')]
        spec = ('system', 'product', 'serial', 'CZJ31402CD')
        arr = {}
        self.assertTrue(matcher.match_spec(spec, lines, arr))

    def test_not_equal(self):
        lines = [('system', 'product', 'serial', 'CZJ31402CD')]
        spec = ('system', 'product', 'serial', 'CZJ31402CE')
        arr = {}
        self.assertFalse(matcher.match_spec(spec, lines, arr))

    def test_var(self):
        lines = [('disk', '1I:1:1', 'size', '1000GB')]
        spec = ('disk', '$disk8', 'size', '1000GB')
        arr = {}
        self.assertTrue(matcher.match_spec(spec, lines, arr))
        self.assertEqual(arr, {'disk8': '1I:1:1'})

    def test_vars(self):
        lines = [
            ('system', 'product', 'serial', 'CZJ31402CD'),
            ('disk', '1I:1:1', 'size', '1000GB'),
            ('disk', '1I:1:1', 'type', 'SATA'),
            ('disk', '1I:1:1', 'control', 'hpa'),
            ('disk', '1I:1:2', 'size', '1000GB'),
            ('disk', '1I:1:2', 'type', 'SATA'),
            ('disk', '1I:1:2', 'control', 'hpa'),
            ('disk', '1I:1:3', 'size', '1000GB'),
            ('disk', '1I:1:3', 'type', 'SATA'),
            ('disk', '1I:1:3', 'control', 'hpa'),
            ('disk', '1I:1:4', 'size', '1000GB'),
            ('disk', '1I:1:4', 'type', 'SATA'),
            ('disk', '1I:1:4', 'control', 'hpa'),
            ('disk', '2I:1:5', 'size', '1000GB'),
            ('disk', '2I:1:5', 'type', 'SATA'),
            ('disk', '2I:1:5', 'control', 'hpa'),
            ('disk', '2I:1:6', 'size', '1000GB'),
            ('disk', '2I:1:6', 'type', 'SATA'),
            ('disk', '2I:1:6', 'control', 'hpa'),
            ('disk', '2I:1:7', 'size', '100GB'),
            ('disk', '2I:1:7', 'type', 'SSDSATA'),
            ('disk', '2I:1:7', 'control', 'hpa'),
            ('disk', '2I:1:8', 'size', '100GB'),
            ('disk', '2I:1:8', 'type', 'SSDSATA'),
            ('disk', '2I:1:8', 'control', 'hpa'),
        ]
        specs = [('system', 'product', 'serial', 'CZJ31402CD'),
                 ('disk', '$disk1', 'size', '100GB'),
                 ('disk', '$disk2', 'size', '100GB'),
                 ('disk', '$disk3', 'size', '1000GB'),
                 ('disk', '$disk4', 'size', '1000GB'),
                 ('disk', '$disk5', 'size', '1000GB'),
                 ('disk', '$disk6', 'size', '1000GB'),
                 ('disk', '$disk7', 'size', '1000GB'),
                 ('disk', '$disk8', 'size', '1000GB')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr,
                         {'disk1': '2I:1:7',
                          'disk2': '2I:1:8',
                          'disk3': '1I:1:1',
                          'disk4': '1I:1:2',
                          'disk5': '1I:1:3',
                          'disk6': '1I:1:4',
                          'disk7': '2I:1:5',
                          'disk8': '2I:1:6',
                          }
                         )

    def test_already_bound(self):
        lines = [
            ('disk', '1I:1:2', 'size', '100GB'),
            ('disk', '1I:1:1', 'size', '1000GB'),
            ('disk', '1I:1:1', 'control', 'hpa'),
            ('disk', '1I:1:2', 'control', 'hpa'),
        ]
        specs = [
            ('disk', '$disk1', 'size', '100GB'),
            ('disk', '$disk1', 'control', 'hpa'),
            ('disk', '$disk2', 'size', '1000GB'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr,
                         {'disk1': '1I:1:2',
                          'disk2': '1I:1:1',
                          })

    def test_order(self):
        specs = [
            ('disk', '$disk1', 'size', '100'),
            ('disk', '$disk1', 'slot', '$slot1'),
            ('disk', '$disk2', 'size', '1000'),
            ('disk', '$disk2', 'slot', '$slot2'),
        ]
        lines = [
            ('disk', '1I:1:1', 'size', '1000'),
            ('disk', '1I:1:1', 'control', 'hpa'),
            ('disk', '1I:1:1', 'slot', '2'),
            ('disk', '2I:1:8', 'size', '100'),
            ('disk', '2I:1:8', 'control', 'hpa'),
            ('disk', '2I:1:8', 'slot', '2'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))

    def test_2vars(self):
        specs = [
            ('disk', '$disk', 'size', '$size'),
        ]
        lines = [
            ('disk', 'vda', 'size', '8'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr,
                         {'size': '8',
                          'disk': 'vda',
                          })

    def test_2dollars(self):
        specs = [
            ('disk', '$$disk', 'size', '$size'),
        ]
        lines = [
            ('disk', 'vda', 'size', '8'),
        ]
        arr = {}
        arr2 = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, arr2))
        self.assertEqual(arr,
                         {'size': '8',
                          'disk': 'vda',
                          })
        self.assertEqual(arr2,
                         {'disk': 'vda',
                          })

    def test_multiple_vars(self):
        specs = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vdb', 'size', '16'),
        ]
        specs2 = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vdb', 'size', '8'),
        ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vdb', 'size', '8'),
        ]
        arr = {}
        self.assertFalse(matcher.match_all(lines, specs, arr, {}))
        self.assertTrue(matcher.match_all(lines, specs2, arr, {}), lines)

    def test_multiple(self):
        spec = ('disk', '$disk', 'size', '8')
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vdb', 'size', '8'),
        ]
        arr = {}
        self.assertTrue(matcher.match_multiple(lines, spec, arr))
        self.assertEqual(arr['disk'], ['vda', 'vdb'])

    def test_gt(self):
        specs = [('disk', '$disk', 'size', 'gt(10)')]
        lines = [
            ('disk', 'vda', 'size', '20'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_ge(self):
        specs = [('disk', '$disk', 'size', 'ge(10.1)')]
        lines = [
            ('disk', 'vda', 'size', '10.5'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_lt(self):
        specs = [('disk', '$disk', 'size', 'lt(30)')]
        lines = [
            ('disk', 'vda', 'size', '20'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_le(self):
        specs = [('disk', '$disk', 'size', 'le(20)')]
        lines = [
            ('disk', 'vda', 'size', '20'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_not(self):
        specs = [('network', '$eth', 'serial', '$mac=not(regexp(^28:d2:))')]
        lines = [('network', 'eth0', 'serial', '20:d2:44:1b:0a:8b')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['eth'], 'eth0')
        self.assertEqual(arr['mac'], '20:d2:44:1b:0a:8b')

    def test_and(self):
        specs = [('disk', '$disk', 'size', 'and(gt(20), lt(50))')]
        lines = [('disk', 'vda', 'size', '40')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_or(self):
        specs = [('disk', '$disk', 'size', 'or(lt(20), gt(30))')]
        lines = [('disk', 'vda', 'size', '40')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_network(self):
        specs = [('network', '$eth', 'ipv4', u'network(192.168.2.0/24)')]
        lines = [('network', 'eth0', 'ipv4', u'192.168.2.2')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['eth'], 'eth0')

    def test_le_var(self):
        specs = [('disk', '$disk', 'size', '$size=le(20)')]
        lines = [('disk', 'vda', 'size', '20')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')
        self.assertEqual(arr['size'], '20')

    def test_in(self):
        specs = [('disk', '$disk', 'size', 'in(10, 20, 30)')]
        lines = [('disk', 'vda', 'size', '20')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_in2(self):
        specs = [('disk', '$disk=in("vda", "vdb")', 'size', '20')]
        lines = [('disk', 'vda', 'size', '20')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_rangeint(self):
        specs = [('disk', '$disk', 'size', 'range(20, 25)')]
        lines = [('disk', 'vda', 'size', '20')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vda')

    def test_rangefloat(self):
        specs = [('ipmi', '+12V', 'value', 'range(11.9, 12.2)')]
        lines = [('ipmi', '+12V', 'value', '12.14')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))

    def test_regexp(self):
        specs = [('network', '$eth', 'serial', 'regexp(^28:d2:)')]
        lines = [('network', 'eth0', 'serial', '28:d2:44:1b:0a:8b')]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))

    def test_backtrack(self):
        specs = [
            ('disk', '$disk', 'size', '8'),
            ('disk', '$disk', 'type', 'b'),
        ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vda', 'type', 'a'),
            ('disk', 'vdb', 'size', '8'),
            ('disk', 'vdb', 'type', 'b'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk'], 'vdb', arr)

    def test_backtrack2(self):
        specs = [
            ('disk', '$disk', 'size', '8'),
            ('disk', '$disk', 'type', 'b'),
            ('disk', '$disk2', 'size', '8'),
        ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vda', 'type', 'a'),
            ('disk', 'vdb', 'size', '8'),
            ('disk', 'vdb', 'type', 'b'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(lines, specs, arr, {}))
        self.assertEqual(arr['disk2'], 'vda', arr)
        self.assertEqual(arr['disk'], 'vdb', arr)

    def test_backtrack3(self):
        specs = [
            ('disk', '$disk', 'size', '8'),
            ('disk', '$disk', 'type', 'c'),
            ('disk', '$disk2', 'size', '8'),
        ]
        lines = [
            ('disk', 'vda', 'size', '8'),
            ('disk', 'vda', 'type', 'a'),
            ('disk', 'vdb', 'size', '8'),
            ('disk', 'vdb', 'type', 'b'),
        ]
        arr = {}
        self.assertFalse(matcher.match_all(lines, specs, arr, {}))

    def test_backtracklong(self):
        specs = [
            ('disk', 'logical', 'count', '8'),
            ('disk', '$disk1', 'size', '1000'),
            ('disk', '$disk1', 'vendor', 'Hitachi'),
            ('disk', '$disk1', 'model', 'HUA722010CLA330'),
            ('disk', '$disk1', 'rev', 'R001'),
            ('disk', '$disk1', 'optimal_io_size', '0'),
            ('disk', '$disk1', 'physical_block_size', '512'),
            ('disk', '$disk1', 'rotational', '1'),
            ('disk', '$disk1', 'Write Cache Enable', '1'),
            ('disk', '$disk1', 'Read Cache Disable', '0'),
            ('disk', '$disk2', 'size', '1000'),
            ('disk', '$disk2', 'vendor', 'Seagate'),
            ('disk', '$disk2', 'model', 'ST31000528AS'),
            ('disk', '$disk2', 'rev', 'R001'),
            ('disk', '$disk2', 'optimal_io_size', '0'),
            ('disk', '$disk2', 'physical_block_size', '512'),
            ('disk', '$disk2', 'rotational', '1'),
            ('disk', '$disk2', 'Write Cache Enable', '1'),
            ('disk', '$disk2', 'Read Cache Disable', '0'),
            ('disk', '$disk3', 'size', '1000'),
            ('disk', '$disk3', 'optimal_io_size', '0'),
            ('disk', '$disk3', 'physical_block_size', '512'),
            ('disk', '$disk3', 'rotational', '1'),
            ('disk', '$disk3', 'Write Cache Enable', '1'),
            ('disk', '$disk3', 'Read Cache Disable', '0'),
            ('disk', '$disk4', 'size', '1000'),
            ('disk', '$disk4', 'optimal_io_size', '0'),
            ('disk', '$disk4', 'physical_block_size', '512'),
            ('disk', '$disk4', 'rotational', '1'),
            ('disk', '$disk4', 'Write Cache Enable', '1'),
            ('disk', '$disk4', 'Read Cache Disable', '0'),
            ('disk', '$disk5', 'size', '1000'),
            ('disk', '$disk5', 'optimal_io_size', '0'),
            ('disk', '$disk5', 'physical_block_size', '512'),
            ('disk', '$disk5', 'rotational', '1'),
            ('disk', '$disk5', 'Write Cache Enable', '1'),
            ('disk', '$disk5', 'Read Cache Disable', '0'),
            ('disk', '$disk6', 'size', '1000'),
            ('disk', '$disk6', 'optimal_io_size', '0'),
            ('disk', '$disk6', 'physical_block_size', '512'),
            ('disk', '$disk6', 'rotational', '1'),
            ('disk', '$disk6', 'Write Cache Enable', '1'),
            ('disk', '$disk6', 'Read Cache Disable', '0'),
            ('disk', '$disk7', 'size', '1000'),
            ('disk', '$disk7', 'optimal_io_size', '0'),
            ('disk', '$disk7', 'physical_block_size', '512'),
            ('disk', '$disk7', 'rotational', '1'),
            ('disk', '$disk7', 'Write Cache Enable', '1'),
            ('disk', '$disk7', 'Read Cache Disable', '0'),
            ('disk', '$disk8', 'size', '1000'),
            ('disk', '$disk8', 'optimal_io_size', '0'),
            ('disk', '$disk8', 'physical_block_size', '512'),
            ('disk', '$disk8', 'rotational', '1'),
            ('disk', '$disk8', 'Write Cache Enable', '1'),
            ('disk', '$disk8', 'Read Cache Disable', '0'),
        ]
        arr = {}
        self.assertTrue(matcher.match_all(X8_HW, specs, arr, {}))

    def test_generate_filename_and_macs(self):
        items = [('system', 'product', 'serial', 'Sysname'),
                 ('network', 'eth0', 'serial', 'mac')]
        self.assertEqual(matcher.generate_filename_and_macs(items),
                         {'sysname': 'Sysname-mac',
                          'sysserial': 'Sysname',
                          'eth': ['eth0'],
                          'serial': ['mac'],
                          })

    def test_generate_filename_and_macs_no_sysname(self):
        items = [('network', 'eth0', 'serial', 'aa:bb:cc')]
        self.assertEqual(matcher.generate_filename_and_macs(items),
                         {'serial': ['aa:bb:cc'],
                          'eth': ['eth0'],
                          'sysname': 'aa-bb-cc',
                          })

    def test_generate_filename_and_macs_virtualbox(self):
        items = [('disk', 'sda', 'size', '8'),
                 ('system', 'product', 'serial', '0'),
                 ('system', 'product', 'name', 'VirtualBox ()'),
                 ('system', 'product', 'vendor', 'innotek GmbH'),
                 ('system', 'product', 'version', '1.2'),
                 ('system', 'memory', 'size', '521113600'),
                 ('network', 'eth0', 'serial', '08:00:27:6f:77:22'),
                 ('network', 'eth0', 'vendor', 'Intel Corporation'),
                 ('network', 'eth0', 'product',
                  '82540EM Gigabit Ethernet Controller'),
                 ('network', 'eth0', 'size', '1000000000'),
                 ('network', 'eth0', 'ipv4', '10.0.2.15'),
                 ('network', 'eth0', 'link', 'yes'),
                 ('network', 'eth0', 'driver', 'e1000'),
                 ('system', 'cpu', 'number', '1')]
        result = matcher.generate_filename_and_macs(items)
        self.assertEqual(result['sysname'], 'VirtualBox-0-08-00-27-6f-77-22')
        self.assertEqual(result['serial'], ['08:00:27:6f:77:22'])
        self.assertEqual(result['eth'], ['eth0'])


if __name__ == "__main__":
    unittest.main()

X8_HW = [('disk', 'logical', 'count', '8'),
         ('disk', 'sdd', 'size', '1000'),
         ('disk', 'sdd', 'model', 'HUA722010CLA330'),
         ('disk', 'sdd', 'vendor', 'Hitachi'),
         ('disk', 'sdd', 'rev', 'R001'),
         ('disk', 'sdd', 'optimal_io_size', '0'),
         ('disk', 'sdd', 'physical_block_size', '512'),
         ('disk', 'sdd', 'rotational', '1'),
         ('disk', 'sdd', 'Write Cache Enable', '1'),
         ('disk', 'sdd', 'Read Cache Disable', '0'),
         ('disk', 'sdd', 'scsi-id', 'scsi-2001b4d2001775100'),
         ('disk', 'sde', 'size', '1000'),
         ('disk', 'sde', 'vendor', 'Hitachi'),
         ('disk', 'sde', 'model', 'HUA722010CLA330'),
         ('disk', 'sde', 'rev', 'R001'),
         ('disk', 'sde', 'optimal_io_size', '0'),
         ('disk', 'sde', 'physical_block_size', '512'),
         ('disk', 'sde', 'rotational', '1'),
         ('disk', 'sde', 'Write Cache Enable', '1'),
         ('disk', 'sde', 'Read Cache Disable', '0'),
         ('disk', 'sde', 'scsi-id', 'scsi-2001b4d2001655500'),
         ('disk', 'sdf', 'size', '1000'),
         ('disk', 'sdf', 'vendor', 'Hitachi'),
         ('disk', 'sdf', 'model', 'HDS721010CLA330'),
         ('disk', 'sdf', 'rev', 'R001'),
         ('disk', 'sdf', 'optimal_io_size', '0'),
         ('disk', 'sdf', 'physical_block_size', '512'),
         ('disk', 'sdf', 'rotational', '1'),
         ('disk', 'sdf', 'Write Cache Enable', '1'),
         ('disk', 'sdf', 'Read Cache Disable', '0'),
         ('disk', 'sdf', 'scsi-id', 'scsi-2001b4d2012776300'),
         ('disk', 'sdg', 'size', '1000'),
         ('disk', 'sdg', 'vendor', 'Seagate'),
         ('disk', 'sdg', 'model', 'ST31000528AS'),
         ('disk', 'sdg', 'rev', 'R001'),
         ('disk', 'sdg', 'optimal_io_size', '0'),
         ('disk', 'sdg', 'physical_block_size', '512'),
         ('disk', 'sdg', 'rotational', '1'),
         ('disk', 'sdg', 'Write Cache Enable', '1'),
         ('disk', 'sdg', 'Read Cache Disable', '0'),
         ('disk', 'sda', 'size', '1000'),
         ('disk', 'sda', 'vendor', 'Seagate'),
         ('disk', 'sda', 'model', 'ST31000528AS'),
         ('disk', 'sda', 'rev', 'R001'),
         ('disk', 'sda', 'optimal_io_size', '0'),
         ('disk', 'sda', 'physical_block_size', '512'),
         ('disk', 'sda', 'rotational', '1'),
         ('disk', 'sda', 'Write Cache Enable', '1'),
         ('disk', 'sda', 'Read Cache Disable', '0'),
         ('disk', 'sdb', 'size', '1000'),
         ('disk', 'sdb', 'vendor', 'Seagate'),
         ('disk', 'sdb', 'model', 'ST31000528AS'),
         ('disk', 'sdb', 'rev', 'R001'),
         ('disk', 'sdb', 'optimal_io_size', '0'),
         ('disk', 'sdb', 'physical_block_size', '512'),
         ('disk', 'sdb', 'rotational', '1'),
         ('disk', 'sdb', 'Write Cache Enable', '1'),
         ('disk', 'sdb', 'Read Cache Disable', '0'),
         ('disk', 'sdb', 'scsi-id', 'scsi-2001b4d2000000000'),
         ('disk', 'sdc', 'size', '1000'),
         ('disk', 'sdc', 'vendor', 'Seagate'),
         ('disk', 'sdc', 'model', 'ST31000528AS'),
         ('disk', 'sdc', 'rev', 'R001'),
         ('disk', 'sdc', 'optimal_io_size', '0'),
         ('disk', 'sdc', 'physical_block_size', '512'),
         ('disk', 'sdc', 'rotational', '1'),
         ('disk', 'sdc', 'Write Cache Enable', '1'),
         ('disk', 'sdc', 'Read Cache Disable', '0'),
         ('disk', 'sdh', 'size', '1000'),
         ('disk', 'sdh', 'vendor', 'Hitachi'),
         ('disk', 'sdh', 'model', 'HDS721010CLA330'),
         ('disk', 'sdh', 'rev', 'R001'),
         ('disk', 'sdh', 'optimal_io_size', '0'),
         ('disk', 'sdh', 'physical_block_size', '512'),
         ('disk', 'sdh', 'rotational', '1'),
         ('disk', 'sdh', 'Write Cache Enable', '1'),
         ('disk', 'sdh', 'Read Cache Disable', '0'),
         ('disk', 'sdh', 'scsi-id', 'scsi-2001b4d2012486900')]
