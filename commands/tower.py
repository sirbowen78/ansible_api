"""
An attempt to construct a cli module for ansible tower/awx
"""
from helper.awx_api import Tower
from argparse import ArgumentParser
from getpass import getpass
import sys

parser = ArgumentParser(description="This is a script that helps in operating Ansible AWX.")
parser.add_argument("-u", "--user", type=str, dest="username", required=True)
parser.add_argument("-p", "--pass", dest="password", required=True, action="store_true")
parser.add_argument("--host", type=str, dest="server_addr", required=True)
parser.add_argument("--port", type=int, dest="server_port")
parser.add_argument("--verifyssl", action="store_true", dest="verify_ssl")

# never use type=list if you are expecting more than one args, it will make your strings into list of chars.
parser.add_argument("--resource",
                    nargs="+",
                    dest="resource_info",
                    help="Resource type and name")

args = parser.parse_args()

if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)
if args.password:
    password = getpass()
    tower_config = dict(
        username=args.username,
        password=password,
        server_addr=args.server_addr,
        server_port=args.server_port if args.server_port else 8052,
        verify_ssl=True if args.verify_ssl else False
    )
    tower = Tower(**tower_config)

    if args.resource_info:
        resource = args.resource_info[0]
        name = args.resource_info[1]
        resource_id = tower.find_resource_id(resource=resource, name=name)
        if resource_id.get("found"):
            r = tower.get_resource_info(resource=resource, resource_id=resource_id.get("result"))
            print(r.json())
        else:
            print(resource_id)
            sys.exit(1)
