"""
This python file collects the mapping and the required keys for inputs for different credential types.
Hence the objects here must be immutable as they are for reference/comparison and not for assignment or modification.
"""
from types import MappingProxyType
from typing import Dict, Any, Union, Tuple
import gc

# MappingProxyType disallows assignment or modification to dictionary object.
CREDENTIAL_TYPES = MappingProxyType(
    {
        "ssh": 1,  # Machine
        "vault": 3,  # Ansible Vault
        "net": 4,  # Network
        "aws": 5,  # Amazon Web Service
        #"openstack": 6,  # OpenStack
        "github_token": 12,  # Github access token
        "gitlab_token": 13,  # Gitlab access token
        "tower": 16,  # Ansible Tower
        "hashivault_kv": 21,  # Hashicorp vault secret key lookup
        "hashivault_ssh": 22  # Hashicorp vault signed ssh
    }
)

# Machine, none of the keys are compulsory.
SSH_INPUTS = ("username", "password", "become_method", "become_username", "become_password")

# Network, only username is compulsory. Optional keys are "password", "authorize", "authorize_password"
NET_INPUTS = ("username",
              "password",
              "authorize",
              "authorize_password")

# Ansible Tower, only verify_ssl is not compulsory.
TOWER_INPUTS = ("host",  # Ansible Tower hostname, required
                "username",  # username of ansible tower, required
                "password",  # password of ansible tower, required
                "verify_ssl"  # optional, default is false.
                )

# Amazon web service, all are compulsory.
AWS_INPUTS = ("username",  # ACCESS KEY
              "password"  # SECRET KEY
              )
# Amazon web service which includes optional security_token
AWS_INPUTS_OPTION = ("username",  # ACCESS KEY
                     "password",  # SECRET KEY
                     "security_token"  # STS token
                     )

# openstack username, password and projects are compulsory.
OPENSTACK_INPUTS = ("username",
                    "password",  # API key
                    "host"  # AUTHENTICATION URL
                    "verify_ssl"  # optional, default is false
                    )

# Github and Gitlab shares the same inputs. For consistency a tuple is used.
GITLAB_TOKEN_INPUTS = ("token",  # the only compulsory key for gitlab/github
                       )

# Two variants of Hashivaults.
HASHIVAULT_KV_INPUTS = ("url",  # hashicorp vault url.
                        "token",  # Hashicorp vault needs to be unsealed before a token can be used.
                        "api_version"  # Could be the kv version 1 or version 2.
                        )
HASHIVAULT_SSH_INPUTS = ("url", "token")


def inputs_validator(inputs: Union[Dict[str, str], Dict[str, int], Dict[str, bool]],
                     inputs_tuple: Tuple[str]) -> Dict[str, Any]:
    """
    This function helps to validate the keys of inputs which is optional for credential creation.
    See Ansible Tower API reference guide.
    :param inputs_tuple:
        The tuple that describes the params of the inputs.
    :param inputs:
        dictionary which has the data required for different types of credentials.
    :return:
        dictionary of validated data.
    """
    # Preserve the original inputs, and use test_the_inputs for testing.
    test_the_inputs = inputs.copy()
    for k in test_the_inputs:
        # Validate if the keys in inputs conforms inputs_tuple.
        if k not in inputs_tuple:
            # Remove invalid keys from inputs.
            inputs.pop(k)
    # Obliterate test_the_inputs after testing.
    del test_the_inputs
    gc.collect()
    # returns the conformed inputs
    return inputs
