variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name for tagging"
  type        = string
  default     = "nimbus-kart"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "devops-team"
}

variable "ssh_cidr" {
  description = "CIDR block allowed for SSH — do not use 0.0.0.0/0 in production"
  type        = string
  default     = "10.20.0.0/16"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ebs_volume_size" {
  description = "Size of the orphan EBS volume in GB"
  type        = number
  default     = 20
}

variable "log_bucket_name" {
  description = "Name of the S3 bucket for application logs"
  type        = string
  default     = "nimbus-kart-app-logs"
}