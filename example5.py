from helper.awx_api import Tower
from helper.linux import LinuxSSH
from getpass import getpass
from pprint import pprint
import gc

# Get CentOS information, which hosts Ansible AWX.
# I have a problem with granting non-root user to copy files via sftp to /var/lib/awx/projects/lab_env
linux_user = input("Enter non-root username of server that hosts Ansible AWX: ")
linux_pass = getpass()

linux_config = dict(
    username=linux_user,
    password=linux_pass,
    hostname="192.168.100.174"
)

# preparing the upload request to copy asa_acl.yml to centos using sftp.
upload_request = dict(
    src_filename="asa_acl.yml",
    dst_filename="asa_acl.yml",
    dst_path="/var/lib/awx/projects/lab_dev"
)
# upload a playbook to the project directory: lab_dev
with LinuxSSH(**linux_config) as linux:
    linux.upload(**upload_request)

# cleaning up sensitive information after use.
# but the information still in memory, only the object is removed.
del linux_config
gc.collect()

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
# prepare information for job template creation
job_template_config = dict(
    name="acl",
    desc="Job to send firewall rule",
    project_id="dev_project",
    inv_id="cisco_asa",
    become_enabled=True,
    diff_mode=True,
    playbook="asa_acl.yml",
    verbosity="debug"
)

# create a job template in project: dev_project
r = tower.create_job_template(**job_template_config)
pprint(r)