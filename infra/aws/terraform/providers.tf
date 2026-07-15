terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  # Remote state — create this S3 bucket + DynamoDB lock table once, out-of-band,
  # then uncomment. Keeping state local is fine for a solo portfolio deployment.
  # backend "s3" {
  #   bucket         = "fingpt-enterprise-tfstate"
  #   key            = "prod/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "fingpt-enterprise-tf-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}
