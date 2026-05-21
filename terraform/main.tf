terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
    iam = "http://localhost:4566"
  }
}

module "network" {
  source      = "./modules/network"
  project     = var.project
  environment = var.environment
  owner       = var.owner
  ssh_cidr    = var.ssh_cidr
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "web_a" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = module.network.subnet_a_id
  vpc_security_group_ids = [module.network.security_group_id]

  tags = {
    Name        = "${var.project}-${var.environment}-web-a"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
    Tier        = "web"
  }
}

resource "aws_instance" "web_b" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = module.network.subnet_b_id
  vpc_security_group_ids = [module.network.security_group_id]

  tags = {
    Name        = "${var.project}-${var.environment}-web-b"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
    Tier        = "web"
  }
}

resource "aws_s3_bucket" "app_logs" {
  bucket        = var.log_bucket_name
  force_destroy = true

  tags = {
    Name        = var.log_bucket_name
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "app_logs" {
  bucket = aws_s3_bucket.app_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_ebs_volume" "orphan" {
  availability_zone = "us-east-1a"
  size              = var.ebs_volume_size
  type              = "gp3"

  tags = {
    Name        = "${var.project}-${var.environment}-orphan-vol"
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}
