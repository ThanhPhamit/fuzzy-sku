# Lambda Search Function Module

This module creates a Japanese SKU fuzzy search Lambda function using the `terraform-aws-modules/lambda/aws` module for best practices and enterprise-grade functionality.

## Features

- **Enterprise Module**: Uses the official AWS Lambda Terraform module
- **Japanese Text Processing**: Integrated with OpenSearch for complex Japanese text search
- **Automatic Building**: Docker-based builds for consistent deployments
- **Monitoring**: CloudWatch alarms for errors and duration
- **Security**: VPC support, least privilege IAM, X-Ray tracing
- **Scalability**: Reserved concurrency and performance optimization

## Architecture

```
src/python/
├── lambda_function.py     # Main Lambda handler with Japanese search logic
└── requirements.txt       # Python dependencies
```

## Usage

```hcl
module "lambda_search" {
  source = "../../modules/lambda_search"

  app_name      = "my-app-staging"
  function_name = "search-function"
  description   = "Japanese SKU fuzzy search function"

  # OpenSearch configuration
  opensearch_endpoint   = "https://search-domain.region.es.amazonaws.com"
  opensearch_index_name = "japanese_sku_index"

  # Lambda configuration
  runtime     = "python3.11"
  timeout     = 30
  memory_size = 512

  # Environment variables
  environment_variables = {
    DEBUG_MODE = "false"
    CACHE_TTL  = "300"
  }

  # VPC configuration (optional)
  vpc_config = {
    subnet_ids         = ["subnet-12345", "subnet-67890"]
    security_group_ids = ["sg-abcdef"]
  }

  tags = {
    Environment = "staging"
    Project     = "fuzzy-sku"
  }
}
```

## Key Features

### Japanese Text Processing

- Multi-analyzer search strategy (exact, japanese, ngram, fuzzy, partial, reading, synonym, romaji)
- Katakana/Hiragana normalization
- Zenkaku to Hankaku character conversion
- Romaji search support

### Performance Optimization

- Docker builds for consistent Python environments
- Reserved concurrency for predictable performance
- CloudWatch monitoring with configurable alarms
- X-Ray tracing for performance analysis

### Security

- VPC support for private subnet deployment
- Least privilege IAM policies
- Environment variable encryption
- Secure OpenSearch integration

## Inputs

| Variable                | Type        | Default              | Description                          |
| ----------------------- | ----------- | -------------------- | ------------------------------------ |
| `app_name`              | string      | -                    | Application name for resource naming |
| `function_name`         | string      | "search-function"    | Lambda function name suffix          |
| `opensearch_endpoint`   | string      | -                    | OpenSearch domain endpoint           |
| `opensearch_index_name` | string      | "japanese_sku_index" | OpenSearch index name                |
| `runtime`               | string      | "python3.11"         | Lambda runtime version               |
| `timeout`               | number      | 30                   | Function timeout in seconds          |
| `memory_size`           | number      | 512                  | Memory allocation in MB              |
| `vpc_config`            | object      | null                 | VPC configuration for Lambda         |
| `environment_variables` | map(string) | {}                   | Additional environment variables     |
| `enable_monitoring`     | bool        | true                 | Enable CloudWatch alarms             |

## Outputs

| Output                             | Description                            |
| ---------------------------------- | -------------------------------------- |
| `lambda_function_arn`              | ARN of the Lambda function             |
| `lambda_function_name`             | Name of the Lambda function            |
| `lambda_function_invoke_arn`       | Invoke ARN for API Gateway integration |
| `lambda_role_arn`                  | ARN of the Lambda execution role       |
| `lambda_cloudwatch_log_group_name` | CloudWatch log group name              |

## Monitoring

The module creates CloudWatch alarms for:

- **Error Rate**: Triggers when error count exceeds threshold
- **Duration**: Alerts when execution time approaches timeout
- **Custom Metrics**: Extensible for additional monitoring

## Development Workflow

1. **Local Development**: Test with your existing `sku_indexer.py`
2. **Code Integration**: Copy search logic to `src/python/lambda_function.py`
3. **Build & Deploy**: Module handles Docker builds automatically
4. **Monitor**: Use CloudWatch dashboards and alarms

## Migration from Custom Resources

This module replaces the previous custom Lambda resources with:

- ✅ Official AWS Lambda Terraform module
- ✅ Standardized variable patterns
- ✅ Enhanced monitoring and alerting
- ✅ Improved security practices
- ✅ Better build consistency

## Dependencies

- `terraform-aws-modules/lambda/aws` ~> 6.0
- `hashicorp/aws` provider ~> 5.0
- `hashicorp/archive` provider ~> 2.0

## Best Practices

1. **Use Docker builds** for Python consistency
2. **Configure VPC** for production security
3. **Set appropriate memory** based on workload
4. **Enable monitoring** for operational visibility
5. **Use environment variables** for configuration
6. **Test thoroughly** before production deployment
