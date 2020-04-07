# Copyright (C) 2013-2014 eNovance SAS <licensing@enovance.com>
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

import pexpect

from hardware import hpacucli
from hardware.tests.utils import sample


class TestParsing(unittest.TestCase):

    def test_parse_ctrl_all_show(self):
        # => ctrl all show
        return self.assertEqual(
            hpacucli.parse_ctrl_all_show(CTRL_ALL_SHOW_OUTPUT),
            CTRL_ALL_SHOW_RESULT)

    def test_parse_ctrl_all_show_hpssacli(self):
        # => ctrl all show
        return self.assertEqual(
            hpacucli.parse_ctrl_all_show(CTRL_ALL_SHOW_OUTPUT_HPSSAPI),
            CTRL_ALL_SHOW_RESULT_HPSSAPI)

    def test_parse_ctrl_pd_all_show(self):
        # => ctrl slot=2 pd all show
        return self.assertEqual(
            hpacucli.parse_ctrl_pd_all_show(CTRL_PD_ALL_SHOW_OUTPUT),
            CTRL_PD_ALL_SHOW_RESULT)

    def test_parse_ctrl_pd_all_show_hpssacli(self):
        # => ctrl slot=0 pd all show
        return self.assertEqual(
            hpacucli.parse_ctrl_pd_all_show(CTRL_PD_ALL_SHOW_OUTPUT_HPSSACLI),
            CTRL_PD_ALL_SHOW_RESULT_HPSSACLI)

    def test_parse_ctrl_pd_show(self):
        # => ctrl slot=0 pd all show
        return self.assertEqual(
            hpacucli.parse_ctrl_pd_disk_show(CTRL_PD_SHOW_OUTPUT),
            CTRL_PD_SHOW_RESULT)

    def test_parse_ctrl_pd_show_hpssacli(self):
        # => ctrl slot=0 pd all show
        return self.assertEqual(
            hpacucli.parse_ctrl_pd_disk_show(CTRL_PD_SHOW_OUTPUT_HPSSACLI),
            CTRL_PD_SHOW_RESULT_HPSSACLI)

    def test_parse_ctrl_pd_all_show_unassigned(self):
        # => ctrl slot=2 pd all show
        return self.assertEqual(
            hpacucli.parse_ctrl_pd_all_show(
                CTRL_PD_ALL_SHOW_UNASSIGNED_OUTPUT),
            [('unassigned',
              [('1I:1:1', 'SATA', '1 TB', 'OK'),
               ('1I:1:2', 'SATA', '1 TB', 'OK'),
               ('1I:1:3', 'SATA', '1 TB', 'OK'),
               ('1I:1:4', 'SATA', '1 TB', 'OK'),
               ('2I:1:5', 'SATA', '1 TB', 'OK'),
               ('2I:1:6', 'SATA', '1 TB', 'OK'),
               ('2I:1:7', 'Solid State SATA', '100 GB', 'OK'),
               ('2I:1:8', 'Solid State SATA', '100 GB', 'OK')])])

    def test_parse_ctrl_pd_all_show_unassigned_hpssacli(self):
        # => ctrl slot=0 pd all show
        return self.assertEqual(
            hpacucli.parse_ctrl_pd_all_show(
                CTRL_PD_ALL_SHOW_UNASSIGNED_OUTPUT_HPSSACLI),
            [('unassigned',
              [('1I:1:1', 'SATA', '2 TB', 'OK'),
               ('1I:1:2', 'SATA', '2 TB', 'OK'),
               ('1I:1:3', 'SATA', '2 TB', 'OK'),
               ('1I:1:4', 'Solid State SATA', '100 GB', 'OK')])])

    def test_parse_ctrl_ld_all_show(self):
        # => ctrl slot=2 ld all show
        return self.assertEqual(
            hpacucli.parse_ctrl_ld_all_show(CTRL_LD_ALL_SHOW_OUTPUT),
            CTRL_LD_ALL_SHOW_RESULT)

    def test_parse_ctrl_ld_all_show_hpssacli(self):
        # => ctrl slot=0 ld all show
        return self.assertEqual(
            hpacucli.parse_ctrl_ld_all_show(CTRL_LD_ALL_SHOW_OUTPUT_HPSSACLI),
            CTRL_LD_ALL_SHOW_RESULT_HPSSACLI)

    def test_error(self):
        # => ctrl slot=2 delete force
        return self.assertRaisesRegexp(hpacucli.Error,
                                       '^\'Syntax error at "force"\'$',
                                       hpacucli.parse_error,
                                       '''
Error: Syntax error at "force"

''')

    def test_parse_ctrl_ld_show(self):
        # => ctrl slot=2 ld 1 show
        return self.assertEqual(
            hpacucli.parse_ctrl_ld_show(CTRL_LD_SHOW_OUTPUT),
            CTRL_LD_SHOW_RESULT
        )

    def test_parse_ctrl_ld_show_hpssacli(self):
        # => ctrl slot=0 ld 1 show
        return self.assertEqual(
            hpacucli.parse_ctrl_ld_show(CTRL_LD_SHOW_OUTPUT_HPSSACLI),
            CTRL_LD_SHOW_RESULT_HPSSACLI
        )

    def test_parse_ctrl_ld_show2(self):
        # => ctrl slot=2 ld 2 show
        return self.assertEqual(
            hpacucli.parse_ctrl_ld_show(CTRL_LD_SHOW_OUTPUT2),
            CTRL_LD_SHOW_RESULT2
        )


