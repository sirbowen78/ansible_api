# ansible_api
This is a REST API wrapper of Ansible AWX 9.2.0. This is meant for my own consumption to fulfil some features I need to perform on Ansible AWX. Writing this wrapper also gives myself an opportunity to learn Ansible Tower and to practice my python kung fu.

# Examples:
- example1.py: demonstrates how to launch a job, in order for extra_vars to be passed over to the rest api the parameter ask_variables_on_launch has to be True.

- example2.py: demonstrates how to create an organization, and create a credential.

- example3.py: demonstrates how to create an inventory, and a host in an inventory.

- example4.py: demonstrates how to create a project, and create a new project directory within linux that hosts Ansible AWX.
