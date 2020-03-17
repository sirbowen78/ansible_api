from helper.awx_api import Tower
from getpass import getpass
from pprint import pprint

# Get AWX server information
awx_server = input("Address of Ansible AWX: ")
username = input(f"Username of {awx_server}: ")
password = getpass()

tower_config = dict(
    server_addr=awx_server,
    username=username,
    password=password
)

# create a Tower instance
tower = Tower(**tower_config)

# create a cisco asa inventory to store all cisco asa hosts into this inventory.
inv_config = dict(
    name="cisco_asa",  # name of the inventory
    desc="cisco asa inventory",  # optional description of the inventory
    # Get the organization id by searching for the organization name.
    org=tower.find_resource_id(resource="organizations", name="lab_env").get("result"),
    inv_vars=dict(ansible_network_os="asa")  # Since it is a cisco asa inventory, specify the network os as asa.
)

inv_response = tower.create_inv(**inv_config)
pprint(inv_response)

# create a host in the created inventory - cisco_asa
cisco_asa = input("Hostname and ip address of Cisco ASA (separate by commas): ").split(",")
inv_host_config = dict(
    name=cisco_asa[0],  # hostname of the host, either a resolvable hostname or ip address.
    desc="fw03 ASAv version 9.2",  # optional description of the inventory.
    inv_id=tower.find_resource_id(resource="inventories", name="cisco_asa").get("result"),  # inventory id.
    # specify additional variables, in this case is an ip address since hostname is unresolvable.
    host_vars=dict(ansible_host=cisco_asa[1])
)
inv_host_response = tower.create_inv_host(**inv_host_config)
pprint(inv_host_response)
