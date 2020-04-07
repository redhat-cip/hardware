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

import unittest

from hardware import megacli
from hardware.tests.utils import sample


class TestMegacliTest(unittest.TestCase):

    def setUp(self):
        def my_run(*args, **arr):
            return self.output
        self.run = megacli.run_megacli
        megacli.run_megacli = my_run

    def tearDown(self):
        megacli.run = self.run

    def test_parse_output_empty(self):
        self.assertEqual(megacli.parse_output(''), {})

    def test_parse_output_simple(self):
        self.assertEqual(megacli.parse_output(' a : b'), {'A': 'b'})

    def test_parse_output_adpcount(self):
        self.assertEqual(megacli.parse_output(sample('megacli_adpcount')),
                         {'ControllerCount': 1,
                          'ExitCode': '0x01'})

    def test_adp_count(self):
        self.output = sample('megacli_adpcount')
        self.assertEqual(megacli.adp_count(), 1)

    def test_adp_all_info(self):
        self.output = sample('megacli_adp_all_info')
        self.assertEqual(megacli.adp_all_info(0),
                         {'CriticalDisks': 0,
                          'Degraded': 0,
                          'Disks': 6,
                          'FwPackageBuild': '21.1.0-0007',
                          'FailedDisks': 0,
                          'Offline': 0,
                          'PhysicalDevices': 7,
                          'ProductName': 'PERC H710 Mini',
                          'SerialNo': '29F026R',
                          'VirtualDrives': 1})

    def test_pd_get_num(self):
        self.output = '''
 Number of Physical Drives on Adapter 0: 6'''
        self.assertEqual(megacli.pd_get_num(0), 6)

    def test_split_parts(self):
        self.assertEqual(len(megacli.split_parts(' +Enclosure [0-9]+:',
                                                 ENC_OUTPUT)),
                         2)

    def test_enc_info(self):
        self.output = '''
    Number of enclosures on adapter 0 -- 1

    Enclosure 0:
    Device ID                     : 32
    Number of Slots               : 8'''
        self.assertEqual(megacli.enc_info(0),
                         [{'Enclosure': 0,
                           'DeviceId': 32,
                           'NumberOfSlots': 8}])

    def test_enc_info2(self):
        self.output = ENC_OUTPUT
        info = megacli.enc_info(0)
        self.assertEqual(len(info), 2)
        self.assertEqual(info[0]['Enclosure'], 0)
        self.assertEqual(info[1]['Enclosure'], 1)

    def test_pdinfo(self):
        self.output = '''
Enclosure Device ID: 32
Slot Number: 5
Enclosure position: 1
Device Id: 5
WWN: 5000C50054C07E80
Sequence Number: 1
Media Error Count: 0
Other Error Count: 0
Predictive Failure Count: 0
Last Predictive Failure Event Seq Number: 0
PD Type: SAS'''
        self.assertEqual(megacli.pdinfo(0, 32, 5),
                         {'DeviceId': 5,
                          'EnclosureDeviceId': 32,
                          'EnclosurePosition': 1,
                          'LastPredictiveFailureEventSeqNumber': 0,
                          'MediaErrorCount': 0,
                          'OtherErrorCount': 0,
                          'PdType': 'SAS',
                          'PredictiveFailureCount': 0,
                          'SequenceNumber': 1,
                          'SlotNumber': 5,
                          'Wwn': '5000C50054C07E80'}
                         )

    def test_ld_get_num(self):
        self.output = '''
 Number of Virtual Drives Configured on Adapter 0: 1'''
        self.assertEqual(megacli.ld_get_num(0), 1)

    def test_ld_get_info(self):
        self.output = sample('megacli_ld_get_info')
        self.assertEqual(megacli.ld_get_info(0, 0),
                         {'Adapter0--VirtualDriveInformation': '',
                          'BadBlocksExist': 'No',
                          'CacheCadeType': 'Read Only',
                          'CanSpinUpIn1Minute': 'Yes',
                          'CurrentAccessPolicy': 'Read/Write',
                          'CurrentCachePolicy':
                          'WriteBack, ReadAdaptive, Direct, '
                          'No Write Cache if Bad BBU',
                          'CurrentPowerSavingsPolicy': 'None',
                          'DefaultAccessPolicy': 'Read/Write',
                          'DefaultCachePolicy': 'WriteBack, ReadAdaptive, '
                          'Direct, No Write Cache if Bad BBU',
                          'DefaultPowerSavingsPolicy': 'Controller Defined',
                          'DiskCachePolicy': "Disk's Default",
                          'EncryptionType': 'None',
                          'IsVdCached': 'Yes',
                          "Ld'SIoProfileSupportsMaxPowerSavings"
                          "WithCachedWrites": 'No',
                          'LdHasDrivesThatSupportT10PowerConditions': 'No',
                          'MirrorData': '465.25 GB',
                          'Name': '',
                          'NumberOfDrives': 2,
                          'RaidLevel': 'Primary-1, Secondary-0, RAID Level '
                          'Qualifier-0',
                          'SectorSize': 512,
                          'Size': '465.25 GB',
                          'SpanDepth': 1,
                          'State': 'Optimal',
                          'StripSize': '64 KB'})


ENC_OUTPUT = sample('megacli_enc')

if __name__ == "__main__":
    unittest.main()

# test_megacli.py ends here
