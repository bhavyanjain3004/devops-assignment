# Design Note — Hardening, Scaling, and Productionising the Cost Janitor

## Multi-cloud reality

To support GCP and Azure without rewriting the core. 

```
janitor/
├── core/
│   ├── scanner.py     <- orchestrator, cloud-agnostic
│   ├── models.py      <- Finding dataclass, shared schema
│   └── report.py      <- JSON + Markdown output
├── providers/
│   ├── base.py        <- Abstract base class
│   ├── aws.py         <- boto3 implementation
│   ├── gcp.py         <- google-cloud-compute
│   └── azure.py       <- azure-mgmt-compute
└── janitor.py         <- CLI, loads provider via --cloud flag
```

When GCP comes in next quarter, someone writes `gcp.py` implementing the same interface as `aws.py`. The core scanner, the report format, the CI pipeline — none of that changes. That is the only structure worth building.

## Permissions

In dry-run mode the Janitor only needs to read. Nothing else. Here is the exact policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CostJanitorReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeInstances",
        "ec2:DescribeAddresses",
        "ec2:DescribeTags",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

Delete mode adds `ec2:DeleteVolume`, `ec2:TerminateInstances`, and `ec2:ReleaseAddress` — but these should be scoped with a condition that only allows deletion of resources tagged `ManagedBy=terraform`. You do not want a bug in the Janitor to be able to touch manually created production resources.

## Safety net

**Failure mode 1 — The volume that looks orphaned but isn't:**
When an EC2 instance is stopped and restarted, its root volume briefly appears in "available" state. A naive scanner sees this, flags it, and if auto-delete is on, destroys it before the instance comes back up. The instance is now unbootable. The fix: never delete a volume on the first scan it appears orphaned. Write a `JanitorFirstSeenDate` tag on detection, and only action it after 7 days of continuous unattached state.

**Failure mode 2 — The stopped instance that is meant to be stopped:**
A developer stops their test instance on Friday night to save money. The Janitor runs on Monday, sees it has been stopped for 14+ days (counting from launch, not from stop time), and terminates it along with all its data. The fix: send an SNS notification 48 hours before any planned termination. Give the team a chance to tag it `Protected=true` or restart it. Auto-deletion without a human checkpoint is the wrong default for instances.

## Observability

The FinOps team should not have to run the Janitor manually to know if it is working. These five metrics tell the story:

| Metric | Source | Alert threshold |
|--------|--------|-----------------|
| `janitor.orphans_found` | CloudWatch custom metric | > 10 in one scan — something is being left behind consistently |
| `janitor.estimated_waste_usd` | CloudWatch custom metric | > $500/month — escalate to engineering lead |
| `janitor.scan_duration_seconds` | CloudWatch custom metric | > 300s — likely hitting API rate limits |
| `janitor.errors_total` | CloudWatch Logs metric filter | > 0 — any error means the scan is incomplete |
| `janitor.resources_deleted` | CloudWatch custom metric | > 20 in one run — something has gone wrong, pause and alert |

All metrics go to CloudWatch under `NimbusKart/CostJanitor`. A daily SNS digest goes to the FinOps team so they have a paper trail even on quiet days.

## What I did not build

Multi-account support, RDS and ElastiCache scanning, Slack notifications, and a trend dashboard were all left out not because they are hard, but because none of them matter until the core detection is trustworthy.
