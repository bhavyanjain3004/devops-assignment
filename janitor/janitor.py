#!/usr/bin/env python3
"""
Cost Janitor — detects orphaned AWS resources and produces a cost report.
Works against LocalStack or real AWS.
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import boto3
from botocore.config import Config

from constants import (
    EBS_GP3_COST_PER_GB_MONTH,
    EC2_T3_MICRO_COST_PER_MONTH,
    ELASTIC_IP_COST_PER_MONTH,
    REQUIRED_TAGS,
    DEFAULT_STOPPED_DAYS_THRESHOLD,
)


def get_boto3_clients(endpoint_url=None, region="us-east-1"):
    config = Config(region_name=region)
    kwargs = dict(
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name=region,
        config=config,
    )
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url

    ec2 = boto3.client("ec2", **kwargs)
    s3 = boto3.client("s3", **kwargs)
    sts = boto3.client("sts", **kwargs)
    return ec2, s3, sts


def get_account_id(sts):
    try:
        return sts.get_caller_identity()["Account"]
    except Exception:
        return "000000000000"


def age_days(dt):
    if dt is None:
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).days


def check_tags(tags_list):
    tags = {t["Key"]: t["Value"] for t in (tags_list or [])}
    missing = [r for r in REQUIRED_TAGS if r not in tags or not tags[r]]
    return tags, missing


def scan_unattached_ebs(ec2):
    findings = []
    response = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )
    for vol in response.get("Volumes", []):
        tags, missing = check_tags(vol.get("Tags", []))
        size = vol.get("Size", 0)
        cost = size * EBS_GP3_COST_PER_GB_MONTH
        protected = tags.get("Protected", "").lower() == "true"
        findings.append({
            "resource_id": vol["VolumeId"],
            "resource_type": "ebs_volume",
            "reason": "unattached",
            "age_days": age_days(vol.get("CreateTime")),
            "estimated_monthly_cost_usd": round(cost, 2),
            "tags": {r: tags.get(r) for r in REQUIRED_TAGS},
            "suggested_action": "delete",
            "safe_to_auto_delete": not protected and not missing,
            "protected": protected,
        })
    return findings


def scan_stopped_ec2(ec2, stopped_days_threshold):
    findings = []
    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
    )
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            tags, missing = check_tags(instance.get("Tags", []))
            stopped_since = instance.get("StateTransitionReason", "")
            launch_time = instance.get("LaunchTime")
            days = age_days(launch_time)
            if days < stopped_days_threshold:
                continue
            protected = tags.get("Protected", "").lower() == "true"
            findings.append({
                "resource_id": instance["InstanceId"],
                "resource_type": "ec2_instance",
                "reason": f"stopped for more than {stopped_days_threshold} days",
                "age_days": days,
                "estimated_monthly_cost_usd": round(EC2_T3_MICRO_COST_PER_MONTH, 2),
                "tags": {r: tags.get(r) for r in REQUIRED_TAGS},
                "suggested_action": "terminate",
                "safe_to_auto_delete": not protected and not missing,
                "protected": protected,
            })
    return findings


def scan_unassociated_eips(ec2):
    findings = []
    response = ec2.describe_addresses()
    for addr in response.get("Addresses", []):
        if addr.get("AssociationId"):
            continue
        tags, missing = check_tags(addr.get("Tags", []))
        protected = tags.get("Protected", "").lower() == "true"
        findings.append({
            "resource_id": addr.get("AllocationId", addr.get("PublicIp", "unknown")),
            "resource_type": "elastic_ip",
            "reason": "not associated with any instance",
            "age_days": 0,
            "estimated_monthly_cost_usd": round(ELASTIC_IP_COST_PER_MONTH, 2),
            "tags": {r: tags.get(r) for r in REQUIRED_TAGS},
            "suggested_action": "release",
            "safe_to_auto_delete": not protected,
            "protected": protected,
        })
    return findings


def scan_untagged_resources(ec2):
    findings = []
    # Check EC2 instances
    response = ec2.describe_instances()
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            if instance.get("State", {}).get("Name") == "terminated":
                continue
            tags, missing = check_tags(instance.get("Tags", []))
            if missing:
                findings.append({
                    "resource_id": instance["InstanceId"],
                    "resource_type": "ec2_instance",
                    "reason": f"missing required tags: {', '.join(missing)}",
                    "age_days": age_days(instance.get("LaunchTime")),
                    "estimated_monthly_cost_usd": 0.0,
                    "tags": {r: tags.get(r) for r in REQUIRED_TAGS},
                    "suggested_action": "tag",
                    "safe_to_auto_delete": False,
                    "protected": False,
                })
    # Check EBS volumes
    vol_response = ec2.describe_volumes()
    for vol in vol_response.get("Volumes", []):
        tags, missing = check_tags(vol.get("Tags", []))
        if missing:
            findings.append({
                "resource_id": vol["VolumeId"],
                "resource_type": "ebs_volume",
                "reason": f"missing required tags: {', '.join(missing)}",
                "age_days": age_days(vol.get("CreateTime")),
                "estimated_monthly_cost_usd": 0.0,
                "tags": {r: tags.get(r) for r in REQUIRED_TAGS},
                "suggested_action": "tag",
                "safe_to_auto_delete": False,
                "protected": False,
            })
    return findings


def delete_resources(ec2, findings, dry_run=True):
    for finding in findings:
        if finding.get("protected"):
            print(f"  SKIPPING protected resource: {finding['resource_id']}")
            continue
        if not finding.get("safe_to_auto_delete"):
            print(f"  SKIPPING unsafe resource: {finding['resource_id']}")
            continue
        if dry_run:
            print(f"  [DRY RUN] Would delete: {finding['resource_id']}")
            continue
        resource_type = finding["resource_type"]
        resource_id = finding["resource_id"]
        try:
            if resource_type == "ebs_volume" and finding["reason"] == "unattached":
                ec2.delete_volume(VolumeId=resource_id)
                print(f"  DELETED volume: {resource_id}")
            elif resource_type == "elastic_ip":
                ec2.release_address(AllocationId=resource_id)
                print(f"  RELEASED EIP: {resource_id}")
            elif resource_type == "ec2_instance":
                ec2.terminate_instances(InstanceIds=[resource_id])
                print(f"  TERMINATED instance: {resource_id}")
        except Exception as e:
            print(f"  ERROR deleting {resource_id}: {e}")


def generate_markdown(report):
    lines = [
        "# Cost Janitor Report",
        f"**Scan time:** {report['scan_timestamp']}",
        f"**Account:** {report['account_id']}",
        f"**Region:** {report['region']}",
        "",
        "## Summary",
        f"- Total orphans found: **{report['summary']['total_orphans']}**",
        f"- Estimated monthly waste: **${report['summary']['estimated_monthly_waste_usd']:.2f}**",
        "",
        "## Findings",
    ]
    if not report["findings"]:
        lines.append("No orphaned resources found.")
    else:
        lines.append("| Resource ID | Type | Reason | Age (days) | Est. Cost/month |")
        lines.append("|-------------|------|--------|------------|-----------------|")
        for f in report["findings"]:
            lines.append(
                f"| {f['resource_id']} | {f['resource_type']} | "
                f"{f['reason']} | {f['age_days']} | "
                f"${f['estimated_monthly_cost_usd']:.2f} |"
            )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Cost Janitor — AWS orphan resource scanner")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default)")
    parser.add_argument("--delete", action="store_true", default=False, help="Delete orphaned resources")
    parser.add_argument("--endpoint-url", default="http://localhost:4566", help="AWS endpoint URL")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--stopped-days", type=int, default=DEFAULT_STOPPED_DAYS_THRESHOLD)
    parser.add_argument("--output", default="report.json", help="Output JSON file path")
    parser.add_argument("--output-md", default="report.md", help="Output Markdown file path")
    args = parser.parse_args()

    dry_run = not args.delete

    ec2, s3, sts = get_boto3_clients(
        endpoint_url=args.endpoint_url,
        region=args.region,
    )

    print("Scanning for orphaned resources...")
    findings = []
    findings += scan_unattached_ebs(ec2)
    findings += scan_stopped_ec2(ec2, args.stopped_days)
    findings += scan_unassociated_eips(ec2)
    findings += scan_untagged_resources(ec2)

    # Deduplicate by resource_id + reason
    seen = set()
    unique_findings = []
    for f in findings:
        key = (f["resource_id"], f["reason"])
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    total_waste = sum(f["estimated_monthly_cost_usd"] for f in unique_findings)

    report = {
        "scan_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "account_id": get_account_id(sts),
        "region": args.region,
        "summary": {
            "total_orphans": len(unique_findings),
            "estimated_monthly_waste_usd": round(total_waste, 2),
        },
        "findings": unique_findings,
    }

    # Write JSON report
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Report written to {args.output}")

    # Write Markdown report
    md = generate_markdown(report)
    with open(args.output_md, "w") as f:
        f.write(md)
    print(f"Markdown written to {args.output_md}")

    if args.delete:
        print("\nRunning in DELETE mode...")
        delete_resources(ec2, unique_findings, dry_run=False)
    else:
        print("\nRunning in DRY RUN mode...")
        delete_resources(ec2, unique_findings, dry_run=True)

    if unique_findings:
        print(f"\nFound {len(unique_findings)} orphaned resources!")
        sys.exit(1)
    else:
        print("\nNo orphaned resources found.")
        sys.exit(0)


if __name__ == "__main__":
    main()