# Lambda Function Development Guide for Terraform

## 🚀 Overview

The `terraform-aws-modules/lambda/aws` module provides automatic building, packaging, and deployment of Lambda functions with dependencies. It's the Terraform equivalent to CDK's NodejsFunction and PythonFunction constructs.

## 🏗️ Module Structure for Lambda Functions

```
modules/
  ├── lambda_function/
      ├── main.tf           # Lambda module configuration
      ├── variables.tf      # Lambda-specific variables
      ├── outputs.tf        # Function ARN, name, etc.
      ├── versions.tf       # Provider constraints
      ├── README.md         # Documentation
      └── src/              # Lambda source code
          ├── nodejs/       # Node.js functions
          │   ├── index.js
          │   └── package.json
          ├── python/       # Python functions
          │   ├── index.py
          │   └── requirements.txt
          └── layers/       # Lambda layers
              └── dependencies/
```

## 📋 Required Variables Pattern

```hcl
# modules/lambda_function/variables.tf
variable "app_name" {
  description = "Application name for Lambda naming"
  type        = string
}

variable "function_name" {
  description = "Lambda function name (will be prefixed with app_name)"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  validation {
    condition = contains([
      "nodejs18.x", "nodejs20.x",
      "python3.9", "python3.10", "python3.11", "python3.12",
      "go1.x", "java11", "java17", "dotnet6"
    ], var.runtime)
    error_message = "Runtime must be a supported Lambda runtime."
  }
}

variable "handler" {
  description = "Lambda function handler"
  type        = string
  default     = "index.handler"
}

variable "timeout" {
  description = "Lambda function timeout in seconds (1-900)"
  type        = number
  default     = 30
  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "Timeout must be between 1 and 900 seconds."
  }
}

variable "memory_size" {
  description = "Lambda function memory size in MB (128-10240)"
  type        = number
  default     = 128
  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 10240
    error_message = "Memory size must be between 128 and 10240 MB."
  }
}

variable "environment_variables" {
  description = "Environment variables for Lambda function"
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "vpc_config" {
  description = "VPC configuration for Lambda"
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  default = null
}

variable "policy_statements" {
  description = "IAM policy statements for Lambda"
  type        = any
  default     = {}
}

variable "layers" {
  description = "List of Lambda layer ARNs"
  type        = list(string)
  default     = []
}

variable "build_in_docker" {
  description = "Build Lambda package in Docker for consistency"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "tags" {
  description = "Tags to apply to Lambda resources"
  type        = map(string)
  default     = {}
}
```

## 🔧 Lambda Module Implementation

### Standard Lambda Module (modules/lambda_function/main.tf):

```hcl
# Get current AWS region and account
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Main Lambda function
module "lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.1.0"

  # Basic configuration
  function_name = "${var.app_name}-${var.function_name}"
  description   = var.description
  handler       = var.handler
  runtime       = var.runtime
  timeout       = var.timeout
  memory_size   = var.memory_size

  # Source configuration
  source_path     = var.source_path
  build_in_docker = var.build_in_docker

  # Environment variables
  environment_variables = merge(var.environment_variables, {
    AWS_REGION  = data.aws_region.current.name
    LOG_LEVEL   = var.log_level
    ENVIRONMENT = var.environment
  })

  # VPC configuration (conditional)
  vpc_subnet_ids         = var.vpc_config != null ? var.vpc_config.subnet_ids : null
  vpc_security_group_ids = var.vpc_config != null ? var.vpc_config.security_group_ids : null

  # IAM policies
  attach_policy_statements = length(var.policy_statements) > 0
  policy_statements        = var.policy_statements

  # Lambda layers
  layers = var.layers

  # CloudWatch Logs
  cloudwatch_logs_retention_in_days = var.log_retention_days

  # Dead letter queue (if provided)
  dead_letter_target_arn = var.dead_letter_queue_arn

  # Tags
  tags = merge(var.tags, {
    Name      = "${var.app_name}-${var.function_name}"
    Runtime   = var.runtime
    Component = "lambda"
    ManagedBy = "terraform"
  })
}

# CloudWatch alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = var.enable_monitoring ? 1 : 0

  alarm_name          = "${var.app_name}-${var.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Lambda function error rate is too high"

  dimensions = {
    FunctionName = module.lambda.lambda_function_name
  }

  alarm_actions = var.alarm_actions
  ok_actions    = var.alarm_actions

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  count = var.enable_monitoring ? 1 : 0

  alarm_name          = "${var.app_name}-${var.function_name}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Average"
  threshold           = var.timeout * 1000 * 0.8  # 80% of timeout in milliseconds

  dimensions = {
    FunctionName = module.lambda.lambda_function_name
  }

  alarm_actions = var.alarm_actions
  tags          = var.tags
}
```

### Module Outputs (modules/lambda_function/outputs.tf):