class TestController(unittest.TestCase):

    def setUp(self):
        self.cli = hpacucli.Cli()
        self.cli.process = mock.MagicMock()

    def test_ctrl_show(self):
        self.assertEqual.__self__.maxDiff = None
        self.cli.process.before = 'ctrl slot=0 show' + CTRL_SHOW_OUTPUT
        return self.assertEqual(self.cli.ctrl_show("slot=0"),
                                CTRL_SHOW_RESULT
                                )

    def test_ctrl_all_show(self):
        self.cli.process.before = 'ctrl all show' + CTRL_ALL_SHOW_OUTPUT
        return self.assertEqual(self.cli.ctrl_all_show(),
                                CTRL_ALL_SHOW_RESULT
                                )

    def test_ctrl_pd_all_show(self):
        self.cli.process.before = ('ctrl slot=2 pd all show'
                                   + CTRL_PD_ALL_SHOW_OUTPUT)
        return self.assertEqual(self.cli.ctrl_pd_all_show('slot=2'),
                                CTRL_PD_ALL_SHOW_RESULT
                                )

    def test_ctrl_ld_all_show(self):
        self.cli.process.before = ('ctrl slot=2 ld all show'
                                   + CTRL_LD_ALL_SHOW_OUTPUT)
        return self.assertEqual(self.cli.ctrl_ld_all_show('slot=2'),
                                CTRL_LD_ALL_SHOW_RESULT
                                )

    def test_ctrl_ld_show(self):
        self.cli.process.before = 'ctrl slot=2 ld 2 show' + CTRL_LD_SHOW_OUTPUT
        return self.assertEqual(
            self.cli.ctrl_ld_show('slot=2', '2'),
            CTRL_LD_SHOW_RESULT
        )

    @unittest.skip("WIP")
    def test_ctrl_create_ld(self):
        self.cli.process.before = ('ctrl slot=2 ld 2 show'
                                   + CTRL_LD_ALL_SHOW_OUTPUT
                                   + CTRL_LD_SHOW_OUTPUT)
        return self.assertEqual(
            self.cli.ctrl_create_ld('slot=2', ('2I:1:7', '2I:1:8'), '1'),
            '/dev/sda'
        )

    def test_timeout_expect(self):
        self.cli.process.expect = (
            mock.MagicMock(side_effect=pexpect.TIMEOUT('')))
        return self.assertRaises(hpacucli.Error, self.cli.ctrl_all_show)

##############################################################################
# Output from real commands and expected results below
##############################################################################


