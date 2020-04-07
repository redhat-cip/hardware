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

'''Functions to match according to a requirement specification.'''

import ipaddress
import logging
import re
import sys


LOG = logging.getLogger('hardware.matcher')


def _adder(array, index, value):
    'Auxiliary function to add a value to an array.'
    array[index] = value


def _appender(array, index, value):
    'Auxiliary function to append a value to an array.'
    try:
        array[index].append(value)
    except KeyError:
        array[index] = [value, ]


def _range(elt, minval, maxval):
    'Helper for match_spec.'
    return float(elt) >= float(minval) and float(elt) <= float(maxval)


def _gt(left, right):
    'Helper for match_spec.'
    return float(left) > float(right)


def _ge(left, right):
    'Helper for match_spec.'
    return float(left) >= float(right)


def _lt(left, right):
    'Helper for match_spec.'
    return float(left) < float(right)


def _le(left, right):
    'Helper for match_spec.'
    return float(left) <= float(right)


def _not(_, right):
    'Helper for match_spec.'
    return not right


def _and(_, left, right):
    'Helper for match_spec.'
    return left and right


def _or(_, left, right):
    'Helper for match_spec.'
    return left or right


def _network(left, right):
    'Helper for match_spec.'
    return ipaddress.IPv4Address(left) in ipaddress.IPv4Network(right)


def _regexp(left, right):
    'Helper for match_spec.'
    return re.search(right, left) is not None


def _in(elt, *lst):
    'Helper for match_spec.'
    return elt in lst


_FUNC_REGEXP = re.compile(r'^([^(]+)'          # function name
                          r'\(\s*([^,]+)'      # first argument
                          r'(?:\s*,\s*(.+))?'  # remaining optional arguments
                          r'\)$')              # last parenthesis


def _call_func(func, implicit, res):
    'Helper function for extract_result and match_spec'
    args = [implicit, res.group(2)]
    # split the optional arguments if we have some
    if res.group(3):
        args = args + re.split(r'\s*,\s*', res.group(3))
    # remove strings delimiters
    args = [x.strip('\'"') for x in args]
    # call function
    args = [_extract_result(implicit, x) for x in args]
    return func(*args)


def _extract_result(implicit, expr):
    'Helper function for match_spec'
    res = _FUNC_REGEXP.search(expr)
    if res:
        func_name = '_' + res.group(1)
        if func_name in globals():
            return _call_func(globals()[func_name], implicit, res)

    return expr


def match_spec(spec, lines, arr, adder=_adder):
    'Match a line according to a spec and store variables in <var>.'
    # match a line without variable
    for idx in range(len(lines)):
        if lines[idx] == spec:
            res = lines[idx]
            del lines[idx]
            return res
    # match a line with a variable, a function or both
    for lidx in range(len(lines)):
        line = lines[lidx]
        varidx = []
        for idx in range(4):
            # try to split the variable and function parts if we have both
            if spec[idx][0] == '$':
                parts = spec[idx].split('=')
                if len(parts) == 2:
                    var, func = parts
                    matched = False
                else:
                    var = func = spec[idx]
            else:
                var = func = spec[idx]
            # Match a function
            if func[-1] == ')':
                res = _FUNC_REGEXP.search(func)
                if res:
                    func_name = '_' + res.group(1)
                    if func_name in globals():
                        if not _call_func(globals()[func_name],
                                          line[idx], res):
                            if var == func:
                                break
                        else:
                            if var == func:
                                continue
                            matched = True
                    else:
                        if var == func:
                            break
            # Match a variable
            if ((var == func) or (var != func and matched)) and var[0] == '$':
                if adder == _adder and var[1:] in arr:
                    if arr[var[1:]] != line[idx]:
                        break
                varidx.append((idx, var[1:]))
            # Match the full string
            elif line[idx] != spec[idx]:
                break
        else:
            for i, var in varidx:
                adder(arr, var, line[i])
            res = lines[lidx]
            del lines[lidx]
            return res
    return False


def match_all(lines, specs, arr, arr2, debug=False, level=0):
    '''Match all lines according to a spec.

Store variables starting with a $ in <arr>. Variables starting with
2 $ like $$vda are stored in arr and arr2.
'''
    # Work on a copy of lines to avoid changing the real lines because
    # match_spec removes the matched line to not match it again on next
    # calls.
    lines = list(lines)
    specs = list(specs)
    copy_arr = dict(arr)
    points = []
    # Prevent infinit loops
    if level == 50:
        return False
    # Match lines using specs
    while specs:
        copy_specs = list(specs)
        spec = specs.pop(0)
        line = match_spec(spec, lines, arr)
        if debug:
            sys.stderr.write('match_spec: %s %s\n' % (line, spec))
        # No match
        if not line:
            # Backtrack on the backtracking points
            while points:
                lines, specs, new_arr = points.pop()
                if debug:
                    sys.stderr.write('retrying with: %s\n' %
                                     (new_arr,))
                if match_all(lines, specs, new_arr, arr2, debug, level + 1):
                    # Copy arr back
                    for k in new_arr:
                        arr[k] = new_arr[k]
                    if debug:
                        sys.stderr.write('success: %d\n' % level)
                    return True
            if level == 0 and debug:
                sys.stderr.write('spec: %s not matched\n' % str(spec))
            return False
        else:
            # Store backtraking points when we find a new variable
            if arr != copy_arr:
                copy_lines = list(lines)
                # Put the matching line at the end of the lines
                copy_lines.append(line)
                points.append((copy_lines, copy_specs, copy_arr))
                copy_arr = dict(arr)
                if debug:
                    sys.stderr.write('new var: %s %s\n' % (arr, line))

    # Manage $$ variables
    for key in list(arr):
        if key[0] == '$':
            nkey = key[1:]
            arr[nkey] = arr[key]
            arr2[nkey] = arr[key]
            del arr[key]
    return True


def match_multiple(lines, spec, arr):
    'Use spec to find all the matching lines and gather variables.'
    ret = False
    lines = list(lines)
    while match_spec(spec, lines, arr, adder=_appender):
        ret = True
    return ret


def generate_filename_and_macs(items):
    '''Generate a file name for a hardware using DMI information.

(product name and version) then if the DMI serial number is
available we use it unless we lookup the first mac address.
As a result, we do have a filename like :

<dmi_product_name>-<dmi_product_version>-{dmi_serial_num|mac_address}
'''

    # Duplicate items as it will be modified by match_* functions
    hw_items = list(items)
    sysvars = {'sysname': ''}

    if match_spec(('system', 'product', 'vendor', '$sysprodvendor'),
                  hw_items, sysvars):
        sysvars['sysname'] += (re.sub(r'\W+', '',
                                      sysvars['sysprodvendor']) + '-')

    if match_spec(('system', 'product', 'name', '$sysprodname'),
                  hw_items, sysvars):
        sysvars['sysname'] = re.sub(r'\W+', '', sysvars['sysprodname']) + '-'

    # Let's use any existing DMI serial number or take the first mac address
    if match_spec(('system', 'product', 'serial', '$sysserial'),
                  hw_items, sysvars):
        sysvars['sysname'] += re.sub(r'\W+', '', sysvars['sysserial']) + '-'

    # we always need to have the mac addresses for pxemngr
    if match_multiple(hw_items,
                      ('network', '$eth', 'serial', '$serial'),
                      sysvars):
        sysvars['sysname'] += sysvars['serial'][0].replace(':', '-')
    else:
        LOG.warning('unable to detect network macs')

    return sysvars

# matcher.py ends here
