# Japanese SKU Fuzzy Search System - Copilot Instructions

## Project Overview

This is a production-ready Japanese SKU fuzzy search system built with OpenSearch and AWS Lambda. The system handles complex Japanese text processing including katakana/hiragana normalization, romaji conversion, and multi-field fuzzy matching for e-commerce SKU search.

## Architecture

### Core Components

- **OpenSearch Domain**: Enterprise-grade search engine with Japanese text processing
- **AWS Lambda**: Search function with optimized Japanese text handling
- **API Gateway**: RESTful API with Cognito authentication
- **Cognito**: User authentication and authorization
- **Infrastructure**: Terraform modules for staging and production environments

### Japanese Text Processing Pipeline

1. **Character Normalization**: Zenkaku → Hankaku conversion (full-width to half-width)
2. **Script Conversion**: Complete katakana ↔ hiragana mapping (108 characters)
3. **Multi-Analyzer Strategy**: 7 specialized analyzers for different search patterns
4. **Synonym Support**: Isolated synonym analyzer to prevent build conflicts
5. **Romaji Support**: Latin character search for Japanese text

## Key Files and Structure

```
fuzzy-sku/
├── fuzzy-sku-test/                    # Main development workspace
│   ├── sku_indexer.py                # Core indexer and search functionality
│   ├── TM_SYOHIN_202509302313.csv   # Sample SKU data
│   ├── Pipfile                       # Python dependencies
│   └── setup.sh                      # Environment setup script
└── infrastructure/                    # Production infrastructure
    ├── modules/                       # Terraform modules
    │   ├── api_gateway/              # API Gateway with Cognito auth
    │   ├── lambda_search/            # Lambda search function
    │   └── cognito_auth/             # Authentication module
    ├── environments/                  # Environment configurations
    │   ├── staging/                  # Staging environment
    │   └── production/               # Production environment
    ├── deploy.sh                     # Deployment automation
    └── README.md                     # Infrastructure documentation
```

## Development Patterns

### Japanese Text Handling

- **Always** use the complete katakana-hiragana character mapping (108 characters)
- **Normalize** zenkaku characters to hankaku before processing
- **Isolate** synonyms in dedicated analyzer to prevent OpenSearch build failures
- **Test** with real Japanese product names and medical terms
- **Validate** character filters work correctly with edge cases

### OpenSearch Configuration

- **Multi-field Strategy**: Use exact → japanese → ngram → fuzzy → partial → reading → synonym → romaji priority
- **Boost Values**: Exact matches get highest boost (100), decreasing by search type
- **Error Prevention**: Never include synonyms in main analyzers, use dedicated .synonym field
- **Filter Order**: Normalize chars first, then katakana_hiragana conversion
- **Index Mapping**: Always test mapping creation before data ingestion

### Code Organization

- **Single File Architecture**: Keep all functionality in `sku_indexer.py` for simplicity
- **Class-Based Design**: Use `JapaneseSKUIndexer` class with clear method separation
- **Error Handling**: Comprehensive error handling with detailed logging
- **Interactive Mode**: Include interactive search for testing and demonstration
- **Test Coverage**: Maintain 40+ test cases covering all Japanese text variations

## AWS Infrastructure Guidelines

### Terraform Best Practices

- **Module Structure**: Separate modules for api_gateway, lambda_search, cognito_auth
- **Environment Separation**: Distinct staging and production configurations
- **Resource Naming**: Use consistent naming pattern: `{app_name}-{environment}-{resource}`
- **Tagging Strategy**: Include Environment, Project, ManagedBy, Region tags
- **State Management**: Use S3 backend with DynamoDB locking

### Security Configuration

- **Cognito**: MFA optional for staging, enforced for production
- **API Gateway**: Restrict CORS origins in production
- **Lambda**: VPC configuration recommended for production
- **IAM**: Least privilege principle with specific resource ARNs
- **Encryption**: Enable at rest and in transit

### Performance Optimization

- **Lambda Memory**: 512MB staging, 1024MB production
- **Concurrency**: Reserved concurrency 5 staging, 20 production
- **API Throttling**: Lower limits for staging, higher for production
- **Caching**: Implement appropriate cache TTL values
- **Monitoring**: CloudWatch dashboards and alarms for production

## Code Style and Conventions

### Python Code

- **Type Hints**: Use comprehensive type annotations
- **Error Handling**: Wrap OpenSearch operations in try-catch blocks
- **Logging**: Use structured logging with appropriate levels
- **Documentation**: Docstrings for all classes and methods
- **Constants**: Define analyzer names and boost values as constants

### Terraform Code