```hcl
output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = module.lambda.lambda_function_arn
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = module.lambda.lambda_function_name
}

output "lambda_function_invoke_arn" {
  description = "The invoke ARN of the Lambda function"
  value       = module.lambda.lambda_function_invoke_arn
}

output "lambda_function_version" {
  description = "Latest published version of Lambda function"
  value       = module.lambda.lambda_function_version
}

output "lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda function"
  value       = module.lambda.lambda_role_arn
}

output "lambda_cloudwatch_log_group_arn" {
  description = "The ARN of the CloudWatch Log Group"
  value       = module.lambda.lambda_cloudwatch_log_group_arn
}

output "lambda_cloudwatch_log_group_name" {
  description = "The name of the CloudWatch Log Group"
  value       = module.lambda.lambda_cloudwatch_log_group_name
}
```

## 🌐 Usage in Environment

### Node.js Lambda Example:

```hcl
# In environment main.tf
module "slack_forwarder" {
  source = "../modules/lambda_function"

  app_name      = "${var.environment}-${var.app_name}"
  function_name = "slack-forwarder"
  description   = "Forward CloudWatch alarms to Slack"
  runtime       = "nodejs20.x"
  handler       = "index.handler"
  timeout       = 30
  memory_size   = 256

  source_path = "${path.module}/lambda/nodejs/slack-forwarder"

  environment_variables = {
    SLACK_WEBHOOK_URL = var.slack_webhook_url
    SLACK_CHANNEL     = var.slack_channel_id
    NODE_ENV          = "production"
  }

  # VPC configuration for private subnet access
  vpc_config = {
    subnet_ids         = [for subnet in data.aws_subnet.private_subnets : subnet.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  # IAM permissions for SSM Parameter Store
  policy_statements = {
    ssm = {
      effect = "Allow"
      actions = [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ]
      resources = [
        "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/slack/*"
      ]
    }
  }

  enable_monitoring = true
  alarm_actions     = [module.chatbot_slack_alert.chatbot_sns_topic_arn]

  tags = local.tags
}
```

### Python Lambda Example:

```hcl
module "data_processor" {
  source = "../modules/lambda_function"

  app_name      = "${var.environment}-${var.app_name}"
  function_name = "data-processor"
  description   = "Process incoming data and store in database"
  runtime       = "python3.12"
  handler       = "index.lambda_handler"
  timeout       = 300
  memory_size   = 512

  source_path     = "${path.module}/lambda/python/data-processor"
  build_in_docker = true  # Ensure consistent Python builds

  environment_variables = {
    DB_HOST     = var.database_host
    DB_NAME     = var.database_name
    PYTHONPATH  = "/var/task"
    LOG_LEVEL   = "INFO"
  }

  # Database access permissions
  policy_statements = {
    rds = {
      effect = "Allow"
      actions = [
        "rds-db:connect"
      ]
      resources = [
        "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${var.db_cluster_id}/${var.db_username}"
      ]
    }
    secretsmanager = {
      effect = "Allow"
      actions = [
        "secretsmanager:GetSecretValue"
      ]
      resources = [
        aws_secretsmanager_secret.db_password.arn
      ]
    }
  }

  tags = local.tags
}
```

## 📁 Source Code Structure Examples

### Node.js Lambda Structure:

```
lambda/nodejs/slack-forwarder/
├── index.js                    # Main handler
├── package.json               # Dependencies
├── package-lock.json          # Lock file
└── lib/
    ├── slack-client.js        # Slack API integration
    ├── message-formatter.js   # Format alarm messages
    └── config.js              # Configuration utilities
```

**Example package.json:**

```json
{
  "name": "slack-forwarder",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "@aws-sdk/client-ssm": "^3.450.0",
    "axios": "^1.6.0"
  }
}
```

**Example index.js:**

```javascript
const { SSMClient, GetParameterCommand } = require('@aws-sdk/client-ssm');
const axios = require('axios');

const ssmClient = new SSMClient({});

exports.handler = async (event) => {
  try {
    // Get Slack webhook URL from Parameter Store
    const webhookUrl = await getParameter('/slack/webhook-url');

    // Process CloudWatch alarm
    const message = formatAlarmMessage(event);

    // Send to Slack
    await axios.post(webhookUrl, {
      channel: process.env.SLACK_CHANNEL,
      text: message,
      username: 'AWS CloudWatch',
    });

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Alert sent successfully' }),
    };
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message }),
    };
  }
};

async function getParameter(name) {
  const command = new GetParameterCommand({
    Name: name,
    WithDecryption: true,
  });
  const response = await ssmClient.send(command);
  return response.Parameter.Value;
}

function formatAlarmMessage(event) {
  // Format CloudWatch alarm for Slack
  const record = JSON.parse(event.Records[0].Sns.Message);
  return `🚨 *${record.AlarmName}*\n${record.AlarmDescription}\nState: ${record.NewStateValue}`;
}
```

### Python Lambda Structure:

```
lambda/python/data-processor/
├── index.py                   # Main handler
├── requirements.txt           # Dependencies
└── lib/
    ├── __init__.py
    ├── database.py            # Database operations
    ├── validators.py          # Data validation
    └── utils.py               # Utility functions
```

**Example requirements.txt:**

```
boto3==1.34.144
psycopg2-binary==2.9.9
pydantic==2.5.0
```

**Example index.py:**

