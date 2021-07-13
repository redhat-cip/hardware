# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

import contextlib
import os
import re
import subprocess
from subprocess import Popen
import sys
import uuid


AUXV_FLAGS = ["AT_HWCAP", "AT_HWCAP2", "AT_PAGESZ",
              "AT_FLAGS", "AT_PLATFORM"]
# These flags may or not be present on a particular arch
AUXV_OPT_FLAGS = ["AT_BASE_PLATFORM"]


def cmd(cmdline):
    """Equivalent of commands.getstatusoutput"""
    try:
        return 0, subprocess.check_output(cmdline,
                                          shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as excpt:
        return excpt.returncode, excpt.output


def output_lines(cmdline):
    """Run a shell command and returns the output as lines."""
    proc = subprocess.Popen(cmdline, shell=True, stdout=subprocess.PIPE,
                            universal_newlines=True)
    stdout = proc.communicate()[0]
    return stdout.splitlines()


def parse_lldtool(hw_lst, interface_name, lines):
    content = ""
    header = ""
    sub_header = ""
    for line in lines:
        if line.startswith('\t'):
            content = line.strip().strip('\n').strip('\t').replace("/", "_")
        else:
            header = line
            header = line.strip().strip('\n').strip('\t').replace("/", "_")
            header = header.replace(" TLV", "")
            content = ""
            sub_header = ""
        if header and content:
            if ":" in content:
                line = content.split(":")
                if (len(line) == 2) and (line[1] == ''):
                    sub_header = line[0].strip().strip('\n').strip('\t')
                    sub_header = sub_header.replace("/", "_")
                    sub_header = sub_header.replace(" TLV:", "")
                    header = header + "/" + sub_header
                    continue
                else:
                    left = line[0].strip().strip('\n').strip('\t')
                    left = left.replace("/", "_")
                    right = content.replace(left + ":", "").strip().strip('\n')
                    right = right.strip('\t').replace("/", "_")
                    # If we never had this sub_header for this header
                    # let's add one
                    if left != sub_header:
                        sub_header = left
                        header = header + "/" + sub_header
                    content = right
            hw_lst.append(('lldp', interface_name, header, content))

    return hw_lst


def get_lld_status(hw_lst, interface_name):
    return parse_lldtool(hw_lst, interface_name,
                         output_lines("lldptool -t -n -i %s" % interface_name))


def parse_ethtool(hw_lst, interface_name, lines):
    content = ""
    header = ""
    sub_header = ""
    original_header = ""
    for line in lines:
        if interface_name in line:
            continue
        data = line.split(":")
        line = line.strip('\n')
        if line.startswith('\t'):
            sub_header = data[0].replace('\t', '').strip()
            header = "%s/%s" % (original_header, sub_header)
        else:
            header = data[0]
            original_header = header

        header = header.replace('\t', '').strip()
        content = ''.join(data[1:]).replace('\t', '').strip()
        if not content:
            continue
        hw_lst.append(('network', interface_name, header, content))

    return hw_lst


def get_ethtool_status(hw_lst, interface_name):
    parse_ethtool(hw_lst, interface_name,
                  output_lines("ethtool -a %s" % interface_name))
    parse_ethtool(hw_lst, interface_name,
                  output_lines("ethtool -k %s" % interface_name))


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def size_in_gb(size):
    """Return the size in GB without the unit."""
    result = size.replace(' ', '')
    if result[-2:] == 'GB':
        return result[:-2]

    elif result[-2:] == 'TB':
        # some size are provided in x.y GB
        # we need to compute the size in TB by
        # considering the input as a float to be
        # multiplied by 1000
        return str(int(float(result[:-2]) * 1000))

    return result


def clean_str(val):
    """Cleanup a bad string (invalid UTF-8 encoding)."""
    if isinstance(val, bytes):
        val = val.decode('UTF-8', 'replace')
    return val


def clean_tuples(lst):
    """Clean a list of tuples from bad UTF-8 strings."""
    return [tuple([clean_str(val) for val in elt]) for elt in lst]


def _get_uuid_x86_64():
    """Get uuid from dmidecode"""

    uuid_cmd = subprocess.Popen(
        "dmidecode -t 1 | grep UUID | awk '{print $2}'", shell=True,
        stdout=subprocess.PIPE, universal_newlines=True)
    stdout = uuid_cmd.communicate()[0]
    return stdout.rstrip()


def _get_uuid_ppc64le(hw_lst):
    """Get uuid for ppc64 arch systems"""
    vendor = None
    serial = None
    for (_, _, sys_subtype, value) in hw_lst:
        if sys_subtype == 'vendor':
            vendor = value
        if sys_subtype == 'serial':
            serial = value

    system_uuid = None
    system_uuid_fname = '/sys/firmware/devicetree/base/system-uuid'
    if os.access(system_uuid_fname, os.R_OK):
        with open(system_uuid_fname) as uuidfile:
            system_uuid = uuidfile.read().rstrip(' \t\r\n\0')
    elif vendor and serial:
        root = uuid.UUID(bytes=b'\x00' * 16)
        vendor_uuid = uuid.uuid5(root, vendor)
        system_uuid = str(uuid.uuid5(vendor_uuid, serial))

    return system_uuid


def get_uuid(hw_lst):
    if os.uname()[4] == 'ppc64le':
        return _get_uuid_ppc64le(hw_lst)
    return _get_uuid_x86_64()


def get_value(hw_lst, *vect):
    for i in hw_lst:
        if i[0:3] == vect:
            return i[3]
    return ''


def get_cidr(netmask):
    """Convert a netmask to a CIDR."""
    binary_str = ''
    for octet in netmask.split('.'):
        binary_str += bin(int(octet))[2:].zfill(8)
    return str(len(binary_str.rstrip('0')))


def from_file(filename):
    """Open a file and read its first line.

    :param filename: the name of the file to be read
    :returns: string -- the first line of filename, stripped of the final '\n'
    :raises: IOError
    """

    with open(filename) as f:
        value = f.readline().rstrip('\n')
    return value


def fix_bad_serial(hw_lst, system_uuid, mobo_id, nic_id):
    """Fix bad serial number.

    TYAN or Supermicro are known to provide fake serial numbers
    as a system serial number.

    In that case, let's use another serial.

    :param hw_lst: list of tuples that represent the system
    :param system_uuid: system uuid
    :param mobo_id: motherboard id
    :param nic_id: NIC id
    """
    for i in hw_lst:
        if i[0:3] == ('system', 'product', 'serial'):
            # Does the current serial number is part of the quirk list
            if i[3] in ['0123456789', '0000000000']:

                # Let's delete the stupid SN and use the another ID instead
                # Items are ordered by level of confidence
                new_serial = ''

                if system_uuid:
                    new_serial = system_uuid
                elif mobo_id:
                    new_serial = mobo_id
                elif nic_id:
                    new_serial = nic_id

                if new_serial:
                    hw_lst.remove(i)
                    hw_lst.append(('system', 'product', 'serial',
                                   new_serial))

                break


def get_cpus(hw_lst):
    def _maybe_int(v):
        try:
            base = 10
            if 'x' in v:
                base = 16
            v = int(v, base)
        except Exception:
            pass
        return v

    def _get_governor(lcpu):
        """Return the scaling governor of a logical core.

        :param lcpu: the logical core number
        :returns: the scaling governor if it exists, otherwise None
        """
        with contextlib.suppress(IOError):
            file_name = ("/sys/devices/system/cpu/cpufreq/"
                         "policy{}/scaling_governor".format(lcpu))
            return from_file(file_name)

        # fallback to the old interface available in kernels < 4.3;
        with contextlib.suppress(IOError):
            file_name = ("/sys/devices/system/cpu/cpu{}/cpufreq/"
                         "scaling_governor".format(lcpu))
            return from_file(file_name)
        return None

    # Extracting lspcu information
    lscpu = {}
    output = output_lines('LANG=en_US.UTF-8 lscpu')

    for line in output:
        if ':' in line:
            item, value = line.split(':', 1)
            lscpu[item.strip(':')] = value.strip()

    # Extracting lspcu -x information
    # Use hexadecimal masks for CPU sets
    lscpux = {}
    output = output_lines('LANG=en_US.UTF-8 lscpu -x')

    for line in output:
        if ':' in line:
            item, value = line.split(':', 1)
            lscpux[item.strip(':')] = value.strip()

    hw_lst.append(("cpu", "physical", "number", int(lscpu["Socket(s)"])))

    with contextlib.suppress(IOError):
        value = from_file("/sys/devices/system/cpu/smt/control")
        hw_lst.append(("cpu", "physical", "smt", value))

    for processor in range(int(lscpu["Socket(s)"])):
        ptag = "physical_{}".format(processor)
        try:
            value = from_file("/sys/devices/system/cpu/cpufreq/boost")
        except IOError:
            pass
        else:
            value = 'enabled' if value == '1' else 'disabled'
            hw_lst.append(('cpu', ptag, 'boost', value))

        for (t_key, d_key, conv) in [('vendor', 'Vendor ID', None),
                                     ('product', 'Model name', None),
                                     ('cores', 'Core(s) per socket', int),
                                     ('threads', None, None),
                                     ('family', 'CPU family', int),
                                     ('model', 'Model', _maybe_int),
                                     ('stepping', 'Stepping', _maybe_int),
                                     ('architecture', 'Architecture', None),
                                     ('l1d cache', 'L1d cache', None),
                                     ('l1i cache', 'L1i cache', None),
                                     ('l2 cache', 'L2 cache', None),
                                     ('l3 cache', 'L3 cache', None),
                                     ('min_Mhz', 'CPU min MHz', float),
                                     ('max_Mhz', 'CPU max MHz', float),
                                     ('current_Mhz', 'CPU MHz', float),
                                     ('flags', 'Flags', None),
                                     ('threads_per_core', 'Thread(s) per core',
                                      int)]:
            value = None
            if d_key in lscpu:
                value = lscpu[d_key]
                if conv:
                    value = conv(value)
            elif t_key == 'threads':
                value = (int(lscpu.get('Thread(s) per core', 1))
                         * int(lscpu.get('Core(s) per socket', 1)))
            if value is not None:
                hw_lst.append(('cpu', ptag, t_key, value))

    hw_lst.append(('cpu', 'logical', 'number', int(lscpu['CPU(s)'])))
    # Governors could be different on logical cpus
    for cpu in range(int(lscpu['CPU(s)'])):
        ltag = "logical_{}".format(cpu)

        governor = _get_governor(cpu)
        if governor is not None:
            hw_lst.append(('cpu', ltag, "governor", governor))

    # Extracting numa nodes
    try:
        hw_lst.append(('numa', 'nodes', 'count', int(lscpu['NUMA node(s)'])))
    except KeyError:
        pass

    # Allow for sparse numa nodes.
    numa_nodes = []
    for key in lscpux:
        match = re.match(r"NUMA node(\d+) CPU\(s\)", key)
        if match:
            numa_nodes.append((key, int(match.groups()[0])))
    # NOTE(tonyb): Explicitly sort the list as prior to python 3.7? keys() did
    # not have a predictable ordering and there maybe consumers of hw_lst rely
    # on that.
    numa_nodes.sort(key=lambda t: t[1])
    for (key, node_id) in numa_nodes:
        ntag = 'node_{}'.format(node_id)
        cpus = lscpu[key]
        # lscpu -x provides the cpu mask
        cpu_mask = lscpux[key]
        total_cpus = 0
        min_cpu = None
        max_cpu = None

        # It's possible to have a NUMA node without any CPUs
        if cpus:
            for item in cpus.split(','):
                # lscpu report numa nodes like 0-5,48-53
                if "-" in item:
                    max_cpu = int(item.split("-")[1])
                    min_cpu = int(item.split("-")[0])
                    total_cpus = total_cpus + max_cpu - min_cpu + 1
                else:
                    # or like 0,1
                    # As we don't have dashes, there is only one core to count
                    total_cpus = total_cpus + 1

        # total_cpus = 12 for "0-5,48-53"
        hw_lst.append(('numa', ntag, 'cpu_count', total_cpus))
        hw_lst.append(('numa', ntag, 'cpu_mask', cpu_mask))


def modprobe(module):
    """Load a kernel module using modprobe."""
    status, _ = cmd('modprobe %s' % module)
    if status == 0:
        sys.stderr.write('Info: Probing %s failed\n' % module)


def detect_auxv(hw_lst):
    new_env = os.environ.copy()
    new_env["LD_SHOW_AUXV"] = "1"

    auxv_cmd = Popen("/bin/true", env=new_env, stdout=subprocess.PIPE)
    stdout, err = auxv_cmd.communicate()
    if err is not None:
        sys.stderr.write("Info: AUXV output received\n")
        return

    auxv = dict()
    supported_flags = AUXV_FLAGS + AUXV_OPT_FLAGS
    for line in stdout.decode("utf-8").splitlines():
        k, v = [i.strip() for i in line.split(":")]
        if k in supported_flags:
            auxv[k[3:].lower()] = v
            hw_lst.append(('hw', 'auxv', k[3:].lower(), v))


def parse_ahci(hrdw, words):
    if len(words) < 4:
        return
    if "flags" in words[2]:
        flags = ""
        for flag in sorted(words[3:]):
            flags = "%s %s" % (flags, flag)
        hrdw.append(('ahci', words[1], "flags", flags.strip()))


def parse_dmesg(hrdw):
    """Run dmesg and parse the output."""

    _, output = cmd("dmesg")
    for line in output.split('\n'):
        words = line.strip().split(" ")

        if words[0].startswith("[") and words[0].endswith("]"):
            words = words[1:]

        if not words:
            continue

        if "ahci" in words[0]:
            parse_ahci(hrdw, words)
