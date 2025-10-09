terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.86.1"
      configuration_aliases = [
        aws,
        aws.virginia
      ]
    }
  }
}

