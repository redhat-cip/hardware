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

"""Generate range of values according to a model."""

import re
import types


_PREFIX = None


def _generate_range(num_range):
    """Generate number for range specified like 10-12:20-30."""

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


def _generate_values(pattern, prefix=_PREFIX):
    """Create a generator for ranges of IPv4 or names.

    Ranges are defined like 10-12:15-18 or from a list of entries.
    """

    if isinstance(pattern, list):
        for elt in pattern:
            yield elt
    elif isinstance(pattern, dict):
        pattern_copy = pattern.copy()
        for key, entry in pattern_copy.items():
            if not prefix or key[0] == prefix:
                if prefix:
                    pattern[key[1:]] = _generate_values(entry)
                else:
                    pattern[key] = _generate_values(entry)
                del pattern[key]
            else:
                pattern[key] = entry
        while True:
            yield pattern
    elif isinstance(pattern, str):
        parts = pattern.split('.')
        if (_IPV4_RANGE_REGEXP.search(pattern)
                and len(parts) == 4
                and (pattern.find(':') != -1 or pattern.find('-') != -1)):
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
                for _ in range(16387064):
                    yield pattern
    else:
        for _ in range(16387064):
            yield pattern


STRING_TYPE = type('')
GENERATOR_TYPE = types.GeneratorType


def _call_nexts(model):
    """Walk through the model to call next() on all generators."""

    entry = {}
    generated = False
    for key in model.keys():
        if isinstance(model[key], GENERATOR_TYPE):
            entry[key] = next(model[key])
            generated = True
        elif isinstance(model[key], dict):
            entry[key] = _call_nexts(model[key])
        else:
            entry[key] = model[key]
    # We can have nested generators so call again
    if generated:
        return _call_nexts(entry)

    return entry


def generate(model, prefix=_PREFIX):
    """Generate a list of dict according to a model.

    Ipv4 ranges are handled by _generate_ip.
    """

    # Safe guard for models without ranges
    for value in model.values():
        if type(value) != STRING_TYPE:
            break
        elif _RANGE_REGEXP.search(value):
            break
    else:
        return [model]
    # The model has at least one range starting from here
    result = []
    yielded = {}
    yielded.update(model)
    yielded_copy = yielded.copy()
    for key, value in yielded_copy.items():
        if not prefix or key[0] == prefix:
            if prefix:
                yielded[key[1:]] = _generate_values(value, prefix)
                del yielded[key]
            else:
                if isinstance(value, str) and not _RANGE_REGEXP.search(value):
                    yielded[key] = value
                else:
                    yielded[key] = _generate_values(value, prefix)
        else:
            yielded[key] = value
    while True:
        try:
            result.append(_call_nexts(yielded))
        except StopIteration:
            break
    return result


def generate_dict(model, prefix=_PREFIX):
    """Generate a dict with ranges in keys and values."""

    result = {}
    for thekey in model.keys():
        if not prefix or thekey[0] == prefix:
            if prefix:
                key = thekey[1:]
            else:
                key = thekey
            for newkey, val in zip(list(_generate_values(key, prefix)),
                                   generate(model[thekey], prefix)):
                try:
                    result[newkey] = merge(result[newkey], val)
                except KeyError:
                    result[newkey] = val
        else:
            key = thekey
            try:
                result[key] = merge(result[key], model[key])
            except KeyError:
                result[key] = model[key]
    return result


def is_included(dict1, dict2):
    """Test if dict1 is included in dict2."""

    for key, value in dict1.items():
        try:
            if dict2[key] != value:
                return False
        except KeyError:
            return False
    return True


def merge(user, default):
    """Merge 2 data structures."""

    for key, val in default.items():
        if key not in user:
            user[key] = val
        else:
            if isinstance(user[key], dict) and isinstance(val, dict):
                user[key] = merge(user[key], val)
            elif isinstance(user[key], list) and isinstance(val, list):
                user[key] = user[key] + val
            else:
                user[key] = val
    return user
