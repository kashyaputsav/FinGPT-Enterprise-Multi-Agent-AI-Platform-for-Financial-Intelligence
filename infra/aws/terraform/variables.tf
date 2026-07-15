variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix used for naming all resources"
  type        = string
  default     = "fingpt-enterprise"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "availability_zones" {
  type    = list(string)
  default = ["ap-south-1a", "ap-south-1b"]
}

variable "container_image" {
  description = "Full ECR image URI:tag pushed by CI/CD; overridden per-deploy"
  type        = string
  default     = "REPLACE_WITH_ECR_IMAGE_URI:latest"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "fargate_cpu" {
  description = "Fargate task CPU units (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "fargate_memory" {
  description = "Fargate task memory in MiB"
  type        = number
  default     = 2048
}

variable "desired_count" {
  description = "Number of running ECS tasks (behind the ALB)"
  type        = number
  default     = 2
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_name" {
  type    = string
  default = "fingpt_enterprise"
}

variable "db_username" {
  type      = string
  default   = "fingpt"
  sensitive = true
}

variable "db_password" {
  description = "RDS master password — pass via -var or TF_VAR_db_password, never commit"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT signing secret — pass via -var or TF_VAR_jwt_secret_key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for the ALB HTTPS listener (must be in the same region)"
  type        = string
}
