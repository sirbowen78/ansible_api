# ansible_api
This is a REST API wrapper of Ansible AWX 9.2.0. This is meant for my own consumption to fulfil some features I need to perform on Ansible AWX. Writing this wrapper also gives myself an opportunity to learn Ansible Tower and to practice my python kung fu.

# Examples:
- example1.py: demonstrates how to launch a job, in order for extra_vars to be passed over to the rest api the parameter ask_variables_on_launch has to be True.

- example2.py: demonstrates how to create an organization, and create a credential.

- example3.py: demonstrates how to create an inventory, and a host in an inventory.

- example4.py: demonstrates how to create a project, and create a new project directory within linux that hosts Ansible AWX.

- example5.py: demonstrates how to upload file to the target centos server that hosts the ansible awx, and create a job template.

- example6.py: demonstrates organization creation, inventory creation, inventory hosts creation, project creation, job template creation, create credential for job template.

- example7.py: demonstrates on removing resources.

- example8.py: demonstrates on creation chaining by using the creation response, the creation begins from creating organization until job templates, and finally add existing credential to the created job.

# command line
Usage example: python tower.py -u admin --host 192.168.1.1 --resource projects lab -p

Required switches are -u/--user, --host and -p/--pass which are the username, hostname and password.
-p/--pass will invoke a getpass() for you to type in the password on your screen securely.

The --resource is to get the information of a specific resource name, such as I need to get the json response of a project named lab.