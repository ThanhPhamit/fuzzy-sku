# Configure Terraform and required providers
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration - update with your actual backend
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "fuzzy-sku/production/terraform.tfstate"
    region         = "ap-northeast-3"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  # Default tags for all resources
  default_tags {
    tags = {
      Environment = "production"
      Project     = "fuzzy-sku"
      ManagedBy   = "terraform"
      Owner       = "lg-vietnam"
      CostCenter  = "engineering"
      CreatedAt   = timestamp()
    }
  }
}