- **Variable Validation**: Add validation rules for critical variables
- **Output Values**: Export all necessary information for integration
- **Documentation**: Comment complex resource configurations
- **Conditional Resources**: Use dynamic blocks and count for optional features

## Testing and Validation

### Search Testing

- **Japanese Variations**: Test hiragana, katakana, kanji, and mixed scripts
- **Medical Terms**: Include medical device and pharmaceutical terms
- **SKU Codes**: Test alphanumeric and mixed character SKU patterns
- **Edge Cases**: Empty queries, special characters, very long strings
- **Performance**: Validate response times under load

### Infrastructure Testing

- **Plan Validation**: Always run `terraform plan` before apply
- **Environment Isolation**: Test in staging before production deployment
- **Resource Verification**: Confirm all resources created successfully
- **Integration Testing**: Test full API flow with authentication
- **Monitoring**: Verify logging and metrics collection

## Common Issues and Solutions

### OpenSearch Mapping Errors

- **Synonym Conflicts**: Isolate synonyms in dedicated analyzer only
- **Filter Order**: Ensure normalize_chars comes before katakana_hiragana
- **Missing Filters**: Always define asciifolding filter explicitly
- **Build Failures**: Remove unused filters like katakana_stemmer

### Infrastructure Deployment

- **Backend Configuration**: Update S3 bucket and DynamoDB table names
- **Endpoint URLs**: Update OpenSearch endpoints for each environment
- **Callback URLs**: Configure correct domain names for Cognito
- **VPC Configuration**: Set up security groups and subnets for Lambda

### Performance Issues

- **Memory Allocation**: Increase Lambda memory for better performance
- **Timeout Settings**: Adjust based on search complexity and data size
- **Concurrency Limits**: Set appropriate reserved concurrency values
- **API Throttling**: Configure burst and rate limits based on expected load

## Deployment Workflow

### Development Process

1. **Local Testing**: Use interactive search mode in `sku_indexer.py`
2. **Index Validation**: Confirm mapping creation and data ingestion
3. **Test Coverage**: Run comprehensive test cases
4. **Code Review**: Ensure code follows established patterns
5. **Documentation**: Update relevant documentation

### Infrastructure Deployment

1. **Environment Preparation**: Update variables and backend configuration
2. **Plan Review**: Run terraform plan and review changes
3. **Staging Deployment**: Deploy to staging environment first
4. **Integration Testing**: Test full API flow with authentication
5. **Production Deployment**: Deploy to production with approval process

## Integration Points

### Frontend Integration

- **Authentication**: Use Cognito Hosted UI or custom integration
- **API Calls**: Include Bearer token in Authorization header
- **Error Handling**: Handle authentication and search errors gracefully
- **Loading States**: Implement appropriate loading indicators
- **Caching**: Client-side caching for better user experience

### Monitoring Integration

- **CloudWatch Logs**: Monitor API Gateway and Lambda logs
- **Metrics**: Track search performance and error rates
- **Alarms**: Set up alerts for error thresholds and performance degradation
- **Dashboards**: Use CloudWatch dashboards for operational visibility
- **X-Ray Tracing**: Analyze request performance and bottlenecks

## Future Enhancements

### Search Improvements

- **Machine Learning**: Implement personalized search ranking
- **Analytics**: Add search analytics and user behavior tracking
- **Autocomplete**: Real-time search suggestions
- **Faceted Search**: Category and attribute filtering
- **Spell Correction**: Japanese text spell correction

### Infrastructure Enhancements

- **Multi-Region**: Deploy across multiple AWS regions
- **Auto-Scaling**: Implement dynamic scaling based on load
- **Blue-Green Deployment**: Zero-downtime deployment strategy
- **Disaster Recovery**: Backup and restore procedures
- **Cost Optimization**: Reserved instances and spot pricing

## Key Considerations

### Japanese Text Processing

- Character encoding consistency (UTF-8)
- Proper handling of mixed script text
- Regional variations in Japanese language
- Context-aware search relevance
- Cultural considerations in search behavior

### Enterprise Requirements

- High availability and disaster recovery
- Security compliance and data protection
- Performance SLAs and monitoring
- Scalability for growth
- Cost optimization and budgeting

### Operational Excellence

- Automated deployment pipelines
- Comprehensive monitoring and alerting
- Documentation and knowledge management
- Incident response procedures
- Regular security audits and updates

## Contact and Support

For technical issues or questions:

- Review CloudWatch logs for detailed error information
- Check OpenSearch cluster health and performance metrics
- Validate IAM permissions and resource configurations
- Test with known working examples from test cases
- Follow troubleshooting guides in infrastructure README
