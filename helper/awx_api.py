"""
Environment:
1. Ansible version 2.9.6.
2. Centos 7 - Linux Kernel 3.10.0-1062.el7.x86_64.
3. Python version 3.7.6.
4. Ansible AWX 9.2.0 (dockerless)

API testing based on Ansible AWX 9.2.0 dockerless version by mrmeee (https://github.com/MrMEEE/awx-build).
See installation instruction from https://awx.wiki/, follow the installation guide to the dot.

Ansible AWX/Tower API wrapper is written as lab and testing code to teach myself Ansible tower, and also for
my own python practice.
"""
import json
from typing import Optional, Dict, Any, Union, Tuple

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, ConnectTimeout, HTTPError
from urllib3.util.retry import Retry
from types import MappingProxyType
# It is good to explicitly declare the objects I need, if I used the * all imports defined in credential_types_inputs
# will also be imported.
from helper.credential_types_inputs import (CREDENTIAL_TYPES,
                                            SSH_INPUTS,
                                            TOWER_INPUTS,
                                            AWS_INPUTS_OPTION,
                                            AWS_INPUTS,
                                            NET_INPUTS,
                                            GITLAB_TOKEN_INPUTS,
                                            HASHIVAULT_SSH_INPUTS,
                                            HASHIVAULT_KV_INPUTS,
                                            inputs_validator)

CONN_ERROR = (ConnectTimeout, ConnectionError)

VERBOSITY = MappingProxyType(
    {
        "normal": 0,
        "verbose": 1,
        "more_verbose": 2,
        "debug": 3,
        "connection_debug": 4,
        "winrm_debug": 5
    }
)


