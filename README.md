## Overview

This repository contains the infrastructure-as-code and automation tooling built for NimbusKart, a fictional e-commerce client whose AWS bill grew from ~$400/month to ~$2,100/month due to orphaned and untagged cloud resources. It provisions a baseline staging environment on LocalStack using Terraform, runs a Python-based Cost Janitor script to detect wasteful resources, and wires everything into a GitHub Actions CI/CD pipeline so cost hygiene is enforced on every PR.

## How to run locally

```bash
git clone https://github.com/bhavyanjain3004/devops-assignment.git
cd devops-assignment

# Start LocalStack (community edition)
docker run -d -p 4566:4566 --name localstack localstack/localstack:3.0.0

# Wait 25 seconds for LocalStack to boot, then verify
sleep 25 && curl http://localhost:4566/_localstack/health

# Install terraform-local wrapper
pip3 install terraform-local

# Initialize and apply Terraform
cd terraform
tflocal init
tflocal apply -auto-approve

# View outputs
tflocal output
```

## Architecture

## Architecture

```
+--------------------------------------------------+
|  LocalStack                                      |
|                                                  |
|  +----------------------------------------------+|
|  |  VPC (10.20.0.0/16)                          ||
|  |                                              ||
|  |  +-----------------+  +-----------------+   ||
|  |  | Subnet A        |  | Subnet B        |   ||
|  |  | us-east-1a      |  | us-east-1b      |   ||
|  |  | [EC2: web-a]    |  | [EC2: web-b]    |   ||
|  |  +-----------------+  +-----------------+   ||
|  |                                              ||
|  |  [Security Group]    [EBS orphan volume]    ||
|  |  80/443 open         unattached             ||
|  |  22 restricted                              ||
|  +----------------------------------------------+|
|                                                  |
|  +----------------------------------------------+|
|  |  S3: nimbus-kart-app-logs (versioning on)    ||
|  +----------------------------------------------+|
+--------------------------------------------------+
```

## Decisions & deviations

- Used localstack 3.0.0 instead of latest version as newer version need paid auth token.

 ## Trade-offs

## AI usage disclosure
- Used Claude to help structure Terraform module layout and debug localstack provider configuration.
