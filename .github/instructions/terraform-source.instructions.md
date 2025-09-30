# GitHub Copilot Instructions for Infrastructure Source Code

## 🏗️ STANDARD TERRAFORM MODULE CREATION

### Required file structure for each module:

```
modules/
  ├── module_name/
      ├── main.tf           # Main resources
      ├── variables.tf      # Input variable declarations
      ├── outputs.tf        # Output value exports
      ├── data.tf           # Data sources (if needed)
      ├── versions.tf       # Provider version constraints
      ├── README.md         # Documentation
      └── templates/        # Template files (if needed)
```

### Naming and structure rules:

#### 1. **variables.tf** - Variable declaration rules:

```hcl
# Required variables: app_name, tags
variable "app_name" {
  description = "Application name for resource naming"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Other variables follow pattern: type + description + validation (if needed)
variable "vpc_id" {
  description = "VPC ID where resources will be created"
  type        = string
}

variable "enable_feature" {
  description = "Enable specific feature"
  type        = bool
  default     = false
}

# Sensitive variables
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
```

#### 2. **main.tf** - Resource creation rules:

```hcl
# Name resources following pattern: service_purpose
resource "aws_security_group" "this" {
  name_prefix = "${var.app_name}-"
  description = "Security group for ${var.app_name}"
  vpc_id      = var.vpc_id

  # Always merge tags from variable with specific tags
  tags = merge(var.tags, {
    Name = "${var.app_name}-security-group"
  })
}

# Use locals for complex logic
locals {
  # Calculate cluster names based on naming convention
  cluster_names = [
    for i in range(var.cluster_count) :
    "${var.app_name}-cluster-${format("%03d", i + 1)}"
  ]
}
```

#### 3. **outputs.tf** - Output value rules:

```hcl
# Export all important information that other modules need
output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.this.id
}

output "arn" {
  description = "ARN of the main resource"
  value       = aws_resource.main.arn
}

# Export complex object if needed
output "endpoint_info" {
  description = "Endpoint information"
  value = {
    address = aws_resource.main.endpoint
    port    = aws_resource.main.port
    arn     = aws_resource.main.arn
  }
}
```

#### 4. **data.tf** - Data source rules:

```hcl
# Only use data source for external information
data "aws_vpc" "this" {
  id = var.vpc_id
}

data "aws_region" "current" {}

# DO NOT use data source for resources you create in the same terraform run
# Only use when resources already exist
```

### 🔗 MODULE INTERCONNECTION RULES

#### How to pass data between modules:

```hcl
# In environment main.tf
module "network" {
  source = "../modules/network"

  app_name = "${var.environment}-${var.app_name}"
  vpc_id   = data.aws_vpc.this.id
  tags     = local.tags
}

module "ecs_service" {
  source = "../modules/ecs_service"

  app_name              = "${var.environment}-${var.app_name}"
  vpc_id                = data.aws_vpc.this.id
  security_group_id     = module.network.security_group_id  # From output
  subnet_ids            = module.network.subnet_ids         # From output

  # Environment specific values
  task_count = var.ecs_task_count

  tags = local.tags
}
```

## 🌍 HOW TO USE ACROSS ENVIRONMENTS

### Environment file structure:

```
environment_name/
  ├── main.tf           # Call modules + resources
  ├── variables.tf      # Environment variable declarations
  ├── terraform.tfvars  # Specific value assignments
  ├── locals.tf         # Local calculation logic
  ├── data.tf           # Common data sources
  ├── backend.tf        # Backend configuration
  ├── providers.tf      # Provider settings
  ├── outputs.tf        # Environment outputs
  └── versions.tf       # Version constraints
```

#### **locals.tf** - Standard pattern:

```hcl
locals {
  # Common tags for entire environment
  tags = {
    "Project"     = "project-name"
    "ManagedBy"   = "team-name"
    "Environment" = "staging|production|development"
    "CostCenter"  = "department"
  }

  # Calculate naming convention
  app_full_name = "${var.environment}-${var.app_name}"

  # Aggregate data from multiple data sources
  private_subnet_ids = [for subnet in data.aws_subnet.private : subnet.id]
}
```

#### **main.tf** - Module calling pattern:

```hcl
# Always pass app_name with environment prefix
module "module_name" {
  source = "../modules/module_name"

  # Required variables
  app_name = "${var.environment}-${var.app_name}"
  vpc_id   = data.aws_vpc.this.id

  # Module specific variables
  specific_config = var.module_specific_config

  # Dependencies from other modules
  dependency_output = module.other_module.output_value

  # Always pass tags
  tags = local.tags
}
```

## 🏷️ TAGS AND NAMING STANDARDS

### Tag Strategy:

```hcl
# In environment locals.tf
locals {
  tags = {
    "Project"       = "welfan-warehouse-management-system"
    "ManagedBy"     = "LionGarden.Inc"
    "Environment"   = var.environment  # staging/production/development
    "Component"     = "backend|frontend|database|cache"
    "Owner"         = "team-name"
    "CostCenter"    = "engineering"
    "Backup"        = "daily|weekly|none"
    "Monitoring"    = "enabled|disabled"
  }
}

# In module variables.tf
variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# In module main.tf
resource "aws_resource" "this" {
  # Resource configuration...

  tags = merge(var.tags, {
    Name      = "${var.app_name}-resource-name"
    Component = "specific-component"
  })
}
```

### Naming Convention:

```hcl
# Pattern: ${environment}-${app_name}-${component}-${purpose}
# Examples:
"staging-wms-ecs-cluster"
"production-wms-rds-primary"
"staging-wms-alb-internal"
"production-wms-cache-primary"
```

## ⚠️ IMPORTANT NOTES WHEN USING COPILOT

### 1. **Dependency Management:**

```hcl
# ❌ WRONG: Use data source for resource not yet created
data "aws_elasticache_cluster" "redis" {
  cluster_id = aws_elasticache_replication_group.redis.id  # Doesn't exist yet
}

# ✅ CORRECT: Use output directly or deploy in stages
output "cluster_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}
```

### 2. **Variable Validation:**

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = contains(["staging", "production", "development"], var.environment)
    error_message = "Environment must be staging, production, or development."
  }
}
```

### 3. **Conditional Resources:**

```hcl
# Use count or for_each for conditional resources
resource "aws_vpc_endpoint" "ssm" {
  count = var.enable_ecs_exec ? 1 : 0
  # Resource configuration...
}
```

### 4. **Security Best Practices:**

```hcl
# Always use restrictive security groups
resource "aws_security_group_rule" "specific_access" {
  type                     = "ingress"
  from_port                = var.port
  to_port                  = var.port
  protocol                 = "tcp"
  source_security_group_id = var.allowed_sg_id  # Don't use 0.0.0.0/0
  security_group_id        = aws_security_group.this.id
}
```

---

**This file guides creating and using Terraform modules following enterprise standards, ensuring consistency, security and maintainability.**
