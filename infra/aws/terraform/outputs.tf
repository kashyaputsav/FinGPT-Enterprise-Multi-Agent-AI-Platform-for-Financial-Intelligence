output "alb_dns_name" {
  description = "Public DNS name of the load balancer — point your domain's CNAME/ALIAS here"
  value       = aws_lb.app.dns_name
}

output "ecr_repository_url" {
  description = "Push your Docker image here from CI/CD"
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.app.name
}

output "rds_endpoint" {
  value     = aws_db_instance.postgres.endpoint
  sensitive = true
}

output "s3_documents_bucket" {
  value = aws_s3_bucket.documents.bucket
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.app.name
}
