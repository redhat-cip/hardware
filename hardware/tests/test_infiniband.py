# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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
from unittest import mock

import hardware.infiniband


@mock.patch.object(hardware.infiniband, 'cmd')
class TestInfiniband(unittest.TestCase):

    def test_ib_card_drv(self, cmd_mock):
        cmd_mock.return_value = (0, IBSTAT_L)
        self.assertEqual(hardware.infiniband.ib_card_drv(), [IBSTAT_L])

    def test_ib_global_info(self, cmd_mock):
        cmd_mock.return_value = (0, IBSTAT_CARD_S)
        self.assertEqual(hardware.infiniband.ib_global_info('mlx4_0'),
                         {'node_guid': '0x0002c9030056b9e6',
                          'sys_guid': '0x0002c9030056b9e9',
                          'fw_ver': '2.9.1000',
                          'device_type': 'MT26428',
                          'hw_ver': 'b0',
                          'nb_ports': '2'})

    def test_ib_port_info(self, cmd_mock):
        cmd_mock.return_value = (0, IBSTAT_CARD_PORT)
        self.assertEqual(hardware.infiniband.ib_port_info('mlx4_0', 2),
                         {'base_lid': '0',
                          'lmc': '0',
                          'physical_state': 'Down',
                          'port_guid': '0x0002c903005a7b7e',
                          'rate': '10',
                          'sm_lid': '0',
                          'state': 'Down'})


if __name__ == "__main__":
    unittest.main()

IBSTAT_L = 'mlx4_0'
IBSTAT_CARD_S = '''CA 'mlx4_0'
 CA type: MT26428
 Number of ports: 2
 Firmware version: 2.9.1000
 Hardware version: b0
 Node GUID: 0x0002c9030056b9e6
 System image GUID: 0x0002c9030056b9e9
'''

IBSTAT_CARD_PORT = '''CA: 'mlx4_0'
Port 2:
State: Down
Physical state: Polling
Rate: 10
Base lid: 0
LMC: 0
SM lid: 0
Capability mask: 0x02510868
Port GUID: 0x0002c903005a7b7e
'''

# test_infiniband.py ends here
