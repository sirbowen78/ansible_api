from helper.awx_api import Tower
from getpass import getpass
from pprint import pprint

"""
Remove the resources
"""
awx_server = input("AWX server address: ")
username = input(f"Username for {awx_server}: ")
password = getpass()

tower_config = dict(
    server_addr=awx_server,
    username=username,
    password=password
)
tower = Tower(**tower_config)

# remove job templates - access_control_list
jt_id = tower.find_resource_id(resource="job_templates", name="access_control_list")
if jt_id.get("found"):
    jt_id = jt_id.get("result")
    job_templates_config = dict(
        resource_id=jt_id,
        resource="job_templates"
    )
    r = tower.delete_request(**job_templates_config)
    pprint(r)
else:
    print(jt_id.get("result"))

# remove project - lab_project
proj_id = tower.find_resource_id(resource="projects", name="lab_project")
if proj_id.get("found"):
    proj_id = proj_id.get("result")
    proj_config = dict(
        resource_id=proj_id,
        resource="projects"
    )
    r = tower.delete_request(**proj_config)
    pprint(r)
else:
    print(proj_id.get("result"))

# remove credentials - fw03
cred_id = tower.find_resource_id(resource="credentials", name="fw03")
if cred_id.get("found"):
    cred_id = cred_id.get("result")
    cred_config = dict(
        resource_id=cred_id,
        resource="credentials"
    )
    r = tower.delete_request(**cred_config)
    pprint(r)
else:
    print(cred_id.get("result"))

# delete hosts - fw03
host_id = tower.find_resource_id(resource="hosts", name="fw03")
if host_id.get("found"):
    host_id = host_id.get("result")
    host_config = dict(
        resource_id=host_id,
        resource="hosts"
    )
    r = tower.delete_request(**host_config)
    pprint(r)
else:
    print(host_id.get("result"))

# delete inventory - firewalls
inv_id = tower.find_resource_id(resource="inventories", name="firewalls")
if inv_id.get("found"):
    inv_id = inv_id.get("result")
    inv_config = dict(
        resource_id=inv_id,
        resource="inventories"
    )
    r = tower.delete_request(**inv_config)
    pprint(r)
else:
    print(inv_id.get("result"))

# delete organizations - cyruslab1
org_id = tower.find_resource_id(resource="organizations", name="cyruslab1")
if org_id.get("found"):
    org_id = org_id.get("result")
    org_config = dict(
        resource_id=org_id,
        resource="organizations"
    )
    r = tower.delete_request(**org_config)
    pprint(r)
else:
    print(org_id.get("result"))