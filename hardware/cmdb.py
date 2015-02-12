#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

'''
'''

import errno
import logging
import pprint
import shutil

# generate must be exposed for eval to work correctly in load_cmdb
from hardware.generate import is_included, generate  # noqa

LOG = logging.getLogger('hardware.cmdb')


class CmdbError(Exception):
    pass


def cmdb_filename(cfg_dir, name):
    'Return the cmdb filename.'
    return cfg_dir + name + '.cmdb'


def load_cmdb(cfg_dir, name):
    'Load the cmdb.'
    filename = cmdb_filename(cfg_dir, name)
    try:
        if "generate(" in open(filename).read(20):
            shutil.copy2(filename, filename + ".orig")
        return eval(open(filename).read(-1))
    except IOError as xcpt:
        if xcpt.errno != errno.ENOENT:
            LOG.error("exception while processing CMDB %s" % str(xcpt))
        return None


def save_cmdb(cfg_dir, name, cmdb):
    'Save the cmdb.'
    filename = cmdb_filename(cfg_dir, name)
    try:
        pprint.pprint(cmdb, stream=open(filename, 'w'))
    except IOError as xcpt:
        LOG.error("exception while saving CMDB %s" % str(xcpt))


def update_cmdb(cmdb, var, pref, forced_find):
    '''Handle CMDB settings if present.

CMDB is updated with var. var is also augmented with the cmdb entry
found.
'''

    def update_entry(entry, cmdb, idx):
        'Update var using a cmdb entry and save the full cmdb on disk.'
        entry.update(var)
        var.update(entry)
        var['used'] = 1
        cmdb[idx] = var

    # First pass to lookup if the var is already in the database
    # and if this is the case, reuse the entry.
    idx = 0
    for entry in cmdb:
        if is_included(pref, entry):
            update_entry(entry, cmdb, idx)
            break
        idx += 1
    else:
        # not looking for $$ type matches
        if not forced_find:
            # Second pass, find a not used entry.
            idx = 0
            for entry in cmdb:
                if 'used' not in entry:
                    update_entry(entry, cmdb, idx)
                    break
                idx += 1
            else:
                raise CmdbError("No more entry in the CMDB, aborting.")
        else:
            raise CmdbError("No entry matched in the CMDB, aborting.")
    return True

# cmdb.py ends here
