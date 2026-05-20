output "vpc_id" {
  description = "ID of the VPC"
  value       = module.network.vpc_id
}

output "subnet_a_id" {
  description = "ID of public subnet A"
  value       = module.network.subnet_a_id
}

output "subnet_b_id" {
  description = "ID of public subnet B"
  value       = module.network.subnet_b_id
}

output "bucket_name" {
  description = "Name of the S3 log bucket"
  value       = aws_s3_bucket.app_logs.id
}

output "orphan_ebs_volume_id" {
  description = "ID of the intentionally unattached EBS volume"
  value       = aws_ebs_volume.orphan.id
}

output "web_instance_a_id" {
  description = "ID of web instance A"
  value       = aws_instance.web_a.id
}

output "web_instance_b_id" {
  description = "ID of web instance B"
  value       = aws_instance.web_b.id
}