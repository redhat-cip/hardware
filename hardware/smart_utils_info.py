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

NVME_INFOS = {
    'Model Number:': 'model_number',
    'Serial Number:': 'serial_number',
    'Firmware Version:': 'firmware_version',
    'Total NVM Capacity:': 'total_nvm_capacity',
    'Warning  Comp. Temp. Threshold:': 'warning_temp_threshold',
    'Critical Comp. Temp. Threshold:': 'critical_temp_threshold',
    'Critical Warning:': 'critical_warning',
    'Temperature:': 'temperature',
    'Power Cycles:': 'power_cycles',
    'Power On Hours:': 'power_on_hours',
    'Unsafe Shutdowns:': 'unsafe_shutdowns',
    'Media and Data Integrity Errors:': 'media_data_integrity_errors',
    'Error Information Log Entries:': 'error_information_log_entries',
}

SMART_FIELDS = {
    "Serial number:": "serial_number",
    "SMART Health Status:": "health",
    "Specified cycle count over device "
    "lifetime:": "specified_start_stop_cycle_count_over_lifetime",
    "Accumulated start-stop cycles:": "start_stop_cycle_count",
    "Specified load-unload count over device "
    "lifetime:": "specified_load_count_over_lifetime",
    "Accumulated load-unload cycles:": "load_count",
    "number of hours powered up =": "power_on_hours",
    "Blocks sent to initiator =": "blocks_sent",
    "Blocks received from initiator =": "blocks_received",
    "Blocks read from cache and sent to initiator =": "blocks_read_from_cache",
    "Non-medium error count:": "non_medium_errors_count",
    "Current Drive Temperature:": "current_drive_temperature",
    "Drive Trip Temperature:": "drive_trip_temperature",
    "Manufactured in ": "manufacture_date",
    "Rotation Rate": "rotation_rate",
}
