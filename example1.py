from helper.awx_api import Tower
from getpass import getpass

# Get the password from user.
password = getpass()

# Ansible Tower/AWX minimum configuration
tower_config = {
    "username": "admin",
    "password": password,
    "server_addr": "192.168.100.174"
}

"""
Below is how the playbook looks like:

- hosts: "{{ hostname }}"
  gather_facts: false
  connection: network_cli
  tasks:
    - name: ASA rules
      asa_acl:
        lines:
          - "access-list {{ acl_name }} line {{ line if line is defined }} extended {{ action }} {{ protocol }} {{ src_object_type }} {{ src_addr }} {{ dst_object_type }} {{ dst_addr }} eq {{ service }} log"
        after: write memory
"""
payload = {
    "hostname": "fw03",
    "acl_name": "ansible_push",
    "line": 1,
    "action": "deny",
    "protocol": "tcp",
    "src_object_type": "host",
    "src_addr": "1.1.1.1",
    "dst_object_type": "host",
    "dst_addr": "2.2.2.2",
    "service": 8443
}
tower = Tower(**tower_config)
# launch the job by sending the extra_vars to the server.
r = tower.job_launch(job_id="acl", extra_vars=payload)
print(r)