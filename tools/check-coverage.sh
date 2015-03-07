#!/bin/sh
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

level=$1
shift
dir=$2
shift

cd "$dir"
python setup.py testr --coverage --testr-args="$*"

cover=$(fgrep "'pc_cov'" cover/index.html | sed 's/.*>\([0-9]*\)%..*/\1/')

echo "Coverage: ${cover}%"

if [ "$cover" -lt "$level" ]; then
    echo "Expecting ${level}%. Aborting."
    exit 1
fi

# check-coverage.sh ends here
