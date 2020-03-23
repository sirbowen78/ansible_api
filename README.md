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

# Command Line
Below example use an Ansible AWX 192.168.100.174, with default port 8052, username is admin and password is password.
Current command line can only create and delete organizations, I am building up the command line bit by bit.
### Get resource information
1. Get organizations resource "cli_test" information:
`python tower.py -u admin --host 192.168.100.174 -p --resource organizations cli_test`
or `python tower.py -u admin -p --host 192.168.100.174 --type organizations --name cli_test`

### Create resource
1. Create an organization:
In this example I will create a new organization "new organizations", if the string has no space then no double quotes is needed.
`python tower.py -u admin -p --host 192.168.100.174 --create --type organizations --name "new organizations"`
