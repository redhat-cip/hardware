# Copyright (C) 2026 Red Hat
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

import io
from pathlib import Path
import unittest
from unittest import mock

from hardware import storcli


SAMPLE_JSON = Path(__file__).parent / 'samples' / 'storcli_controller_json'


class TestStorcli(unittest.TestCase):

    def test_search_exec_prefers_perccli(self):
        with mock.patch.object(storcli.shutil, 'which',
                               side_effect=['/usr/bin/perccli64']):
            self.assertEqual(storcli.search_exec(), '/usr/bin/perccli64')

    def test_search_exec_uses_storcli_when_perccli_is_missing(self):
        def which(name):
            if name == 'storcli64':
                return '/usr/bin/storcli64'
            return None

        with mock.patch.object(storcli.shutil, 'which', side_effect=which):
            self.assertEqual(storcli.search_exec(), '/usr/bin/storcli64')

    def test_search_exec_uses_vendor_storcli_path(self):
        def which(name):
            if name == '/opt/MegaRAID/storcli/storcli64':
                return name
            return None

        with mock.patch.object(storcli.shutil, 'which', side_effect=which):
            self.assertEqual(storcli.search_exec(),
                             '/opt/MegaRAID/storcli/storcli64')

    def test_search_exec_prefers_vendor_perccli_over_path_storcli(self):
        def which(name):
            if name == 'storcli64':
                return '/usr/bin/storcli64'
            if name == '/opt/MegaRAID/perccli/perccli64':
                return name
            return None

        with mock.patch.object(storcli.shutil, 'which', side_effect=which):
            self.assertEqual(storcli.search_exec(),
                             '/opt/MegaRAID/perccli/perccli64')

    def test_search_exec_returns_none_when_missing(self):
        with mock.patch.object(storcli.shutil, 'which', return_value=None):
            self.assertIsNone(storcli.search_exec())

    def test_parse_output(self):
        parsed = storcli.parse_output(SAMPLE_JSON.read_text())
        self.assertEqual(parsed['Controllers'][0]['Command Status']['Status'],
                         'Success')
        self.assertEqual(
            parsed['Controllers'][0]['Response Data']['Basics']['Controller'],
            0)

    def test_parse_output_invalid_json(self):
        self.assertEqual(storcli.parse_output('not json'), {})

    def test_parse_output_non_object_json(self):
        self.assertEqual(storcli.parse_output('[]'), {})

    def test_controller_data_maps_controller_and_disks(self):
        result = storcli._controller_data(
            storcli.parse_output(SAMPLE_JSON.read_text()))

        self.assertIn(('megaraid', 'Controller_0', 'Model',
                       'Sample RAID Controller'), result)
        self.assertIn(('megaraid', 'Controller_0', 'FirmwareVersion',
                       '1.2.3'), result)
        self.assertIn(('pdisk', 'disk0', 'ctrl', '0'), result)
        self.assertIn(('pdisk', 'disk0', 'type', 'SAS'), result)
        self.assertIn(('pdisk', 'disk0', 'id', '32:5'), result)
        self.assertIn(('pdisk', 'disk0', 'size', '465.25'), result)
        self.assertIn(('ldisk', 'disk0', 'DgVd', '0/0'), result)
        self.assertIn(('ldisk', 'disk0', 'RaidLevel', 'RAID1'), result)
        self.assertIn(('ldisk', 'disk0', 'Size', '465.25'), result)
        self.assertIn(('disk', 'megaraid', 'count', '1'), result)

    @mock.patch.object(storcli.megacli, 'detect', return_value=['legacy'])
    @mock.patch.object(storcli, 'search_exec', return_value=None)
    def test_detect_falls_back_to_megacli_when_new_cli_is_missing(
            self, _search_exec, legacy_detect):
        self.assertEqual(storcli.detect(), ['legacy'])
        legacy_detect.assert_called_once_with()

    @mock.patch.object(storcli.megacli, 'search_exec', return_value=None)
    @mock.patch.object(storcli, 'run_and_parse')
    @mock.patch.object(storcli, 'search_exec', return_value='/usr/bin/storcli')
    def test_detect_uses_storcli_results(self, _search_exec, run_and_parse,
                                         _legacy_search):
        run_and_parse.return_value = storcli.parse_output(
            SAMPLE_JSON.read_text())

        result = storcli.detect()

        self.assertIn(('disk', 'megaraid', 'count', '1'), result)
        run_and_parse.assert_called_once_with('/call', 'show', 'all')

    @mock.patch.object(storcli, 'search_exec', return_value='/usr/bin/perccli')
    @mock.patch.object(storcli.subprocess, 'run')
    def test_run_and_parse_adds_json_flag(self, run, _search_exec):
        run.return_value.stdout = SAMPLE_JSON.read_text()

        result = storcli.run_and_parse('/call', 'show', 'all')

        self.assertIn('Controllers', result)
        self.assertEqual(run.call_args.args[0],
                         ['/usr/bin/perccli', '/call', 'show', 'all', 'J'])
        self.assertTrue(run.call_args.kwargs['text'])
        self.assertFalse(run.call_args.kwargs['check'])

    @mock.patch.object(storcli, 'search_exec', return_value='/usr/bin/storcli')
    @mock.patch.object(storcli.subprocess, 'run')
    def test_run_and_parse_does_not_duplicate_json_flag(self, run,
                                                        _search_exec):
        run.return_value.stdout = '{}'

        storcli.run_and_parse('/call', 'show', 'all', 'j')

        self.assertEqual(run.call_args.args[0],
                         ['/usr/bin/storcli', '/call', 'show', 'all', 'j'])

    @mock.patch.object(storcli, 'search_exec', return_value=None)
    def test_run_cli_returns_empty_when_missing(self, _search_exec):
        with mock.patch.object(storcli.sys, 'stderr', new=io.StringIO()):
            self.assertEqual(storcli.run_cli('/call', 'show', 'all'), '')

    @mock.patch.object(storcli, 'search_exec', return_value='/usr/bin/storcli')
    @mock.patch.object(storcli.subprocess, 'run', side_effect=OSError('oops'))
    def test_run_cli_handles_execution_error(self, _run, _search_exec):
        with mock.patch.object(storcli.sys, 'stderr', new=io.StringIO()):
            self.assertEqual(storcli.run_cli('/call', 'show', 'all'), '')


if __name__ == '__main__':
    unittest.main()
