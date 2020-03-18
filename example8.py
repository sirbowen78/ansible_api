from helper.awx_api import Tower
from helper.credential_types_inputs import SSH_INPUTS
from getpass import getpass
"""
This example demonstrates creation chaining by using the response after each creation.
On posting /api/v2/job_templates/{id}/credentials/ I realize json decoder raised an exception,
this is because posting only {"name": "credential name", "id": 1} the server will not return any json body (http 204)
"""

# Ansible AWX/Tower information
awx_server = input("AWX server ip address: ")
username = input(f"Username of {awx_server}: ")
password = getpass()
tower_config = dict(
    server_addr=awx_server,
    username=username,
    password=password
)
# create an instance of Ansible AWX/Tower
tower = Tower(**tower_config)

# create organization
tower_response = tower.create_org(name="cyruslab",
                                  desc="cyruslab.net",
                                  max_hosts=200)
# json response returned after organization creation.
print(tower_response)

# Get asa credential
asa_user = input("Username for asa: ")
asa_pass = getpass()
# create credential
cred_response = tower.create_credential(name="fw03",
                                        desc="fw03 credentials",
                                        org_id=tower_response["response"].get("id"),
                                        inputs=dict(
                                            zip(SSH_INPUTS, (asa_user, asa_pass, "enable", asa_user, asa_pass))
                                        ))
print(cred_response)

# create inventory
inv_response = tower.create_inv(name="firewalls",
                                desc="firewalls",
                                org=tower_response["response"].get("id"),
                                inv_vars=dict(
                                    ansible_network_os="asa"
                                ))
print(inv_response)

# create host and attach to inventory
host_response = tower.create_inv_host(name="fw03",
                                      host_vars=dict(
                                          ansible_host="192.168.100.40"
                                      ),
                                      inv_id=inv_response["response"].get("id"))
print(host_response)

# create a project
project_response = tower.create_project(name="lab",
                                        local_path="lab_dev",
                                        org_id=tower_response["response"].get("id"),
                                        )
print(project_response)

# create a job template and attached inventory and project.
job_response = tower.create_job_template(name="acl",
                                         inv_id=inv_response["response"].get("id"),
                                         project_id=project_response["response"].get("id"),
                                         playbook="asa_acl.yml",
                                         verbosity="debug",
                                         become_enabled=True,
                                         diff_mode=True)
print(job_response)

# add existing credential to the created job.
jt_cred_response = tower.create_job_templates_cred(cred_id=cred_response["response"].get("id"),
                                                   job_template_id=job_response["response"].get("id"))
# adding existing credential to job template will not get any content, http 204.
print(jt_cred_response)
