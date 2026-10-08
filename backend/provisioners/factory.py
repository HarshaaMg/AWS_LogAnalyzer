"""
Provisioner factory returning the active VMProvisioner (VMware or AWS).
"""

import os
from provisioners.base import VMProvisioner
from provisioners.vmware_provisioner import VMwareProvisioner
from provisioners.aws_provisioner import AWSProvisioner


def get_provisioner() -> VMProvisioner:
    """Returns the configured infrastructure provisioner."""
    provider_type = os.getenv("PROVISIONER_TYPE", "vmware").lower()
    if provider_type == "aws":
        return AWSProvisioner()
    return VMwareProvisioner()
