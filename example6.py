from helper.awx_api import Tower, SSH_INPUTS
from getpass import getpass
from pprint import pprint

awx_server = input("AWX server address: ")
username = input(f"Username for {awx_server}: ")
password = getpass()

tower_config = dict(
    server_addr=awx_server,
    username=username,
    password=password
)
tower = Tower(**tower_config)

# create a new organization
org_name = input("Give your organization a name: ")
desc = input(f"Describe {org_name}: ")
max_hosts = int(input(f"Define max_host for {org_name} (valid integer only): "))
org_config = dict(
    name=org_name,
    desc=desc,
    max_hosts=max_hosts
)
org_response = tower.create_org(**org_config)
pprint(org_response)

# create inventory
inv_name = input("Give your inventory a name: ")
inv_desc = input("Describe your inventory: ")
inv_os = input("OS type of inventory such as asa, ios, windows, linux: ")
inv_config = dict(
    name=inv_name,
    desc=inv_desc,
    inv_vars=dict(
        ansible_network_os=inv_os
    )
)
inv_response = tower.create_inv(**inv_config)
pprint(inv_response)

# create a host in inventory
inv_host_info = input("Hostname and ip address separate them by comma (hostname, ipaddress): ").split(",")
inv_host_desc = input(f"Describe {inv_host_info[0]}: ")
inv_host_config = dict(
    name=inv_host_info[0],
    desc=inv_host_desc,
    inv_id=tower.find_resource_id(resource="inventories", name=inv_name).get("result"),
    host_vars=dict(
        ansible_host=inv_host_info[1]
    )
)
inv_host_response = tower.create_inv_host(**inv_host_config)
pprint(inv_host_response)

# create a project
proj_name = input("Give your project a name: ")
proj_desc = input("Describe your project: ")
proj_local_path = input("Project sub directory: ")
org_name = input("Attach project to which organization: ")
org_id = tower.find_resource_id(resource="organizations", name=org_name).get("result")
proj_config = dict(
    name=proj_name,
    desc=proj_desc,
    local_path=proj_local_path,
    org_id=org_id
)
proj_response = tower.create_project(**proj_config)
pprint(proj_response)

# create job template
proj_template_name = input("Give job template a name: ")
proj_template_desc = input("Describe the template: ")
proj_template_playbook = input("plabook name: ")
proj_template_config = dict(
    name=proj_template_name,
    desc=proj_template_desc,
    inv_id=tower.find_resource_id(resource="inventories", name=inv_name).get("result"),
    project_id=tower.find_resource_id(resource="projects", name=proj_name).get("result"),
    playbook=proj_template_playbook,
    verbosity="debug",
    diff_mode=True,
    become_enabled=True
)

proj_template_response = tower.create_job_template(**proj_template_config)
pprint(proj_template_response)

# create credential for project template
credential_name = input("Credential name: ")
host_username = input(f"Username for {inv_host_info[0]}: ")
host_password = getpass()
job_template_credential_config = dict(
    job_template_id=proj_template_name,
    name=inv_host_info[0],
    org_id=org_name,
    credential_type="ssh",
    inputs=dict(
        zip(SSH_INPUTS, (host_username, host_password, "enable", host_username, host_password))
    )
)
jt_cred_response = tower.create_job_templates_cred(**job_template_credential_config)
pprint(jt_cred_response)
