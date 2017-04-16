# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import sys

from hardware.cardiff import cardiff
from hardware.cardiff import compare_sets
from hardware.cardiff import utils


def get_facts(client):
    nodes = client.node.list(detail=True)
    # cardiff expects data in the form of a list of nodes
    # where each node is represented by a list of tuples
    # with each tuple representing a fact about the node
    try:
        facts = [[tuple(fact) for fact in node.extra['edeploy_facts']] for
                 node in nodes]
    except KeyError:
        err_msg = ("You must run introspection on the nodes before "
                   "running this tool.\n")
        sys.stderr.write(err_msg)
        sys.exit(1)
    return facts


def get_ironic_client(args):
    try:
        from ironicclient import client
        from ironicclient.exc import AmbiguousAuthSystem
    except ImportError:
        err_msg = ("The python-ironicclient module is not installed or not "
                   "on the python path.\nThis module is required to use this "
                   "tool.\n")
        sys.stderr.write(err_msg)
        sys.exit(2)

    # This section gets an ironic client.
    # TODO(trown): refactor to include error handling, and inputing
    #              credentials on the command line. Might also want
    #              getpass for password input.
    kwargs = {'os_password': os.environ.get('OS_PASSWORD'),
              'os_username': os.environ.get('OS_USERNAME'),
              'os_tenant_name': os.environ.get('OS_TENANT_NAME'),
              'os_auth_url': os.environ.get('OS_AUTH_URL')}
    try:
        ironic = client.get_client(1, **kwargs)
    except AmbiguousAuthSystem:
        err_msg = ("You must source a keystonerc file in order to use "
                   "this tool.\n")
        sys.stderr.write(err_msg)
        sys.exit(3)

    return ironic


def print_report(args, facts):
    # The global_params are only used for a single output_dir key.
    # The output_dir key is not currently useful for this use case.
    # We could probably refactor hardware to make it a kwarg, so we don't need
    # to pass an empty dictionary.
    global_params = {}
    # The detail dictionary has three keys (group, category, item). This is
    # only used in the case that we have the print_level set to
    # utils.Levels.DETAIL
    # This is not currently used, but required by the architecture of hardware.
    detail = {'group': '', 'category': '', 'item': ''}
    # We have a different kernel cmdline for each system, so we have to ignore
    # system to get groups that have more than one system.
    ignore_list = 'system'
    # unique_id can either be 'serial' or 'uuid', in virtual environments
    # 'serial' is not reported so we default to 'uuid'
    unique_id = args.unique_id
    # Extract the host list from the data to get the initial list of hosts.
    systems_groups = []
    systems_groups.append(utils.get_hosts_list(facts, unique_id))
    # Print the group information
    if args.groups or args.full:
        compare_sets.print_systems_groups(systems_groups)

    # Print the category information
    if args.categories or args.full:
        cardiff.group_systems(global_params, facts, unique_id,
                              systems_groups, ignore_list)

    # Print the outlier information
    if args.outliers or args.full:
        cardiff.compare_performance(facts, unique_id, systems_groups, detail)


def main():
    parser = argparse.ArgumentParser(description='Consume benchmark data '
                                                 'from Ironic.')
    parser.add_argument('-f', '--full', action='store_true',
                        help='Print the full report.')
    parser.add_argument('-g', '--groups', action='store_true',
                        help='Print the groupings by similar hardware.')
    parser.add_argument('-c', '--categories', action='store_true',
                        help='Print the report for each category.')
    parser.add_argument('-o', '--outliers', action='store_true',
                        help='Print the report showing outliers.')
    parser.add_argument('-u', '--unique-id', dest='unique_id',
                        action='store', default='uuid',
                        choices=['uuid', 'serial'],
                        help='Unique key to identify the nodes by.')
    args = parser.parse_args()

    # If we did not pass any print arguments, print the help and exit
    if not (args.groups or args.categories or args.outliers or args.full):
        print("\nYou did not specify anything to print.\n")
        parser.print_help()
        sys.exit(4)

    ironic = get_ironic_client(args)
    facts = get_facts(ironic)

    print_report(args, facts)

if __name__ == '__main__':
    main()
