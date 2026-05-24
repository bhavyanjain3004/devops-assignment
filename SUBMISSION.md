# Submission — DevOps Engineer Assignment

**Candidate name:** Bhavya Jain
**Email:** bhavyajain3004@gmail.com
**Date submitted:** 2026-05-24
**Hours spent (approximate):** 8

## Deliverables checklist

- [x] Part A: Terraform code under /terraform applies cleanly on LocalStack
- [x] Part A: `terraform validate` and `terraform fmt -check` both pass
- [x] Part B: Janitor script runs in --dry-run mode and produces report.json
- [x] Part B: GitHub Actions workflow runs green on a fresh PR
- [x] Part B: --delete mode respects Protected=true tag
- [x] Part C: DESIGN.md is present and within 2 pages
- [x] Walkthrough video link below is accessible (unlisted is fine)

## Walkthrough video

Link: https://drive.google.com/file/d/1kM_QUkqz_fyfF0e1NIuDK5CcS220Qfkk/view?usp=sharing

## Sample report

Path to a sample report.json produced by your script: samples/report.example.json

## Known limitations

- S3 lifecycle rule removed from Terraform due to LocalStack community edition timeout
- Used LocalStack 3.0.0 instead of latest as newer versions require a paid auth token
- Stopped EC2 age detection uses LaunchTime as proxy since LocalStack does not populate StateTransitionReason accurately

## AI usage disclosure

- Used Claude to help structure Terraform module layout and debug LocalStack provider configuration
- Claude initially suggested localstack/localstack:latest which requires a paid license — caught this when the container failed with a license error and switched to 3.0.0