CTRL_SHOW_OUTPUT = '''
HPE Smart Array P816i-a SR Gen10 in Slot 0 (Embedded)
   Bus Interface: PCI
   Slot: 0
   Serial Number: PEYHD0DRHBH2C9
   RAID 6 (ADG) Status: Enabled
   Controller Status: OK
   Hardware Revision: A
   Firmware Version: 1.65-0
   Wait for Cache Room: Disabled
   Surface Analysis Inconsistency Notification: Disabled
   Post Prompt Timeout: 15 secs
   Cache Board Present: True
   Cache Status: OK
   Drive Write Cache: Disabled
   Total Cache Size: 4.0
   Total Cache Memory Available: 3.8
   No-Battery Write Cache: Disabled
   SSD Caching RAID5 WriteBack Enabled: True
   SSD Caching Version: 2
   Cache Backup Power Source: Batteries
   Battery/Capacitor Count: 1
   Battery/Capacitor Status: OK
   SATA NCQ Supported: True
   Spare Activation Mode: Activate on physical drive failure (default)
   Controller Temperature (C): 49
   Capacitor Temperature  (C): 39
   Number of Ports: 4 Internal only
   Encryption: Not Set
   Express Local Encryption: False
   Driver Name: smartpqi
   Driver Version: Linux 1.1.4-130
   PCI Address (Domain:Bus:Device.Function): 0000:23:00.0
   Negotiated PCIe Data Rate: PCIe 3.0 x8 (7880 MB/s)
   Controller Mode: Mixed
   Port Max Phy Rate Limiting Supported: False
   Latency Scheduler Setting: Disabled
   Current Power Mode: MaxPerformance
   Survival Mode: Enabled
   Host Serial Number: CZ28470BSS
   Sanitize Erase Supported: True
   Sanitize Lock: None
   Sensor ID: 0
      Location: Capacitor
      Current Value (C): 39
      Max Value Since Power On: 40
   Sensor ID: 1
      Location: ASIC
      Current Value (C): 49
      Max Value Since Power On: 50
   Sensor ID: 2
      Location: Unknown
      Current Value (C): 40
      Max Value Since Power On: 40
   Primary Boot Volume: None
   Secondary Boot Volume: None
'''

CTRL_SHOW_RESULT = {
    'sensor_id': '2',
    'wait_for_cache_room': 'Disabled',
    'express_local_encryption': 'False',
    'controller_mode': 'Mixed',
    'bus_interface': 'PCI',
    'controller_temperature_c': '49',
    'driver_version': 'Linux 1.1.4-130',
    'surface_analysis_inconsistency_notification': 'Disabled',
    'firmware_version': '1.65-0',
    'number_of_ports': '4 Internal only',
    'latency_scheduler_setting': 'Disabled',
    'battery/capacitor_count': '1',
    'raid_6_adg_status': 'Enabled',
    'primary_boot_volume': 'None',
    'hardware_revision': 'A',
    'sanitize_lock': 'None',
    'survival_mode': 'Enabled',
    'current_power_mode': 'MaxPerformance',
    'location': 'Unknown',
    'serial_number': 'PEYHD0DRHBH2C9',
    'cache_status': 'OK',
    'total_cache_memory_available': '3.8',
    'cache_backup_power_source': 'Batteries',
    'total_cache_size': '4.0',
    'negotiated_pcie_data_rate': 'PCIe 3.0 x8 (7880 MB/s)',
    'controller_status': 'OK',
    'pci_address_domain:bus:device.function': '0000:23:00.0',
    'post_prompt_timeout': '15 secs',
    'sanitize_erase_supported': 'True',
    'ssd_caching_raid5_writeback_enabled': 'True',
    'battery/capacitor_status': 'OK',
    'cache_board_present': 'True',
    'port_max_phy_rate_limiting_supported': 'False',
    'max_value_since_power_on': '40',
    'sata_ncq_supported': 'True',
    'no-battery_write_cache': 'Disabled',
    'spare_activation_mode': 'Activate on physical drive failure (default)',
    'host_serial_number': 'CZ28470BSS',
    'capacitor_temperature_c': '39',
    'drive_write_cache': 'Disabled',
    'driver_name': 'smartpqi',
    'current_value_c': '40',
    'ssd_caching_version': '2',
    'encryption': 'Not Set',
    'secondary_boot_volume': 'None'
}

CTRL_ALL_SHOW_OUTPUT = '''
Smart Array P420 in Slot 2                (sn: PDKRH0ARH4F1R6)

'''

CTRL_ALL_SHOW_RESULT = [(2, 'Smart Array P420', 'PDKRH0ARH4F1R6')]

CTRL_ALL_SHOW_OUTPUT_HPSSAPI = '''
Smart Array P420i in Slot 0 (Embedded)    (sn: 5001438025E9D500)

'''

CTRL_ALL_SHOW_RESULT_HPSSAPI = [(0, 'Smart Array P420i', '5001438025E9D500')]

