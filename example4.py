"""
To create a project, you need to have an available sub directory that hosts your playbooks.
in the Ansible AWX installation configuration the base path of projects is /var/lib/awx/projects.
So in order to create a new project a new project folder has to be created under the base path.
"""
from helper.awx_api import Tower
from helper.linux import LinuxSSH
from getpass import getpass
from pprint import pprint

# Get AWX server information
awx_server = input("Address of Ansible AWX: ")
username = input(f"Username of {awx_server}: ")
password = getpass()

# Prepare a tower config.
tower_config = dict(
    server_addr=awx_server,
    username=username,
    password=password
)

# create a Tower instance
tower = Tower(**tower_config)

# Get CentOS information, which hosts Ansible AWX.
linux_user = input("Enter non-root username of server that hosts Ansible AWX: ")
linux_pass = getpass()

linux_config = dict(
    username=linux_user,
    password=linux_pass,
    hostname=awx_server
)

# create a linux instance, we are using the default base path /var/lib/awx/projects
with LinuxSSH(**linux_config) as linux:
    # create a new project directory, call it lab_dev
    if "lab_dev" not in linux.get_project_dirs().get("playbook_dirs"):
        linux.create_project_dir(dirname="lab_dev")

# Create a new project in Ansible AWX, scm_type is default manual.
project_config = dict(
    name="dev_project",
    local_path="lab_dev",
    org_id=tower.find_resource_id(resource="organizations", name="lab_env").get("result")
)

r = tower.create_project(**project_config)
pprint(r)
