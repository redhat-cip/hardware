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

"""Wrapper functions around the StorCLI and PERCCLI commands."""

import json
import re
import shutil
import subprocess
import sys

from hardware import detect_utils
from hardware import megacli


# PERCCLI is the preferred utility for Dell PERC controllers. StorCLI is the
# general-purpose alternative for controllers supported by the same CLI.
EXECUTABLES = (
    'perccli64', 'perccli', 'PercCLI64', 'PercCLI',
    'storcli64', 'storcli', 'StorCLI64', 'StorCLI',
)


def search_exec():
    """Return the path to the first available PERCCLI/StorCLI executable."""
    for executable in EXECUTABLES:
        path = shutil.which(executable)
        if path:
            return path
    return None


def parse_output(output):
    """Parse JSON output from StorCLI or PERCCLI.

    Invalid or empty output is treated as no result, matching the behavior of
    the other hardware command wrappers when a utility is unavailable.
    """
    try:
        result = json.loads(output)
    except (TypeError, ValueError):
        return {}
    return result if isinstance(result, dict) else {}


def run_cli(*args):
    """Run the available CLI with the supplied arguments and return stdout."""
    prog_exec = search_exec()
    if not prog_exec:
        sys.stderr.write('Cannot find perccli or storcli on the system\n')
        return ''

    try:
        proc = subprocess.run(
            [prog_exec, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError as exc:
        sys.stderr.write('Unable to run %s: %s\n' % (prog_exec, exc))
        return ''

    return proc.stdout


def run_and_parse(*args):
    """Run a read-only CLI command with JSON output enabled and parse it."""
    cli_args = list(args)
    if not cli_args or cli_args[-1].lower() != 'j':
        cli_args.append('J')
    return parse_output(run_cli(*cli_args))


def _mapping(value):
    """Return a mapping for a StorCLI response section."""
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    return {}


def _key_name(key):
    """Convert a CLI field name to the existing CamelCase field style."""
    if key == 'RaidLevel':
        return key
    return ''.join(part.title() for part in re.findall(r'[A-Za-z0-9]+', key))


def _add_properties(hw_list, category, device, properties, excluded=()):
    for key, value in properties.items():
        if key in excluded or value is None:
            continue
        hw_list.append((category, device, _key_name(str(key)), str(value)))


def _size_in_gb(value):
    if value is None or not str(value).strip():
        return None
    return detect_utils.size_in_gb(str(value))


def _controller_data(data):
    """Translate StorCLI controller, physical disk, and virtual disk data."""
    hw_list = []
    disk_count = 0
    total_disk_size = 0.0
    controllers = data.get('Controllers', [])
    if not isinstance(controllers, list):
        return hw_list

    for index, controller in enumerate(controllers):
        if not isinstance(controller, dict):
            continue
        command_status = _mapping(controller.get('Command Status'))
        if command_status.get('Status', 'Success') != 'Success':
            continue
        response = controller.get('Response Data')
        if not isinstance(response, dict):
            continue

        basics = _mapping(response.get('Basics'))
        controller_id = str(basics.get('Controller', index))
        controller_name = 'Controller_%s' % controller_id

        for section in ('Basics', 'Version', 'Status'):
            _add_properties(hw_list, 'megaraid', controller_name,
                            _mapping(response.get(section)))

        physical_disks = response.get('PD LIST', [])
        enclosures_seen = set()
        if isinstance(physical_disks, list):
            for physical_disk in physical_disks:
                if not isinstance(physical_disk, dict):
                    continue
                disk_name = 'disk%d' % disk_count
                disk_count += 1
                enclosure_slot = str(physical_disk.get('EID:Slt', ''))
                enclosure = enclosure_slot.partition(':')[0]
                has_enclosure = ':' in enclosure_slot

                hw_list.append(('pdisk', disk_name, 'ctrl', controller_id))
                hw_list.append(('pdisk', disk_name, 'type', str(
                    physical_disk.get('Intf', ''))))
                if has_enclosure:
                    hw_list.append(('pdisk', disk_name, 'id', enclosure_slot))
                    if enclosure not in enclosures_seen:
                        enclosure_name = '%s/Enclosure_%s' % (controller_name,
                                                              enclosure)
                        hw_list.append(('megaraid', enclosure_name,
                                        'DeviceId', enclosure))
                        enclosures_seen.add(enclosure)
                size = _size_in_gb(physical_disk.get('Size'))
                if size is not None:
                    hw_list.append(('pdisk', disk_name, 'size', size))
                    try:
                        total_disk_size += float(size)
                    except ValueError:
                        pass

                _add_properties(
                    hw_list, 'pdisk', disk_name, physical_disk,
                    excluded=('EID:Slt', 'Intf', 'Size'))

        virtual_disks = response.get('VD LIST', [])
        if isinstance(virtual_disks, list):
            for disk_index, virtual_disk in enumerate(virtual_disks):
                if not isinstance(virtual_disk, dict):
                    continue
                disk_name = 'disk%d' % disk_index
                size = _size_in_gb(virtual_disk.get('Size'))
                virtual_disk_properties = dict(virtual_disk)
                if 'TYPE' in virtual_disk_properties:
                    virtual_disk_properties['RaidLevel'] = (
                        virtual_disk_properties.pop('TYPE'))
                _add_properties(hw_list, 'ldisk', disk_name,
                                virtual_disk_properties, excluded=('Size',))
                if size is not None:
                    hw_list.append(('ldisk', disk_name, 'Size', size))

    if total_disk_size:
        hw_list.append(('pdisk', 'all', 'size', '%.2f' % total_disk_size))
    hw_list.append(('disk', 'megaraid', 'count', str(disk_count)))
    return hw_list


def detect():
    """Detect RAID controllers, falling back to MegaCLI when needed."""
    if not search_exec():
        return megacli.detect()

    result = _controller_data(run_and_parse('/call', 'show', 'all'))
    if result and any(item[0] == 'megaraid' for item in result):
        return result

    if megacli.search_exec():
        return megacli.detect()
    return []