CTRL_PD_ALL_SHOW_OUTPUT = '''
Smart Array P420 in Slot 2

   array A

      physicaldrive 2I:1:7 (port 2I:box 1:bay 7, Solid State SATA, 100 GB, OK)
      physicaldrive 2I:1:8 (port 2I:box 1:bay 8, Solid State SATA, 100 GB, OK)

   array B

      physicaldrive 1I:1:1 (port 1I:box 1:bay 1, SATA, 1 TB, OK)

   array C

      physicaldrive 1I:1:2 (port 1I:box 1:bay 2, SATA, 1 TB, OK)

   array D

      physicaldrive 1I:1:3 (port 1I:box 1:bay 3, SATA, 1 TB, OK)

   array E

      physicaldrive 1I:1:4 (port 1I:box 1:bay 4, SATA, 1 TB, OK)

   array F

      physicaldrive 2I:1:5 (port 2I:box 1:bay 5, SATA, 1 TB, OK)

   array G

      physicaldrive 2I:1:6 (port 2I:box 1:bay 6, SATA, 1 TB, OK)

'''

CTRL_PD_ALL_SHOW_RESULT = [
    ('array A', [('2I:1:7', 'Solid State SATA', '100 GB', 'OK'),
                 ('2I:1:8', 'Solid State SATA', '100 GB', 'OK')]),
    ('array B', [('1I:1:1', 'SATA', '1 TB', 'OK')]),
    ('array C', [('1I:1:2', 'SATA', '1 TB', 'OK')]),
    ('array D', [('1I:1:3', 'SATA', '1 TB', 'OK')]),
    ('array E', [('1I:1:4', 'SATA', '1 TB', 'OK')]),
    ('array F', [('2I:1:5', 'SATA', '1 TB', 'OK')]),
    ('array G', [('2I:1:6', 'SATA', '1 TB', 'OK')]),
]

CTRL_PD_ALL_SHOW_OUTPUT_HPSSACLI = '''
Smart Array P420i in Slot 0 (Embedded)

   array A

      physicaldrive 1I:1:4 (port 1I:box 1:bay 4, Solid State SATA, 100 GB, OK)

   array B

      physicaldrive 1I:1:1 (port 1I:box 1:bay 1, SATA, 2 TB, OK)

   array C

      physicaldrive 1I:1:2 (port 1I:box 1:bay 2, SATA, 2 TB, OK)

   array D

      physicaldrive 1I:1:3 (port 1I:box 1:bay 3, SATA, 2 TB, OK)

'''

CTRL_PD_ALL_SHOW_RESULT_HPSSACLI = [
    ('array A', [('1I:1:4', 'Solid State SATA', '100 GB', 'OK')]),
    ('array B', [('1I:1:1', 'SATA', '2 TB', 'OK')]),
    ('array C', [('1I:1:2', 'SATA', '2 TB', 'OK')]),
    ('array D', [('1I:1:3', 'SATA', '2 TB', 'OK')]),
]

CTRL_PD_SHOW_RESULT_HPSSACLI = {'carrier_application_version': '11',
                                'carrier_bootloader_version': '6',
                                'current_temperature_c': '32',
                                'drive_authentication_status': 'OK',
                                'drive_type': 'Unassigned Drive',
                                'firmware_revision': 'MK7OHPG3',
                                'interface_type': 'SATA',
                                'maximum_temperature_c': '36',
                                'model': 'ATA MB2000GBUPB',
                                'native_block_size': '512',
                                'phy_count': '1',
                                'phy_transfer_rate': '6.0Gbps',
                                'rotational_speed': '7200',
                                'sata_ncq_capable': 'True',
                                'sata_ncq_enabled': 'True',
                                'serial_number': 'YFK70EZA',
                                'size': '2 TB',
                                'status': 'OK'}

CTRL_PD_SHOW_RESULT = {'status': 'OK',
                       'phy_count': '1',
                       'sata_ncq_capable': 'True',
                       'ssd_smart_trip_wearout': 'False',
                       'carrier_bootloader_version': '6',
                       'firmware_revision': '5DV1HPG0',
                       'carrier_application_version': '11',
                       'interface_type': 'Solid State SATA',
                       'drive_authentication_status': 'OK',
                       'power_on_hours': '43',
                       'sata_ncq_enabled': 'True',
                       'usage_remaining': '100.00%',
                       'phy_transfer_rate': '6.0Gbps',
                       'drive_type': 'Data Drive',
                       'current_temperature_c': '11',
                       'serial_number': 'BTTV305001NZ100FGN',
                       'array': 'A',
                       'maximum_temperature_c': '22',
                       'model': 'ATA MK0100GCTYU',
                       'size': '100 GB'}

