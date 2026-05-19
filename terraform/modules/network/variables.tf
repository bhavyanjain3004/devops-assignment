variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "project" {
  description = "Project name for tagging"
  type        = string
}

variable "environment" {
  description = "Environment name for tagging"
  type        = string
}

variable "owner" {
  description = "Owner tag value"
  type        = string
}

variable "ssh_cidr" {
  description = "CIDR allowed for SSH access on port 22"
  type        = string
  default     = "10.20.0.0/16"
}