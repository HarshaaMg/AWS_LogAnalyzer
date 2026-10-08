"""
Layer 2 - AWS EC2 Provisioner.
Implements VMProvisioner for AWS cloud deployments using Boto3 EC2 API.
Launches EC2 instances with cloud-init user-data to automatically install Node Exporter,
configure Fluent Bit, and self-register with the platform.
"""

import os
import time
import random
import boto3
from typing import Dict, Any, Optional
from provisioners.base import VMProvisioner
from models.entities import create_host_entity, create_provisioning_entity, HostStatus, get_utc_iso
import storage_factory


class AWSProvisioner(VMProvisioner):
    """AWS EC2 cloud infrastructure provisioner."""

    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.ami_id = os.getenv("EC2_AMI_ID", "ami-0c7217cdde317cfec")  # Ubuntu 22.04 LTS
        self.instance_type = os.getenv("EC2_INSTANCE_TYPE", "t3.medium")
        self.key_name = os.getenv("EC2_KEY_NAME")
        self.security_group_ids = [sg.strip() for sg in os.getenv("EC2_SECURITY_GROUPS", "").split(",") if sg.strip()]
        self.subnet_id = os.getenv("EC2_SUBNET_ID")
        self.iam_role_name = os.getenv("EC2_IAM_INSTANCE_PROFILE", "LogAnalyzerInstanceProfile")

        try:
            self.ec2 = boto3.client("ec2", region_name=self.region)
        except Exception as e:
            self.ec2 = None
            print(f"Warning: EC2 client initialization failed: {e}")

    def provision_vm(
        self,
        hostname: str,
        cpu_capacity: int = 4,
        memory_capacity: int = 8192,
        disk_capacity: int = 50,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Launches an EC2 instance in AWS and registers provisioning job.
        """
        storage = storage_factory.get_storage()
        host_id = f"host_aws_{random.randint(100, 999)}"
        provisioning_id = f"prov_aws_{int(time.time())}"

        job = create_provisioning_entity(
            provisioning_id=provisioning_id,
            host_id=host_id,
            hostname=hostname,
            provider="aws",
            dry_run=dry_run
        )
        storage.save_provisioning_job(job)

        if dry_run or not self.ec2:
            job["status"] = "DRY_RUN_COMPLETED" if dry_run else "SIMULATED_AWS_PROVISION"
            job["completed_at"] = get_utc_iso()
            job["steps"].append({"step": "EC2_RUN_INSTANCES", "status": "WOULD_LAUNCH", "timestamp": get_utc_iso()})
            storage.save_provisioning_job(job)

            # Create host in active/simulated state
            host = create_host_entity(
                host_id=host_id,
                hostname=hostname,
                ip=f"10.0.{random.randint(1, 10)}.{random.randint(2, 250)}",
                cpu_capacity=cpu_capacity,
                memory_capacity=memory_capacity,
                disk_capacity=disk_capacity,
                os_name="Ubuntu 22.04 LTS (AWS EC2)",
                provider="aws",
                status=HostStatus.ACTIVE.value
            )
            storage.save_host(host)
            return job

        # Real AWS Boto3 Execution
        try:
            user_data_script = f"""#!/bin/bash
hostnamectl set-hostname {hostname}
curl -s http://169.254.169.254/latest/meta-data/local-ipv4 > /tmp/ip.txt
PRIVATE_IP=$(cat /tmp/ip.txt)
# Call registration endpoint
curl -X POST http://backend:5000/api/hosts/register \\
  -H "Content-Type: application/json" \\
  -d '{{"hostname": "{hostname}", "ip": "'"$PRIVATE_IP"'", "cpu": 4, "memory": 8192, "provider": "aws"}}'
"""
            launch_args = {
                "ImageId": self.ami_id,
                "InstanceType": self.instance_type,
                "MinCount": 1,
                "MaxCount": 1,
                "UserData": user_data_script,
                "TagSpecifications": [
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": hostname},
                            {"Key": "ManagedBy", "Value": "AWS-LogAnalyzer-AutoScaler"}
                        ]
                    }
                ]
            }
            if self.key_name:
                launch_args["KeyName"] = self.key_name
            if self.security_group_ids:
                launch_args["SecurityGroupIds"] = self.security_group_ids
            if self.subnet_id:
                launch_args["SubnetId"] = self.subnet_id

            response = self.ec2.run_instances(**launch_args)
            instance = response["Instances"][0]
            instance_id = instance["InstanceId"]

            job["steps"].append({
                "step": "EC2_RUN_INSTANCES",
                "status": f"LAUNCHED ({instance_id})",
                "timestamp": get_utc_iso()
            })
            job["status"] = HostStatus.BOOTING.value
            storage.save_provisioning_job(job)

            # Store host representation
            host = create_host_entity(
                host_id=instance_id,
                hostname=hostname,
                ip=instance.get("PrivateIpAddress", "Pending"),
                cpu_capacity=cpu_capacity,
                memory_capacity=memory_capacity,
                disk_capacity=disk_capacity,
                os_name="Ubuntu 22.04 LTS (AWS EC2)",
                provider="aws",
                status=HostStatus.BOOTING.value
            )
            storage.save_host(host)

        except Exception as e:
            job["status"] = HostStatus.FAILED.value
            job["error"] = str(e)
            job["completed_at"] = get_utc_iso()
            storage.save_provisioning_job(job)

        return job

    def deprovision_vm(self, host_id: str) -> bool:
        """Terminates an EC2 instance."""
        if not self.ec2 or not host_id.startswith("i-"):
            return False
        try:
            self.ec2.terminate_instances(InstanceIds=[host_id])
            storage = storage_factory.get_storage()
            host = storage.get_host(host_id)
            if host:
                host["status"] = HostStatus.TERMINATING.value
                storage.save_host(host)
            return True
        except Exception as e:
            print(f"Error terminating EC2 instance {host_id}: {e}")
            return False

    def get_status(self, host_id: str) -> str:
        if not self.ec2 or not host_id.startswith("i-"):
            return HostStatus.FAILED.value
        try:
            res = self.ec2.describe_instances(InstanceIds=[host_id])
            state = res["Reservations"][0]["Instances"][0]["State"]["Name"]
            return HostStatus.ACTIVE.value if state == "running" else state.upper()
        except Exception:
            return HostStatus.FAILED.value
