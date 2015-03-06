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

# check that the pylint score is higher than the first argument.
#
# usage: check-pylint-score.sh <score> <pylint args>

level=$1
shift
tmpfile=$(mktemp)

cleanup() {
    rm -f $tmpfile
}

trap cleanup 0

pylint "$@" | tee $tmpfile

score=$(sed -n 's@.*rated at \([0-9.]*\)/10.*@\1@p' < $tmpfile)

if [ "$(echo "$score >= $level" | bc)" -eq 1 ]; then
    exit 0
else
    exit 1
fi

# check-pylint-score.sh ends here