```python
import json
import os
import logging
from typing import Dict, Any
from lib.database import DatabaseManager
from lib.validators import validate_data

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process incoming data and store in database
    """
    try:
        # Initialize database manager
        db_manager = DatabaseManager(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME')
        )

        # Process each record
        processed_count = 0
        for record in event.get('Records', []):
            data = json.loads(record.get('body', '{}'))

            # Validate data
            validated_data = validate_data(data)

            # Store in database
            db_manager.insert_record(validated_data)
            processed_count += 1

        logger.info(f"Successfully processed {processed_count} records")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {processed_count} records successfully'
            })
        }

    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

## 🏷️ Lambda Layers Module

### Layer Module Structure:

```hcl
# modules/lambda_layer/main.tf
module "lambda_layer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.1.0"

  create_function = false
  create_layer    = true

  layer_name               = "${var.app_name}-${var.layer_name}"
  description              = var.description
  compatible_runtimes      = var.compatible_runtimes
  compatible_architectures = var.compatible_architectures

  source_path = var.source_path

  tags = merge(var.tags, {
    Name      = "${var.app_name}-${var.layer_name}"
    Component = "lambda-layer"
  })
}
```

### Using Layers in Environment:

```hcl
# Create shared dependencies layer
module "shared_layer" {
  source = "../modules/lambda_layer"

  app_name        = "${var.environment}-${var.app_name}"
  layer_name      = "shared-deps"
  description     = "Shared dependencies for Lambda functions"
  compatible_runtimes = ["nodejs18.x", "nodejs20.x"]

  source_path = "${path.module}/layers/nodejs-shared"

  tags = local.tags
}

# Use layer in Lambda function
module "api_handler" {
  source = "../modules/lambda_function"

  app_name      = "${var.environment}-${var.app_name}"
  function_name = "api-handler"
  runtime       = "nodejs20.x"

  # Attach the layer
  layers = [module.shared_layer.lambda_layer_arn]

  tags = local.tags
}
```

## 🔐 Security Best Practices

### 1. IAM Principle of Least Privilege:

```hcl
policy_statements = {
  # Specific DynamoDB table access
  dynamodb = {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem"
    ]
    resources = [
      aws_dynamodb_table.specific_table.arn,
      "${aws_dynamodb_table.specific_table.arn}/index/*"
    ]
  }

  # Specific S3 bucket access
  s3 = {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = [
      "${aws_s3_bucket.specific_bucket.arn}/*"
    ]
  }
}
```

### 2. Environment Variables and Secrets:

```hcl
# Use Parameter Store for sensitive data
environment_variables = {
  # Non-sensitive configuration
  ENVIRONMENT = var.environment
  LOG_LEVEL   = "INFO"

  # Reference to Parameter Store for sensitive data
  DB_PASSWORD_PARAM = "/lambda/${var.app_name}/db-password"
}

# Grant access to specific parameters
policy_statements = {
  ssm = {
    effect = "Allow"
    actions = [
      "ssm:GetParameter"
    ]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/lambda/${var.app_name}/*"
    ]
  }
}
```

### 3. VPC Configuration for Private Resources:

```hcl
# Security group for Lambda in VPC
resource "aws_security_group" "lambda" {
  name_prefix = "${var.app_name}-lambda-"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS outbound"
  }

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.database_subnet_cidr]
    description = "PostgreSQL database access"
  }

  tags = merge(var.tags, {
    Name = "${var.app_name}-lambda-sg"
  })
}
```

## 📊 Monitoring and Alerting

### CloudWatch Dashboards:

```hcl
resource "aws_cloudwatch_dashboard" "lambda_dashboard" {
  dashboard_name = "${var.app_name}-lambda-metrics"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", module.lambda.lambda_function_name],
            [".", "Errors", ".", "."],
            [".", "Invocations", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = data.aws_region.current.name
          title  = "Lambda Function Metrics"
        }
      }
    ]
  })
}
```

### SNS Topics for Alerts:

```hcl
resource "aws_sns_topic" "lambda_alerts" {
  name = "${var.app_name}-lambda-alerts"

  tags = var.tags
}

resource "aws_sns_topic_subscription" "lambda_alerts_email" {
  topic_arn = aws_sns_topic.lambda_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
```

## 🚀 Best Practices Summary

1. **Module Design**: Create reusable Lambda modules with proper variable validation
2. **Source Organization**: Structure source code logically with proper separation of concerns
3. **Dependency Management**: Pin dependency versions and use layers for shared code
4. **Security**: Apply least privilege IAM policies and use Parameter Store for secrets
5. **VPC Configuration**: Place Lambdas in private subnets when accessing internal resources
6. **Monitoring**: Set up CloudWatch alarms and dashboards for observability
7. **Error Handling**: Implement proper error handling and logging in function code
8. **Build Consistency**: Use Docker builds for Python to ensure consistent deployments
9. **Resource Limits**: Set appropriate timeout and memory limits based on workload
10. **Dead Letter Queues**: Configure DLQs for critical functions to handle failures

This comprehensive guide provides the foundation for building robust, secure, and maintainable Lambda functions using Terraform modules.
