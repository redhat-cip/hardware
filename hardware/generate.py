#
# Copyright (C) 2013-2014 eNovance SAS <licensing@enovance.com>
#
# Author: Frederic Lepied <frederic.lepied@enovance.com>
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

''' Generate range of values according to a model.
'''

import re


def _generate_range(num_range):
    'Generate number for range specified like 10-12:20-30.'
    for rang in num_range.split(':'):
        boundaries = rang.split('-')
        if len(boundaries) == 2:
            try:
                if boundaries[0][0] == '0':
                    fmt = '%%0%dd' % len(boundaries[0])
                else:
                    fmt = '%d'
                start = int(boundaries[0])
                stop = int(boundaries[1]) + 1
                if stop > start:
                    step = 1
                else:
                    step = -1
                    stop = stop - 2
                for res in range(start, stop, step):
                    yield fmt % res
            except ValueError:
                yield num_range
        else:
            yield num_range


_RANGE_REGEXP = re.compile(r'^(.*?)([0-9]+-[0-9]+(:([0-9]+-[0-9]+))*)(.*)$')
_IPV4_RANGE_REGEXP = re.compile(r'^[0-9:\-.]+$')


def _generate_values(pattern):
    '''Create a generator for ranges of IPv4 or names.

Ranges are defined like 10-12:15-18 or from a list of entries.
'''
    if isinstance(pattern, list) or isinstance(pattern, tuple):
        for elt in pattern:
            yield elt
    else:
        parts = pattern.split('.')
        if (_IPV4_RANGE_REGEXP.search(pattern) and
            len(parts) == 4 and (pattern.find(':') != -1 or
                                 pattern.find('-') != -1)):
            gens = [_generate_range(part) for part in parts]
            for part0 in gens[0]:
                for part1 in gens[1]:
                    for part2 in gens[2]:
                        for part3 in gens[3]:
                            yield '.'.join((part0, part1, part2, part3))
                        gens[3] = _generate_range(parts[3])
                    gens[2] = _generate_range(parts[2])
                gens[1] = _generate_range(parts[1])
        else:
            res = _RANGE_REGEXP.search(pattern)
            if res:
                head = res.group(1)
                foot = res.group(res.lastindex)
                for num in _generate_range(res.group(2)):
                    yield head + num + foot
            else:
                for _ in xrange(16387064):
                    yield pattern


_STRING_TYPE = type('')


def generate(model):
    '''Generate a list of dict according to a model.

Ipv4 ranges are handled by _generate_ip.
'''
    # Safe guard for models without ranges
    for value in model.values():
        if type(value) != _STRING_TYPE:
            break
        elif _RANGE_REGEXP.search(value):
            break
    else:
        return [model]
    # The model has a range starting from here
    result = []
    copy = {}
    copy.update(model)
    for key, value in copy.items():
        copy[key] = _generate_values(value)
    while True:
        try:
            entry = {}
            for key in copy:
                entry[key] = copy[key].next()
            result.append(entry)
        except StopIteration:
            break
    return result


def is_included(dict1, dict2):
    'Test if dict1 is included in dict2.'
    for key, value in dict1.items():
        try:
            if dict2[key] != value:
                return False
        except KeyError:
            return False
    return True

# generate.py ends here
