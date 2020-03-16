from helper.awx_api import Tower, SSH_INPUTS
from getpass import getpass
from pprint import pprint

# get awx information
awx_server = input("Address of awx server: ")
username = input(f"Username of {awx_server}: ")
password = getpass(f"Password of {username}@{awx_server}: ")

# awx/tower configuration at minimum.
tower_config = dict(
    server_addr=awx_server,
    username=username,
    password=password
)

# create an ansible awx/tower instance with supplied tower configuration
tower = Tower(**tower_config)

# create an organization
org_response = tower.create_org(name="lab_env",
                                desc="This is an example on how to create an org",
                                max_hosts=100)
# response from ansible awx
pprint(org_response)

# create a credential to store cisco asa firewall credentials.
asa = input("Hostname and ip address of cisco asa (separate in commas): ").split(",")
asa_user = input(f"Username of {asa[0]}: ")
asa_pass = getpass()
asa_ssh_values = asa_user, asa_pass, "enable", asa_user, asa_pass
# use the default credential_type: machine
cred_config = dict(
    name=asa[0],
    desc="-".join(asa),
    # find the organization id by supplying name.
    org_id=tower.find_resource_id(resource="organizations", name="lab_env").get("result"),
    inputs=dict(
        zip(SSH_INPUTS, asa_ssh_values)
    )
)
cred_creation_response = tower.create_credential(**cred_config)
pprint(cred_creation_response)