CTRL_PD_ALL_SHOW_UNASSIGNED_OUTPUT = '''

Smart Array P420 in Slot 2

   unassigned

      physicaldrive 1I:1:1 (port 1I:box 1:bay 1, SATA, 1 TB, OK)
      physicaldrive 1I:1:2 (port 1I:box 1:bay 2, SATA, 1 TB, OK)
      physicaldrive 1I:1:3 (port 1I:box 1:bay 3, SATA, 1 TB, OK)
      physicaldrive 1I:1:4 (port 1I:box 1:bay 4, SATA, 1 TB, OK)
      physicaldrive 2I:1:5 (port 2I:box 1:bay 5, SATA, 1 TB, OK)
      physicaldrive 2I:1:6 (port 2I:box 1:bay 6, SATA, 1 TB, OK)
      physicaldrive 2I:1:7 (port 2I:box 1:bay 7, Solid State SATA, 100 GB, OK)
      physicaldrive 2I:1:8 (port 2I:box 1:bay 8, Solid State SATA, 100 GB, OK)

'''

CTRL_PD_ALL_SHOW_UNASSIGNED_OUTPUT_HPSSACLI = '''

Smart Array P420i in Slot 0 (Embedded)

   unassigned

      physicaldrive 1I:1:1 (port 1I:box 1:bay 1, SATA, 2 TB, OK)
      physicaldrive 1I:1:2 (port 1I:box 1:bay 2, SATA, 2 TB, OK)
      physicaldrive 1I:1:3 (port 1I:box 1:bay 3, SATA, 2 TB, OK)
      physicaldrive 1I:1:4 (port 1I:box 1:bay 4, Solid State SATA, 100 GB, OK)

'''

CTRL_LD_ALL_SHOW_OUTPUT = '''
Smart Array P420 in Slot 2

   array A

      logicaldrive 1 (93.1 GB, RAID 1, OK)

   array B

      logicaldrive 2 (931.5 GB, RAID 0, OK)

   array C

      logicaldrive 3 (931.5 GB, RAID 0, OK)

   array D

      logicaldrive 4 (931.5 GB, RAID 0, OK)

   array E

      logicaldrive 5 (931.5 GB, RAID 0, OK)

   array F

      logicaldrive 6 (931.5 GB, RAID 0, OK)

   array G

      logicaldrive 7 (931.5 GB, RAID 0, OK)

'''

CTRL_LD_ALL_SHOW_RESULT = [
    ('array A', [('1', '93.1 GB', 'RAID 1', 'OK')]),
    ('array B', [('2', '931.5 GB', 'RAID 0', 'OK')]),
    ('array C', [('3', '931.5 GB', 'RAID 0', 'OK')]),
    ('array D', [('4', '931.5 GB', 'RAID 0', 'OK')]),
    ('array E', [('5', '931.5 GB', 'RAID 0', 'OK')]),
    ('array F', [('6', '931.5 GB', 'RAID 0', 'OK')]),
    ('array G', [('7', '931.5 GB', 'RAID 0', 'OK')]),
]

CTRL_LD_ALL_SHOW_OUTPUT_HPSSACLI = '''

Smart Array P420i in Slot 0 (Embedded)

   array A

      logicaldrive 1 (93.1 GB, RAID 0, OK)

'''

CTRL_LD_ALL_SHOW_RESULT_HPSSACLI = [
    ('array A', [('1', '93.1 GB', 'RAID 0', 'OK')]),
]

# => ctrl slot=2 pd 2I:1:8 show
CTRL_PD_SHOW_OUTPUT = '''

Smart Array P420 in Slot 2

   array A

      physicaldrive 2I:1:8
         Port: 2I
         Box: 1
         Bay: 8
         Status: OK
         Drive Type: Data Drive
         Interface Type: Solid State SATA
         Size: 100 GB
         Firmware Revision: 5DV1HPG0
         Serial Number: BTTV305001NZ100FGN
         Model: ATA     MK0100GCTYU
         SATA NCQ Capable: True
         SATA NCQ Enabled: True
         Current Temperature (C): 11
         Maximum Temperature (C): 22
         Usage remaining: 100.00%
         Power On Hours: 43
         SSD Smart Trip Wearout: False
         PHY Count: 1
         PHY Transfer Rate: 6.0Gbps
         Drive Authentication Status: OK
         Carrier Application Version: 11
         Carrier Bootloader Version: 6

'''

