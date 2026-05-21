# Pricing constants for AWS resources
# Source: https://aws.amazon.com/ebs/pricing/ (us-east-1, as of 2026)
EBS_GP3_COST_PER_GB_MONTH = 0.08  # $0.08/GB-month for gp3

# Source: https://aws.amazon.com/ec2/pricing/on-demand/ (t3.micro, us-east-1)
EC2_T3_MICRO_COST_PER_HOUR = 0.0104  # $0.0104/hour
EC2_T3_MICRO_COST_PER_MONTH = EC2_T3_MICRO_COST_PER_HOUR * 24 * 30  # ~$7.49/month

# Source: https://aws.amazon.com/ec2/pricing/on-demand/ (Elastic IPs)
ELASTIC_IP_COST_PER_HOUR = 0.005  # $0.005/hour when not associated
ELASTIC_IP_COST_PER_MONTH = ELASTIC_IP_COST_PER_HOUR * 24 * 30  # ~$3.60/month

# Required tags that every resource must have
REQUIRED_TAGS = ["Project", "Environment", "Owner"]

# Default thresholds
DEFAULT_STOPPED_DAYS_THRESHOLD = 14