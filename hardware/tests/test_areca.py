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

from hardware import areca
from hardware.tests.utils import sample


class TestMegacliTest(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        def my_run(*args, **arr):
            return self.output
        self.run = areca._run_areca
        areca._run_areca = my_run

    def tearDown(self):
        areca.run = self.run

    def test_sys_info(self):
        self.output = sample('areca_sysinfo')
        self.assertEqual(areca._sys_info(),
                         {'MainProcessor': 800,
                          'MainProcessor/unit': 'MHz',
                          'CpuIcacheSize': 32,
                          'CpuIcacheSize/unit': 'KB',
                          'CpuDcacheSize': 32,
                          'CpuDcacheSize/unit': 'KB',
                          'CpuScacheSize': 512,
                          'CpuScacheSize/unit': 'KB',
                          'SystemMemory': '256MB/533MHz/ECC',
                          'FirmwareVersion': 'V1.49 2011-08-10',
                          'BootRomVersion': 'V1.49 2010-12-02',
                          'SerialNumber': 'Y106CABRAR200408',
                          'ControllerName': 'ARC-1222',
                          'CurrentIpAddress': '192.168.1.100'})

    def test_sys_showcfg(self):
        self.output = sample('areca_sys_showcfg')
        self.assertEqual(areca._sys_showcfg(),
                         {'SystemBeeperSetting': 'Enabled',
                          'BackgroundTaskPriority': 'High(80%)',
                          'Jbod/RaidConfiguration': 'JBOD',
                          'SataNcqSupport': 'Enabled',
                          'HddReadAheadCache': 'Enabled',
                          'VolumeDataReadAhead': 'Normal',
                          'HddQueueDepth': 8,
                          'EmptyHddSlotLed': 'ON',
                          'CpuFanDetection': 'Disabled',
                          'SasMuxSetting': 'Auto',
                          'Ses2Support': 'Enabled',
                          'MaxCommandLength': '148K',
                          'AutoActivateIncompleteRaid': 'Disabled',
                          'DiskWriteCacheMode': 'Disabled',
                          'WriteSameForInitialization': 'SAS And SATA',
                          'HotPluggedDiskForRebuilding': 'Blank Disk Only',
                          'DiskCapacityTruncationMode': 'Multiples Of 10G',
                          'SmartOptionForHdd': 'Failed The Drive',
                          'SmartPollingInterval': 'On Demand'})

    def test_adsys_info(self):
        self.output = sample('areca_adsysinfo')
        self.assertEqual(areca._adsys_info(),
                         {'TlerSetting': 7,
                          'TlerSetting/unit': 'Seconds',
                          'TimeoutSetting': 8,
                          'TimeoutSetting/unit': 'Seconds',
                          'RetryCountSetting': 2,
                          'RetryCountSetting/unit': 'Times',
                          'BufferThreshold': 25,
                          'BufferThreshold/unit': '%',
                          'AmountOfReadAhead': 'Auto',
                          'NumberOfAvStreams': 6,
                          'OptimizeAvRecoding': 'Disabled',
                          'PhyStatus': 'Default',
                          'ReadPerformanceMargin': 0,
                          'ReadPerformanceMargin/unit': '%',
                          'WritePerformanceMargin': 0,
                          'WritePerformanceMargin/unit': '%',
                          'ReadAndDiscardParityData': 'Disabled',
                          'HitachiSataHddSpeed': 'Default',
                          'WdcSataHddSpeed': 'Default',
                          'SeagateSataHddSpeed': 'Default'})

    def test_hw_info(self):
        self.output = sample('areca_hw_info')
        self.assertEqual(areca._hw_info(),
                         {'Enclosure1/12V': '12.220',
                          'Enclosure1/12V/unit': 'V',
                          'Enclosure1/3.3V': '3.328',
                          'Enclosure1/3.3V/unit': 'V',
                          'Enclosure1/5V': '5.134',
                          'Enclosure1/5V/unit': 'V',
                          'Enclosure1/BatteryStatus': 100,
                          'Enclosure1/BatteryStatus/unit': '%',
                          'Enclosure1/ControllerTemp.': 37,
                          'Enclosure1/ControllerTemp./unit': 'C',
                          'Enclosure1/Cpu+1.2V': '1.216',
                          'Enclosure1/Cpu+1.2V/unit': 'V',
                          'Enclosure1/Cpu+1.8V': '1.856',
                          'Enclosure1/Cpu+1.8V/unit': 'V',
                          'Enclosure1/CpuFan': 2596,
                          'Enclosure1/CpuFan/unit': 'RPM',
                          'Enclosure1/CpuTemperature': 39,
                          'Enclosure1/CpuTemperature/unit': 'C',
                          'Enclosure1/Ddr-Ii+0.9V': '0.912',
                          'Enclosure1/Ddr-Ii+0.9V/unit': 'V',
                          'Enclosure1/Ddr-Ii+1.8V': '1.856',
                          'Enclosure1/Ddr-Ii+1.8V/unit': 'V',
                          'Enclosure1/Pci-E+1.8V': '1.856',
                          'Enclosure1/Pci-E+1.8V/unit': 'V'})

    def test_hddpwr_info(self):
        self.output = sample('areca_hddpwr_info')
        self.assertEqual(areca._hdd_pwr_info(),
                         {'StaggerPowerOnControl': '0.7',
                          'TimeToHddLowPowerIdle': 'Disabled',
                          'TimeToHddLowRpmMode': 'Disabled',
                          'TimeToSpinDownIdleHdd': 'Disabled'})

    def test_diskinfo(self):
        self.output = sample('areca_disks_info')
        self.assertEqual(areca._disk_info(1),
                         {'DeviceLocation': 'Enclosure#1 Slot#8',
                          'DeviceState': 'NORMAL',
                          'DeviceTemperature': 27,
                          'DeviceTemperature/unit': 'C',
                          'DeviceType': 'SATA(5001B4D4188DF017)',
                          'DiskCapacity': '1000.2',
                          'DiskCapacity/unit': 'GB',
                          'FirmwareRev.': 'JP4OA3MA',
                          'MediaErrorCount': 0,
                          'ModelName': 'Hitachi HDS721010CLA330',
                          'SerialNumber': 'JPS930N121H4YV',
                          'SmartCalibrationRetries': 'N.A.(N.A.)',
                          'SmartReadErrorRate': '100(16)',
                          'SmartReallocationCount': '100(5)',
                          'SmartSeekErrorRate': '100(67)',
                          'SmartSpinupRetries': '100(60)',
                          'SmartSpinupTime': '122(24)',
                          'TimeoutCount': 0})
