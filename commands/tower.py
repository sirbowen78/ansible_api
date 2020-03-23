"""
An attempt to construct a cli module for ansible tower/awx.
I would need a filter in the command line in order to get useful information from json.
Currently I am building it up bit by bit.
"""
from helper.awx_api import Tower
from argparse import ArgumentParser
from getpass import getpass
import sys

parser = ArgumentParser(description="This is a script that helps in operating Ansible AWX.",
                        usage="python tower.py -u username --host 192.168.1.100 --resource projects lab -p")
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
parser.add_argument("--create", action="store_true", dest="create")
parser.add_argument("--type", type=str, dest="type")
parser.add_argument("--name", type=str, dest="name")
parser.add_argument("--desc", type=str, dest="desc")
parser.add_argument("--max-hosts", type=int, dest="max_hosts")
parser.add_argument("--del", action="store_true", dest="delete")

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

    if args.resource_info and len(args.resource_info) == 2:
        # if --resource is used check if there are two arguments.
        resource = args.resource_info[0]
        name = args.resource_info[1]
        resource_id = tower.find_resource_id(resource=resource, name=name)
        if resource_id.get("found"):
            r = tower.get_resource_info(resource=resource, resource_id=resource_id.get("result"))
            print(r.json())
        else:
            print(resource_id)
            sys.exit(1)
    elif args.type.lower() == "organizations":
        if args.create:
            payload = dict(
                name=args.name,
                desc=args.desc if args.desc else "",
                max_hosts=args.max_hosts if args.max_hosts else 0
            )
            print(tower.create_org(**payload))
        elif args.delete:
            resource_id = tower.find_resource_id(resource=args.type.lower(),
                                                 name=args.name)
            if resource_id.get("found"):
                r = tower.delete_request(resource_id=resource_id.get("result"),
                                         resource=args.type.lower())
                print(r)
            else:
                print(resource_id)
        else:
            resource_id = tower.find_resource_id(resource=args.type.lower(),
                                                 name=args.name)
            if resource_id.get("found"):
                r = tower.get_resource_info(resource=args.type.lower(),
                                            resource_id=resource_id.get("result"))
                print(r.json())
            else:
                print(resource_id)
    else:
        print("--resource arguments insufficient, or the resource is currently not implemented in this version.")
        sys.exit(1)
else:
    print("Password is incorrect or not supplied.")
    sys.exit(1)
