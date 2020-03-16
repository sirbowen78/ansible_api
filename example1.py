from helper.awx_api import Tower
from helper.linux import LinuxSSH
from getpass import getpass
import sys

password = getpass()
tower_config = {
    "username": "admin",
    "password": password,
    "server_addr": "192.168.100.174"
}

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
r = tower.job_launch(job_id="acl", extra_vars=payload)
print(r)