CTRL_PD_SHOW_OUTPUT_HPSSACLI = '''

Smart Array P420i in Slot 0 (Embedded)

   unassigned

      physicaldrive 1I:1:1
         Port: 1I
         Box: 1
         Bay: 1
         Status: OK
         Drive Type: Unassigned Drive
         Interface Type: SATA
         Size: 2 TB
         Native Block Size: 512
         Rotational Speed: 7200
         Firmware Revision: MK7OHPG3
         Serial Number: YFK70EZA
         Model: ATA     MB2000GBUPB
         SATA NCQ Capable: True
         SATA NCQ Enabled: True
         Current Temperature (C): 32
         Maximum Temperature (C): 36
         PHY Count: 1
         PHY Transfer Rate: 6.0Gbps
         Drive Authentication Status: OK
         Carrier Application Version: 11
         Carrier Bootloader Version: 6


'''

# => ctrl slot=2 ld 1 show
CTRL_LD_SHOW_OUTPUT = sample('ctrl_ld_show')

CTRL_LD_SHOW_RESULT = {
    'Caching': 'Enabled',
    'Caching Association': 'None',
    'Cylinders': '23934',
    'Disk Name': '/dev/sda',
    'Drive Type': 'Data',
    'Fault Tolerance': '1',
    'Full Stripe Size': '256 KB',
    'Heads': '255',
    'Logical Drive': '1',
    'Logical Drive Label': 'A299BBB1PDKRH0ARH4F1R6D4B9',
    'Mirror Group 0': '2I:1:7',
    'Mirror Group 1': '2I:1:8',
    'Mount Points': 'None',
    'Sectors Per Track': '32',
    'Size': '93.1 GB',
    'Status': 'OK',
    'Strip Size': '256 KB',
    'Unique Identifier': '600508B1001CE81A48ACAE0E3331C2F6'}

CTRL_LD_SHOW_OUTPUT_HPSSACLI = '''

Smart Array P420i in Slot 0 (Embedded)

   array A

      Logical Drive: 1
         Size: 93.1 GB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 23934
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001C32C501A237950F9370AB
         Disk Name: /dev/sda          Mount Points: None
         Logical Drive Label: 01B8A4585001438025E9D500  21EF
         Drive Type: Data
         LD Acceleration Method: Controller Cache

'''

CTRL_LD_SHOW_RESULT_HPSSACLI = {
    'Caching': 'Enabled',
    'Cylinders': '23934',
    'Disk Name': '/dev/sda',
    'Drive Type': 'Data',
    'Fault Tolerance': '0',
    'Full Stripe Size': '256 KB',
    'Heads': '255',
    'LD Acceleration Method': 'Controller Cache',
    'Logical Drive': '1',
    'Logical Drive Label': '01B8A4585001438025E9D500  21EF',
    'Mount Points': 'None',
    'Sectors Per Track': '32',
    'Size': '93.1 GB',
    'Status': 'OK',
    'Strip Size': '256 KB',
    'Unique Identifier': '600508B1001C32C501A237950F9370AB'
}

# => ctrl slot=2 ld 2 show

CTRL_LD_SHOW_OUTPUT2 = '''

Smart Array P420 in Slot 2

   array B

      Logical Drive: 2
         Size: 931.5 GB
         Fault Tolerance: 0
         Heads: 255
         Sectors Per Track: 32
         Cylinders: 65535
         Strip Size: 256 KB
         Full Stripe Size: 256 KB
         Status: OK
         Caching:  Enabled
         Unique Identifier: 600508B1001C87603833075ECAC289A6
         Disk Name: /dev/sdb
         Mount Points: None
         Logical Drive Label: A29A9DA2PDKRH0ARH4F1R63C33
         Drive Type: Data
         Caching Association: None

'''

CTRL_LD_SHOW_RESULT2 = {
    'Status': 'OK',
    'Mount Points': 'None',
    'Sectors Per Track': '32',
    'Caching Association': 'None',
    'Cylinders': '65535',
    'Full Stripe Size': '256 KB',
    'Drive Type': 'Data',
    'Logical Drive Label': 'A29A9DA2PDKRH0ARH4F1R63C33',
    'Strip Size': '256 KB',
    'Disk Name': '/dev/sdb',
    'Caching': 'Enabled',
    'Heads': '255',
    'Unique Identifier': '600508B1001C87603833075ECAC289A6',
    'Logical Drive': '2',
    'Fault Tolerance': '0',
    'Size': '931.5 GB'}

if __name__ == "__main__":
    unittest.main()
