variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "alert_email" {
  description = "Email address for SNS alerts"
  type        = string
  default     = "admin@example.com"
}

variable "min_instances" {
  description = "Minimum number of Linux VMs in auto-scaled monitoring cluster"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of Linux VMs in auto-scaled monitoring cluster"
  type        = number
  default     = 5
}

variable "instance_type" {
  description = "EC2 instance size for provisioned Linux worker VMs"
  type        = string
  default     = "t3.medium"
}