class Tower:
    """
    The purpose of this class is so that multiple instances of different Ansible Tower/AWX can be created,
    and each instance is different from one another in terms of username, password, server address, port number.
    """

    def __init__(self, username: str = None, password: str = None,
                 server_addr: str = "127.0.0.1", server_port: int = 8052, verify_ssl: bool = False):
        self.username = username
        self.password = password
        self.server_addr = server_addr
        self.server_port = server_port
        self.verify_ssl = verify_ssl

    @staticmethod
    def app_header() -> Dict[str, str]:
        """
        I created this static method because i realize i need to do the same thing
        more than once on every methods.
        :return:
            http header for post/put requests.
        """
        return {
            "Content-Type": "application/json"
        }

    def delete_request(self, resource_id: int = None, resource: str = None, child_resource: str = None):
        """
        Delete request which requires the resource id, the id will be inserted to the uri
        :param child_resource:
            Child of a parent resource, not all api has a uri to delete the child resource,
            available ones are:
            inventory_sources (parent): children are groups and hosts.
            job_templates (parent): child is survey_spec.
            workflow_job_templates (parent): child is survey_spec.
        :param resource:
            authentication, projects, token, instance_groups, config, organizations,
            users, project_updates, teams, credentials, credential_types, inventories,
            inventory_scripts, inventory_sources, inventory_updates, groups, hosts,
            job_templates, jobs, ad_hoc_commands, system_jobs, schedules,
            notification_templates, workflow_job_templates, workflow_jobs,
            workflow_job_templates_nodes, workflow_approvals, workflow_approval_templates,
            credential_input_sources
        :param resource_id:
            config is the only resource that does not require a resource_id.
        :return:
        """
        if child_resource is not None:
            api_uri = f"/v2/{resource}/{resource_id}/{child_resource}/"
        elif resource is not None and resource_id is not None:
            api_uri = f"/v2/{resource}/{resource_id}/"
        else:
            api_uri = f"/v2/{resource}/"
        is_https_status, base_url = self.get_api_url()
        config = {
            "auth": HTTPBasicAuth(self.username, self.password),
            "headers": self.app_header()
        }
        if is_https_status:
            config.update({"verify": self.verify_ssl})
        url = base_url + api_uri
        try:
            response = requests.delete(url, **config)
            if response.status_code == 204:
                return {
                    "status": "success",
                    "message": f"Resource {resource} with id {resource_id} has deleted."
                }
            elif response.status_code == 404:
                return {
                    "status": "failed",
                    "message": "The resource is not found, it could be due to resource_id is not specified."
                }
            elif response.status_code == 409:
                return {
                    "status": "failed",
                    "message": response.text
                }
            else:
                return {
                    "status": "failed",
                    "status_code": response.status_code,
                    "message": response.text
                }
        except CONN_ERROR as CE:
            return {
                "status": "failed",
                "message": str(CE)
            }

    def post_request(self, url: str, is_https_status: bool,
                     payload: Dict[str, Any]) -> Union[Dict[str, str], Dict[str, int], Dict[str, bool]]:
        """
        I have realized the exact same things are used for more than once in more than one method, hence I
        segregate this block as a separate method.
        :param url:
            The url for calling the API
        :param is_https_status:
            This is a lazy way to determine if the prefix is https or not.
        :param payload:
            The request body to be posted.
        :return:
            Dictionary of response.
        """
        config = {
            "auth": HTTPBasicAuth(username=self.username, password=self.password),
            "data": json.dumps(payload),
            "headers": self.app_header()
        }
        if is_https_status:
            config.update({"verify": self.verify_ssl})

        try:
            response = requests.post(url, **config)
            response.raise_for_status()
            return {
                "status": response.status_code,
                "response": json.loads(response.text)
            }
        except CONN_ERROR as e:
            # 522 - Connection timeout.
            # 408 - Request timeout
            return {
                "status": 522 if CONN_ERROR[0] else 408,
                "response": str(e)
            }
        except HTTPError as e:
            return {
                "status": response.status_code,
                "response": str(e)
            }

    def get_api_url(self, total_retries: int = 2, backoff_factor: float = 0.5,
                    verify_ssl: bool = False, request_timeout: float = 0.5) -> Tuple[bool, str]:
        """
        This is a method to check if the url uses https or http and return the prefix with the address.
        :param total_retries:
            total retries for web request
        :param backoff_factor:
            cooldown interval between failed retries
        :param verify_ssl:
            ssl cert check, default is dun check, well this is a lab code.
            your secure web server will be vulnerable to Man-in-the-middle forgery.
        :param request_timeout:
            The time to give up requesting web resource.
        :return:
            Tuple, index 0 is status to tell if it is https or not, index 1 is the full url.
        """
        retries = Retry(total=total_retries,
                        backoff_factor=backoff_factor,
                        status_forcelist=[500, 502, 503, 504])
        url = "https://" + self.server_addr + ":" + str(self.server_port) + "/api"
        with requests.Session() as s:
            s.mount("https://", HTTPAdapter(max_retries=retries))
            try:
                s.get(url, verify=verify_ssl, timeout=request_timeout)
                return True, url
            except CONN_ERROR:
                return False, url.replace("https://", "http://")

    def get_resource_info(self, resource: str = None, resource_id: int = None):
        if resource is not None and resource_id is not None:
            api_uri = f"/v2/{resource}/{resource_id}"
        elif resource is not None:
            api_uri = f"/v2/{resource}"
        else:
            return {
                "status": "failed",
                "status_code": 400,
                "message": "Neither resource nor resource_id are supplied to the method."
            }
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri
        config = {
            "auth": HTTPBasicAuth(self.username, self.password),
            "headers": self.app_header()
        }
        if is_https_status:
            config.update({"verify": self.verify_ssl})
        try:
            response = requests.get(url, **config)
            return response
        except CONN_ERROR as CE:
            return {
                "status": response.status_code,
                "message": str(CE)
            }
        except HTTPError as HE:
            return {
                "status": response.status_code,
                "message": str(HE)
            }

    def find_resource_id(self, resource: str = None, name: str = None) -> Union[Dict[str, str], Dict[str, bool]]:
        """
        If you refer to the API reference, there are a lot of post requests that requires the knowledge of id.
        This method will not work if you have duplicated names in the resource.
        Ansible AWX accepts creation requests of the same name under certain conditions to name a few:
        1. Create Credentials:
            cannot have the same name if both credential type and organization are the same as another credential.
        2. Create Projects:
            cannot have the same name if organization is the same as another project.
        3. Create Inventories:
            cannot have the same name if organization is the same as another inventory.
        4. Create Organizations:
            name cannot be the same.
        So to make life easy always use unique names for your creation.
        This method behaves similarly to the ?search=findme documented in the API guide, just that ?search=findme will
        return a list of the found items.
        :param resource:
            Also known as the endpoint, can be projects, credentials, inventories, organizations
        :param name:
        :return:
        """
        response = self.get_resource_info(resource=resource)
        results = response.json()["results"]
        for result in results:
            if name in result["name"]:
                return {
                    "found": True,
                    "result": int(result["id"])
                }
        return {
            "found": False,
            "result": f"Cannot find {name} in Ansible AWX."
        }

    def create_org(self, name: str = None, desc: Optional[str] = None, max_hosts: int = 0,
                   custom_virtualenv: str = None) -> Union[Dict[str, str], Dict[str, int]]:
        """
        Create and organization. See Ansible Tower API reference for the params.
        :param name:
            Organization name, this is required.
        :param desc:
            Description of the organization this is optional
        :param max_hosts:
            Maximum hosts in this organization, default is 0.
        :param custom_virtualenv:
            Hmm... Read the Ansible API documentation, creating a tower instance in virtualenv is amazing...
        :return:
            Dictionary of response threw up by post_request method.
        """
        api_uri = "/v2/organizations/"
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri
        payload = {
            "name": name,
            "description": desc
        }
        if max_hosts > 0:
            payload.update({"max_hosts": max_hosts})
        if custom_virtualenv is not None:
            payload.update({"custom_virtualenv": custom_virtualenv})
        return self.post_request(url, is_https_status, payload)

    def create_inv(self, name: str = "NewInventory", desc: str = None,
                   org: int = 1, kind: str = None, host_filter: str = None,
                   inv_vars: Union[Dict[str, str], Dict[str, int], Dict[str, bool], str] = None):
        """
        Create inventory. Read Ansible Tower API reference for the params description.
        This inventory is a container you can create groups and hosts within this inventory.
        :param name:
            Name of the inventory, required
        :param desc:
            Description of the inventory, which is optional
        :param org:
            Organization id, must be integer.
        :param kind:
            Default is "", the other is smart inventory.
        :param host_filter:
            Default is "", this is a string read the API documentation.
        :param inv_vars:
            variables in yaml or json, read the API documentation.
        :return:
        """
        api_uri = "/v2/inventories/"
        # base payload, minimum requirement to post.
        payload = {
            "name": name,
            "organization": org
        }
        # Check for valid data, best effort only as I do not know how to properly validate yaml from string.
        if inv_vars is not None and isinstance(inv_vars, dict):
            inv_vars = json.dumps(inv_vars)
            payload.update({"variables": inv_vars})
        elif inv_vars is not None and isinstance(inv_vars, str):
            payload.update({"variables": inv_vars})
        if desc is not None:
            payload.update({"description": desc})
        if kind is not None and str.lower(kind) == "smart":
            payload.update({"kind": kind})
        if host_filter is not None and isinstance(host_filter, str):
            payload.update({"host_filter": host_filter})
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri
        return self.post_request(url, is_https_status, payload)

    def create_inv_group(self, inv_id: int = 1,
                         name: str = "NewGroup",
                         desc: Optional[str] = None,
                         grp_vars: Union[Dict[str, str],
                                         Dict[str, int],
                                         Dict[str, bool], str] = None) -> Union[Dict[str, str], Dict[str, int]]:
        """
        Create group within inventories, read the Ansible Tower API reference for detailed explanation on params.
        :param inv_id:
            inventory id, an integer, part of the request uri.
        :param name:
            name of the group, this is required.
        :param desc:
            description of the group, this is optional.
        :param grp_vars:
            variables for the groups either in yaml or json.
        :return:
            response threw up by post_request method.
        """
        api_uri = f"/v2/inventories/{inv_id}/groups/"
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri
        payload = {
            "name": name
        }
        if desc is not None and isinstance(desc, str):
            payload.update({"description": desc})
        if grp_vars is not None:
            if isinstance(grp_vars, dict):
                payload.update({"variables": json.dumps(grp_vars)})
            elif isinstance(grp_vars, str):
                payload.update({"variables": grp_vars})
        return self.post_request(url, is_https_status, payload)

    def create_inv_host(self, inv_id: int = 1,
                        name: str = "NewHost",
                        desc: Optional[str] = None,
                        enabled: bool = True,
                        host_vars: Union[Dict[str, str],
                                         Dict[str, int],
                                         Dict[str, bool], str] = None) -> Union[Dict[str, str], Dict[str, int]]:
        """
        The api call is very similar to create_inv_group, perhaps these two methods can merge? The only difference
        is the uri instead of groups it is hosts.
        Read Ansible Tower API reference guide for detailed explanation on params.
        :param inv_id:
            inventory id, which is integer, part of the api uri.
        :param name:
            name of the host.
        :param desc:
            description of the host, this is optional.
        :param enabled:
            Default is enabled.
        :param host_vars:
            The variables of host config can be ansible_network_os: asa, ansible_host: 192.168.1.1
        :return:
            dictionary of response threw up by post_request method.
        """
        api_uri = f"/v2/inventories/{inv_id}/hosts/"
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri
        payload = {
            "name": name,
        }
        if not enabled:
            payload.update({"enabled": enabled})
        # duplicate code, this line is exactly the same as create_inv_group
        if desc is not None and isinstance(desc, str):
            payload.update({"description": desc})
        if host_vars is not None:
            if isinstance(host_vars, dict):
                payload.update({"variables": json.dumps(host_vars)})
            elif isinstance(host_vars, str):
                payload.update({"variables": host_vars})
        return self.post_request(url, is_https_status, payload)

    def create_credential(self, name: str = "admin", desc: str = None,
                          credential_type: str = "ssh", org_id: Optional[int] = 0, user: str = None, team: str = None,
                          inputs: Dict[str, str] = None) -> Union[Dict[str, str], Dict[str, int]]:
        """
        There are many credential types, not all are supported by the code. At best effort,
        this method will try to check the inputs then give a helper message if the inputs is wrong.
        :param name:
            name of the credential
        :param desc:
            description of the credential
        :param credential_type:
            a string of credential type supported are ssh, net, tower, vault, aws, openstack, gitlab_token,
            github_token, hashivault_kv, hashivault_ssh.
            This method will then use the string and lookup for
            the credential type id which is required by Ansible AWX REST API for credential creation.
        :param org_id:
            Organization id, if this is specify, user and team must not be specified.
        :param user:
            if this is specified, organization and team must not be specified.
        :param team:
            if this is specified, user and organization must not be specified.
        :param inputs:
            data for different credential types.
        :return:
        """
        api_uri = "/v2/credentials/"
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri
        # Base payload. See Ansible Tower API reference guide.
        payload = {
            "name": name,
            "credential_type": CREDENTIAL_TYPES.get(str.lower(credential_type))
        }
        # Description is optional.
        if desc is not None:
            payload.update({"description": desc})
        # Choose one from organization or user or team, must choose one out of three.
        if org_id > 0 and user is None and team is None:
            payload.update({"organization": org_id})
        elif user is not None and org_id == 0 and team is None:
            payload.update({"user": user})
        elif team is not None and user is None and org_id == 0:
            payload.update({"team": team})
        else:
            # Forcing the request to have at least one chosen from organization or team or user.
            return {
                "status": "failed",
                "status_code": 400,
                "message": "Choose to inherit permission exclusively from user or team or organization."
            }
        if inputs is not None and isinstance(inputs, dict):
            # If inputs has something and is a dict type then check which credential type and do fact checking
            # accordingly.
            if credential_type.lower() == "ssh":
                """
                This block is to ensure the inputs dict conforms to Ansible AWX's requirement.
                For Machine/ssh credential type there is no requirement to put in any of these in inputs:
                username, password, become_method, become_username, become_password.
                """
                if any(key in inputs for key in SSH_INPUTS):
                    # if any key exists in the tuple SSH_INPUTS
                    inputs = inputs_validator(inputs, SSH_INPUTS)
                    if inputs != {}:
                        # This is to guard against empty inputs is sent.
                        # it is possible inputs is an empty dict when the inputs does not have required keys.
                        payload.update(
                            {
                                "inputs": inputs
                            }
                        )
                        # This part will ignore the inputs if there is None supplied
                        return self.post_request(url, is_https_status, payload)
                    else:
                        # if the inputs supplied has incorrect keys, this dictionary advises user with example.
                        return {
                            "status": "failed",
                            "status_code": 400,
                            "message": "Keys in inputs are incorrect, see example.",
                            "example": dict(zip(SSH_INPUTS, ["admin",
                                                             "password",
                                                             "enable",
                                                             "enable_user",
                                                             "enable_pass"]))
                        }

            elif credential_type.lower() == "net":
                """
                Network inputs requires at least username. password, authorize and authorize_password are optional.
                """
                if "username" in inputs.keys():
                    # Has confirmed at least the key username is present in inputs.
                    inputs = inputs_validator(inputs, NET_INPUTS)
                    payload.update(
                        {
                            "inputs": inputs
                        }
                    )
                    return self.post_request(url, is_https_status, payload)
                else:
                    # Send a helper message to user if compulsory key is not found in inputs.
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "The key username is compulsory, but is not found in inputs. See example.",
                        "example": dict(zip(NET_INPUTS, ["admin", "password", "true", "enable_password"]))
                    }
            elif credential_type.lower() == "aws":
                """
                This is best effort validation. I realize even if there is only username in inputs Ansible AWX accepts.
                This code block ensures username, password and security_token are available, all other invalid keys
                are removed.
                """
                inputs = inputs_validator(inputs, AWS_INPUTS_OPTION)
                if inputs == dict():
                    # There will be a chance when no valid keys is in inputs, if this situation arises
                    # inputs will be a dict() or {}, but this is not None, it simply means the dict is empty.
                    # None type is an object not exactly means empty, so {} is not None it is dict type object.
                    # Below sends a helper message with minimum requirement for creating aws credential.
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Username and password are compulsory keys, but these are not found in inputs. See example.",
                        "example": dict(zip(AWS_INPUTS, ["accesskey", "secretkey"]))
                    }
                payload.update(
                    {
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            elif credential_type.lower() == "tower":
                inputs = inputs_validator(inputs, TOWER_INPUTS)
                if inputs == dict():
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Invalid keys in inputs, see example.",
                        "example": dict(zip(TOWER_INPUTS, ["https://authentication.url",
                                                           "username",
                                                           "password",
                                                           True]))
                    }
                payload.update(
                    {
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            elif credential_type.lower() == "gitlab_token" or credential_type == "github_token":
                """
                Both gitlab and github shares the same params of inputs.
                """
                inputs = inputs_validator(inputs, GITLAB_TOKEN_INPUTS)
                if inputs == dict():
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Invalid keys in inputs. See example.",
                        "example": {"token": "gitlab_or_github_token"}
                    }
                payload.update(
                    {
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            elif credential_type.lower() == "hashivault_kv":
                inputs = inputs_validator(inputs, HASHIVAULT_KV_INPUTS)
                if inputs == dict():
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Invalid keys in inputs. See example.",
                        "example": dict(zip(HASHIVAULT_KV_INPUTS, ["https://192.168.1.1:8200",
                                                                   "abcdefghijklmnop9999",
                                                                   "v2"]))
                    }
                payload.update(
                    {
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            elif credential_type.lower() == "hashivault_ssh":
                inputs = inputs_validator(inputs, HASHIVAULT_SSH_INPUTS),
                if inputs == dict():
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Invalid keys in inputs. See example.",
                        "example": dict(zip(HASHIVAULT_SSH_INPUTS, ["https://192.168.1.1:8200",
                                                                    "abcdefghijklmnop9999"]))
                    }
                payload.update(
                    {
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            else:
                return {
                    "status": "failed",
                    "status_code": 400,
                    "message": "Unrecognized credential_type. See \"supported\" for credential_type.",
                    "supported": [key for key in CREDENTIAL_TYPES]
                }
        # credential creation without inputs. I am surprised this is allowed by ansible awx.
        return self.post_request(url, is_https_status, payload)

    def collect_info(self, info_type: str = "credentials",
                     extra_params: Optional[str] = None) -> Union[Dict[str, str], Dict[str, int]]:
        """
        The purpose is to collect facts about credentials and organizations, I have not yet checked other GET
        response on other endpoints so far I am using for credentials and organizations only.
        :param extra_params:
        :param info_type:
        :return:
        """
        response = self.get_resource_info(resource=info_type)
        results = response.json().get("results")
        collect_ids = list()
        collect_names = list()
        collect_params = list()
        for result in results:
            collect_ids.append(result.get("id"))
            collect_names.append(result.get("name"))
            collect_params.append(result.get(extra_params, None))

        gather_info = {
            # GET is straightforward either 200 or 404.
            "status": "success" if response.status_code == 200 else "failed",
            "count": response.json().get("count"),
            "facts": dict(zip(collect_ids, collect_names)),
            "ids": collect_ids
        }
        if collect_params:
            gather_info.update(
                {
                    "extra": dict(zip(collect_params, collect_names)),
                    "used": collect_params
                }
            )
        return gather_info

    def create_project(self, name: str = "MyProject",
                       desc: str = None, local_path: str = None,
                       scm_type: str = "", scm_url: str = None, scm_branch: str = None,
                       scm_refspec: str = None, scm_clean: bool = False, scm_delete_on_update: bool = False,
                       credential: int = None, timeout: int = 0, org_id: int = 1,
                       scm_update_on_launch: bool = False, scm_update_cache_timeout: int = 0,
                       allow_override: bool = False,
                       custom_virtualenv: str = None) -> Union[Dict[str, str], Dict[str, int]]:
        api_uri = "/v2/projects/"
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri

        if org_id != 1:
            # Ensure the org_id is valid.
            org_info = self.collect_info(info_type="organizations")
            if org_id not in org_info["ids"]:
                return {
                    "status": "failed",
                    "status_code": 400,
                    "message": f"Organization id {org_id} does not exist in Ansible AWX.",
                    "valid": org_info["facts"]
                }

        payload = {
            "name": name,
            "organization": org_id,
            "description": desc if desc is not None else ""
        }
        if timeout > 0:
            payload.update({"timeout": timeout})
        if custom_virtualenv is not None:
            payload.update({"custom_virtualenv": custom_virtualenv})
        if local_path is not None:
            """
            local_path is required in Ansible AWX 9.2.0 web ui if SCM TYPE is manual.
            local_path is the subdirectory name in project base path.
            the local_path lets Ansible AWX to find the yaml file for Ansible Job.
            local_path can only be used by ONE project, there is no sharing amongst project.
            """
            lpath = self.collect_info(info_type="projects", extra_params="local_path")
            project_name = lpath["extra"]
            if local_path in lpath["used"]:
                return {
                    "status": "failed",
                    "message": f"local_path ({local_path}) is currently being used by project ({project_name[local_path]})."
                }
            payload.update({"local_path": local_path})
        if credential is not None and isinstance(credential, int):
            # Check if the id supplied is valid, if it is not valid, a helper message will appear to guide user.
            creds = self.collect_info()
            if credential not in creds.get("ids"):
                # helper message not only sounds error, but also provide a dictionary of valid credentials.
                return {
                    "status": "failed",
                    "message": f"Credential ID {credential} is not found in Ansible AWX.",
                    "valid": creds.get("facts")
                }
            else:
                payload.update({"credential": credential})
        if scm_type == "":
            payload.update({"scm_type": scm_type})
        elif scm_type == "git":
            """
            Currently only support git in the code.
            """
            payload.update({"scm_type": scm_type})
            if scm_url is not None:
                # In the Ansible AWX url if git is chosen, scm url is a mandatory field.
                payload.update(
                    {  # The below params are relevant to git, maybe even svn, redhat insights.
                        "scm_url": scm_url,
                        "scm_clean": scm_clean,
                        "scm_delete_on_update": scm_delete_on_update,
                        "scm_update_on_launch": scm_update_on_launch,
                        "scm_update_cache_timeout": scm_update_cache_timeout,
                        "allow_override": allow_override
                    }
                )
            else:
                return {
                    "status": "failed",
                    "status_code": 400,
                    "message": f"{scm_type} requires you to fill in the scm_url in the request body.",
                    "example": {"scm_type": "https://github.com/ansible/ansible-tower-samples"}
                }
            if scm_branch is not None and isinstance(scm_branch, str):
                payload.update({"scm_branch": scm_branch})
            if scm_refspec is not None and isinstance(scm_refspec, str):
                payload.update({"scm_refspec": scm_refspec})
        else:
            return {
                "status": "failed",
                "status_code": 400,
                "message": f"Unrecognized scm_type {scm_type}, current supported ones are git and manual."
            }
        return self.post_request(url, is_https_status, payload)

    def create_job_template(self,
                            name: str = "NewTemplate",
                            desc: str = None,
                            credential: str = None,
                            job_type: str = "run",
                            inv_id: Union[str, int] = None,
                            project_id: Union[str, int] = None,
                            playbook: str = None,
                            scm_branch: str = None,
                            forks: int = 0,
                            limit: str = None,
                            verbosity: Union[str, int] = 0,
                            extra_vars: Dict = None,
                            job_tags: str = None,
                            force_handlers: bool = False,
                            skip_tags: str = None,
                            start_at_tasks: str = None,
                            timeout: int = 0,
                            use_fact_cache: bool = False,
                            host_config_key: str = None,
                            ask_scm_branch_on_launch: bool = False,
                            ask_diff_mode_on_launch: bool = False,
                            ask_variables_on_launch: bool = True,  # in order for extra_vars to be used in api
                            ask_limit_on_launch: bool = False,
                            ask_tags_on_launch: bool = False,
                            ask_skip_tags_on_launch: bool = False,
                            ask_job_type_on_launch: bool = False,
                            ask_verbosity_on_launch: bool = False,
                            ask_inventory_on_launch: bool = False,
                            ask_credential_on_launch: bool = False,
                            survey_enabled: bool = False,
                            become_enabled: bool = False,
                            diff_mode: bool = False,
                            allow_simultaneous: bool = False,
                            custom_virtualenv: str = None,
                            job_slice_count: int = 1,
                            webhook_service: str = None,
                            webhook_credential: Union[str, int] = None):
        """
        This job_template creation requires a lot of parameters,
        read the ansible tower api reference guide for details.
        :param credential:
            If there is an existing credential you wish to add to the job tempalte.
            If this is provided the method will call another
            api endpoint /api/v2/job_templates/{id}/credentials/.
        :param name:
            required parameter to specify the job_templates name.
        :param desc:
            optional.
        :param job_type:
            default is run. The other is check. I cannot find scan in Ansible AWX web ui.
        :param inv_id:
            This can be a name in string or id, this refers to the inventory.
        :param project_id:
            This can be name in string or id, this refers to the project.
        :param playbook:
            playbook yaml file.
        :param scm_branch:
        :param forks:
        :param limit:
        :param verbosity:
            can be a string or int, default is 0 which is normal. If string put in one of these normal, verbose,
            more_verbose, debug, connection_debug, winrm_debug. This method will use the string to lookup for the
            verbosity id with VERBOSITY MappingProxyType object.
        :param extra_vars:
            can be dictionary (json), extra variables for your playbook. It is more recommended to use
            extra_vars when launching job_template, it is best not to define the extra_vars unless you do not
            expect to put in extra_vars when launching this job template.
        :param job_tags:
        :param force_handlers:
        :param skip_tags:
        :param start_at_tasks:
        :param timeout:
        :param use_fact_cache:
        :param host_config_key:
            This enables the provisioning call back.
        :param ask_scm_branch_on_launch:
        :param ask_diff_mode_on_launch:
        :param ask_variables_on_launch:
        :param ask_limit_on_launch:
        :param ask_tags_on_launch:
        :param ask_skip_tags_on_launch:
        :param ask_job_type_on_launch:
        :param ask_verbosity_on_launch:
        :param ask_inventory_on_launch:
        :param ask_credential_on_launch:
        :param survey_enabled:
        :param become_enabled:
        :param diff_mode:
        :param allow_simultaneous:
        :param custom_virtualenv:
        :param job_slice_count:
        :param webhook_service:
            gitlab or github
        :param webhook_credential:
            if webhook_service is chosen, this must be defined, either the name of the github/gitlab credential or
            the credential id.
        :return:
        """
        api_uri = "/v2/job_templates/"
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri
        payload = {
            "name": name,
            "descripton": "" if desc is None else desc,
            "job_type": job_type,
            "playbook": playbook,
            "forks": forks,
            "scm_branch": "" if scm_branch is None else scm_branch,
            "limit": "" if limit is None else limit,
            "extra_vars": extra_vars,
            "job_tags": "" if job_tags is None else job_tags,
            "force_handlers": force_handlers,
            "skip_tags": "" if skip_tags is None else skip_tags,
            "start_at_task": "" if start_at_tasks is None else start_at_tasks,
            "timeout": timeout,
            "use_fact_cache": use_fact_cache,
            "host_config_key": "" if host_config_key is None else host_config_key,
            "ask_scm_branch_on_launch": ask_scm_branch_on_launch,
            "ask_diff_mode_on_launch": ask_diff_mode_on_launch,
            "ask_variables_on_launch": ask_variables_on_launch,
            "ask_limit_on_launch": ask_limit_on_launch,
            "ask_tags_on_launch": ask_tags_on_launch,
            "ask_skip_tags_on_launch": ask_skip_tags_on_launch,
            "ask_job_type_on_launch": ask_job_type_on_launch,
            "ask_verbosity_on_launch": ask_verbosity_on_launch,
            "ask_inventory_on_launch": ask_inventory_on_launch,
            "ask_credential_on_launch": ask_credential_on_launch,
            "survey_enabled": survey_enabled,
            "become_enabled": become_enabled,
            "diff_mode": diff_mode,
            "allow_simultaneous": allow_simultaneous,
            "custom_virtualenv": "" if custom_virtualenv is None else custom_virtualenv,
            "job_slice_count": job_slice_count,
            "webhook_credential": "" if webhook_credential is None else webhook_credential
        }
        if isinstance(project_id, str):
            project_response = self.find_resource_id(resource="projects", name=project_id)
            if project_response.get("found"):
                payload.update({"project": project_response.get("result")})
            else:
                return project_response
        elif isinstance(project_id, int):
            payload.update({"project": project_id})
        else:
            return {
                "status": "failed",
                "message": "project_id must be either string or integer."
            }
        if isinstance(inv_id, str):
            inv_response = self.find_resource_id(resource="inventories", name=inv_id)
            if inv_response.get("found"):
                payload.update({"inventory": inv_response.get("result")})
            else:
                return inv_response
        elif isinstance(inv_id, int):
            payload.update({"inventory": inv_id})
        else:
            return {
                "status": "failed",
                "message": "inv_id must be either string or integer."
            }
        if isinstance(verbosity, str):
            payload.update({"verbosity": VERBOSITY[verbosity.lower()]})
        elif isinstance(verbosity, int) and 0 <= verbosity <= 5:
            payload.update({"verbosity": verbosity})
        else:
            payload.update({"verbosity": 0})
        if webhook_service == "gitlab" or webhook_service == "github":
            payload.update({"webhook_service": webhook_service})
        else:
            payload.update({"webhook_service": ""})

        # Before posting the payload, check for required keys. Good for me to find for bugs
        # if Ansible AWX says it is a bad request.
        required = ["name", "job_type", "inventory", "project", "playbook", "verbosity"]
        if all(k in payload for k in required):
            job_create_response = self.post_request(url, is_https_status, payload)
        else:
            return {
                "status": "failed",
                "message": "Insufficient mandatory parameters, see required.",
                "required": ", ".join(required)
            }
        if job_create_response["status"] == 201:
            if isinstance(credential, str):
                get_cred_response = self.find_resource_id(resource="credentials", name=credential)
                if get_cred_response.get("found"):
                    return self.create_job_templates_cred(cred_id=get_cred_response.get("result"),
                                                          job_template_id=self.find_resource_id(
                                                              resource="job_templates",
                                                              name=name).get("result"),
                                                          name=credential)
                else:
                    return job_create_response
            else:
                return job_create_response

    def job_launch(self, job_id: Union[str, int] = None, extra_vars: Dict = None):
        if isinstance(job_id, str):
            response = self.find_resource_id(resource="job_templates", name=job_id)
            if response.get("found"):
                api_uri = f"/v2/job_templates/{response.get('result')}/launch/"
            else:
                return {
                    "status": "failed",
                    "message": f"{job_id} cannot be found."
                }
        elif isinstance(job_id, int):
            api_uri = f"/v2/job_templates/{job_id}/launch/"
        else:
            return {
                "status": "failed",
                "message": "job_id cannot be none."
            }
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri
        payload = {
            "extra_vars": extra_vars
        }
        return self.post_request(url, is_https_status, payload)

    def create_job_templates_cred(self,
                                  cred_id: Union[str, int] = None,
                                  desc: str = None,
                                  job_template_id: Union[str, int] = None,
                                  name: str = "NewCredential",
                                  org_id: Union[str, int] = None,
                                  credential_type: Union[str, int] = None,
                                  inputs: Union[Dict[str, str], Dict[str, int], Dict[str, bool]] = None):
        """
        This creates a new credential for job template.
        :param desc:
        :param job_template_id:
            This is the job template id which is part of the api uri. If you provide a string,
            this method will find the job template id for you.
        :param cred_id:
            This is required if you want to add an existing credential to job templates.
        :param name:
            This is the name of the credential, this is mandatory field. If you need to add
            an existing credential to job templates the name must be specified.
        :param org_id:
            This is the organization id, in this method if you supply a string the method will find
            the organization id for you.
        :param credential_type:
            This is the credential type, if you specify a string the method will find the credential_type
            id for you.
        :param inputs:
            This is the additional inputs such as username, password for different types of credential_type.
        :return:
        """
        if isinstance(job_template_id, str):
            find_response = self.find_resource_id(resource="job_templates", name=job_template_id)
            if find_response.get("found"):
                jt_id = find_response.get("result")
                api_uri = f"/v2/job_templates/{jt_id}/credentials/"
            else:
                return {
                    "status": "failed",
                    "message": f"Supplied job template id {job_template_id} is not found."
                }
        elif isinstance(job_template_id, int):
            api_uri = f"/v2/job_templates/{job_template_id}/credentials/"
        else:
            return {
                "status": "failed",
                "message": "Invalid object type for job_template_id."
            }
        is_https_status, base_url = self.get_api_url()
        url = base_url + api_uri
        if isinstance(cred_id, str):
            find_cred = self.find_resource_id(resource="credentials", name=cred_id)
            if find_cred.get("found"):
                add_cred_payload = {
                    "name": cred_id,
                    "id": find_cred.get("result")
                }
                return self.post_request(url, is_https_status, add_cred_payload)
        elif isinstance(cred_id, int):
            response = self.get_resource_info(resource="credentials", resource_id=cred_id)
            if response.status_code == 200:
                add_cred_payload = {
                    "name": response.json().get("name"),
                    "id": cred_id
                }
                return self.post_request(url, is_https_status, add_cred_payload)
        payload = {
            "name": name
        }
        if isinstance(org_id, str):
            find_org = self.find_resource_id(resource="organizations", name=org_id)
            if find_org.get("found"):
                payload.update(
                    {
                        "organization": find_org.get("result")
                    }
                )
            else:
                return {
                    "status": "failed",
                    "message": f"The org_id {org_id} cannot be found."
                }
        elif isinstance(org_id, int):
            find_org_response = self.get_resource_info(resource="organizations", resource_id=org_id)
            if find_org_response.status_code == 200:
                payload.update(
                    {
                        "organization": org_id
                    }
                )
        payload.update(
            {
                "description": "" if desc is None else desc
            }
        )
        if inputs is not None and isinstance(inputs, dict):
            # If inputs has something and is a dict type then check which credential type and do fact checking
            # accordingly.
            if credential_type.lower() == "ssh":
                """
                    This block is to ensure the inputs dict conforms to Ansible AWX's requirement.
                    For Machine/ssh credential type there is no requirement to put in any of these in inputs:
                    username, password, become_method, become_username, become_password.
                    """
                if any(key in inputs for key in SSH_INPUTS):
                    # if any key exists in the tuple SSH_INPUTS
                    inputs = inputs_validator(inputs, SSH_INPUTS)
                    if inputs != {}:
                        # This is to guard against empty inputs is sent.
                        # it is possible inputs is an empty dict when the inputs does not have required keys.
                        payload.update(
                            {
                                "credential_type": CREDENTIAL_TYPES[credential_type.lower()],
                                "inputs": inputs
                            }
                        )
                        # This part will ignore the inputs if there is None supplied
                        return self.post_request(url, is_https_status, payload)
                    else:
                        # if the inputs supplied has incorrect keys, this dictionary advises user with example.
                        return {
                            "status": "failed",
                            "status_code": 400,
                            "message": "Keys in inputs are incorrect, see example.",
                            "example": dict(zip(SSH_INPUTS, ["admin",
                                                             "password",
                                                             "enable",
                                                             "enable_user",
                                                             "enable_pass"]))
                        }

            elif credential_type.lower() == "net":
                """
                    Network inputs requires at least username. password, authorize and authorize_password are optional.
                    """
                if "username" in inputs.keys():
                    # Has confirmed at least the key username is present in inputs.
                    inputs = inputs_validator(inputs, NET_INPUTS)
                    payload.update(
                        {
                            "credential_type": CREDENTIAL_TYPES[credential_type.lower()],
                            "inputs": inputs
                        }
                    )
                    return self.post_request(url, is_https_status, payload)
                else:
                    # Send a helper message to user if compulsory key is not found in inputs.
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "The key username is compulsory, but is not found in inputs. See example.",
                        "example": dict(zip(NET_INPUTS, ["admin", "password", "true", "enable_password"]))
                    }
            elif credential_type.lower() == "aws":
                """
                    This is best effort validation. I realize even if there is only username in inputs Ansible AWX accepts.
                    This code block ensures username, password and security_token are available, all other invalid keys
                    are removed.
                    """
                inputs = inputs_validator(inputs, AWS_INPUTS_OPTION)
                if inputs == dict():
                    # There will be a chance when no valid keys is in inputs, if this situation arises
                    # inputs will be a dict() or {}, but this is not None, it simply means the dict is empty.
                    # None type is an object not exactly means empty, so {} is not None it is dict type object.
                    # Below sends a helper message with minimum requirement for creating aws credential.
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Username and password are compulsory keys, but these are not found in inputs. See "
                                   "example.",
                        "example": dict(zip(AWS_INPUTS, ["accesskey", "secretkey"]))
                    }
                payload.update(
                    {
                        "credential_type": CREDENTIAL_TYPES[credential_type.lower()],
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            elif credential_type.lower() == "tower":
                inputs = inputs_validator(inputs, TOWER_INPUTS)
                if inputs == dict():
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Invalid keys in inputs, see example.",
                        "example": dict(zip(TOWER_INPUTS, ["https://authentication.url",
                                                           "username",
                                                           "password",
                                                           True]))
                    }
                payload.update(
                    {
                        "credential_type": CREDENTIAL_TYPES[credential_type.lower()],
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            elif credential_type.lower() == "gitlab_token" or credential_type == "github_token":
                """
                Both gitlab and github shares the same params of inputs.
                """
                inputs = inputs_validator(inputs, GITLAB_TOKEN_INPUTS)
                if inputs == dict():
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Invalid keys in inputs. See example.",
                        "example": {"token": "gitlab_or_github_token"}
                    }
                payload.update(
                    {
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            elif credential_type.lower() == "hashivault_kv":
                inputs = inputs_validator(inputs, HASHIVAULT_KV_INPUTS)
                if inputs == dict():
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Invalid keys in inputs. See example.",
                        "example": dict(zip(HASHIVAULT_KV_INPUTS, ["https://192.168.1.1:8200",
                                                                   "abcdefghijklmnop9999",
                                                                   "v2"]))
                    }
                payload.update(
                    {
                        "credential_type": CREDENTIAL_TYPES[credential_type.lower()],
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            elif credential_type.lower() == "hashivault_ssh":
                inputs = inputs_validator(inputs, HASHIVAULT_SSH_INPUTS),
                if inputs == dict():
                    return {
                        "status": "failed",
                        "status_code": 400,
                        "message": "Invalid keys in inputs. See example.",
                        "example": dict(zip(HASHIVAULT_SSH_INPUTS, ["https://192.168.1.1:8200",
                                                                    "abcdefghijklmnop9999"]))
                    }
                payload.update(
                    {
                        "credential_type": CREDENTIAL_TYPES[credential_type.lower()],
                        "inputs": inputs
                    }
                )
                return self.post_request(url, is_https_status, payload)
            else:
                return {
                    "status": "failed",
                    "status_code": 400,
                    "message": "Unrecognized credential_type. See \"supported\" for credential_type.",
                    "supported": [key for key in CREDENTIAL_TYPES]
                }
        else:
            return self.post_request(url, is_https_status, payload)
