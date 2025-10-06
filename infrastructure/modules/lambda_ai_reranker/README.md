# Lambda AI Reranker Module

AWS Lambda function module that uses Bedrock Claude Sonnet 4.5 to re-rank OpenSearch results for Japanese SKU search.

Built using `terraform-aws-modules/lambda/aws` for automatic packaging, deployment, and management.

## Overview

This Lambda function implements intelligent AI-powered re-ranking of search results:

1. **Confidence Check**: Evaluates OpenSearch result quality using dual thresholds
2. **Conditional AI**: Only calls Bedrock when confidence is low
3. **Semantic Re-ranking**: Uses Claude to understand Japanese context, brand names, and user intent
4. **Cost Optimization**: Avoids unnecessary AI calls for high-confidence results

## Confidence Logic

```python
High Confidence = (topScore > 25.0) AND (ratio > 2.0)
```

- **topScore > 25**: Top result has strong OpenSearch match
- **ratio > 2.0**: Clear winner (2x better than second place)
- **Low confidence triggers AI**: Ambiguous or low-quality results need semantic understanding

## Module Usage

```hcl
module "lambda_ai_reranker" {
  source = "../../modules/lambda_ai_reranker"

  app_name      = "fuzzy-sku-production"
  function_name = "ai-reranker"
  description   = "AI reranker for Japanese SKU search using Bedrock Claude"
  tags          = local.common_tags

  # Lambda configuration
  runtime     = "python3.12"
  handler     = "lambda_function.lambda_handler"
  timeout     = 30
  memory_size = 512

  # Bedrock configuration
  bedrock_region   = "ap-northeast-3"
  bedrock_model_id = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"  # Global inference profile

  # Confidence thresholds
  confidence_threshold = 25.0
  score_gap_ratio      = 2.0

  # Monitoring and logging
  log_level           = "INFO"
  log_retention_days  = 14
  enable_xray_tracing = true
  enable_monitoring   = true

  # Build configuration
  build_in_docker = true
}
```

## Environment Variables

| Variable               | Default                            | Description                                 |
| ---------------------- | ---------------------------------- | ------------------------------------------- |
| `BEDROCK_REGION`       | `ap-northeast-3`                   | AWS region for Bedrock client (custom var)  |
| `BEDROCK_MODEL_ID`     | `anthropic.claude-sonnet-4-5-v1:0` | Claude model identifier                     |
| `CONFIDENCE_THRESHOLD` | `25.0`                             | Minimum top score for high confidence       |
| `SCORE_GAP_RATIO`      | `2.0`                              | Minimum ratio between 1st and 2nd scores    |
| `LOG_LEVEL`            | `INFO`                             | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENVIRONMENT`          | `staging`                          | Environment name                            |

⚠️ **Note**: `AWS_REGION` is reserved by Lambda. Use `BEDROCK_REGION` instead.

## Input Format

### Direct Invocation

```json
{
  "query": "メイジ",
  "results": [
    {
      "id": "123",
      "sku_name": "明治 スーパーカップ",
      "score": 15.5
    },
    {
      "id": "456",
      "sku_name": "ゆうめいと",
      "score": 14.8
    }
  ]
}
```

### API Gateway

```json
{
  "body": "{\"query\":\"メイジ\",\"results\":[...]}"
}
```

## Output Format

```json
{
  "statusCode": 200,
  "body": {
    "reranked_results": [
      {
        "id": "123",
        "sku_name": "明治 スーパーカップ",
        "score": 72.5,
        "original_score": 15.5,
        "ai_relevance_score": 95,
        "ai_reason": "明治ブランドと完全一致、高い関連性"
      }
    ],
    "used_ai": true,
    "confidence_info": {
      "needs_ai_reranking": true,
      "top_score": 15.5,
      "second_score": 14.8,
      "score_gap_ratio": 1.05,
      "reason": "Low confidence - needs AI reranking"
    }
  }
}
```

## AI Re-ranking Process

When confidence is low, Claude evaluates results based on:

1. **意味的関連性 (Semantic Relevance)**: Does the SKU name match query intent?
2. **ブランド認識 (Brand Recognition)**: Famous brands or accurate product names?
3. **製品文脈 (Product Context)**: Category, usage, features match intent?
4. **日本語の自然さ (Japanese Naturalness)**: Correct notation and natural language?

### Score Blending

Final score = (AI score × 0.7) + (OpenSearch score × 0.3)

- **70% AI weight**: Semantic understanding is primary
- **30% OpenSearch weight**: Preserve string matching signals

## Cost Optimization

### Example: 1,000 searches/day

- High confidence (75%): 750 searches × $0 = $0
- Low confidence (25%): 250 searches × ~$0.005 = $1.25/day
- **Monthly cost**: ~$37.50

### Comparison: AI for all searches

- 1,000 searches × $0.005 = $5/day
- **Monthly cost**: ~$150

**Savings: 75% cost reduction** while maintaining quality for ambiguous queries.

## Error Handling

The function implements graceful fallback:

- **Bedrock API errors**: Returns original OpenSearch results
- **JSON parsing errors**: Returns original results with error log
- **Missing fields**: Returns 400 Bad Request
- **Claude timeout**: Returns original results (no AI)

All errors are logged to CloudWatch for monitoring.

## Dependencies

```
boto3>=1.34.0
botocore>=1.34.0
```

Provided by AWS Lambda runtime (Python 3.12) or Lambda layer.

## Testing

### Local Testing (requires AWS credentials)

```python
import json
from lambda_function import lambda_handler

event = {
    "query": "メイジ",
    "results": [
        {"id": "1", "sku_name": "明治 ヨーグルト", "score": 15.5},
        {"id": "2", "sku_name": "ゆうめいと", "score": 14.8}
    ]
}

response = lambda_handler(event, None)
print(json.dumps(json.loads(response['body']), indent=2, ensure_ascii=False))
```

### Example Scenarios

#### Scenario 1: High Confidence (No AI)

```python
# Input: "コカコーラ"
# Top score: 45.2, Ratio: 3.5
# Result: Skip AI, return original order
```

#### Scenario 2: Low Confidence (Use AI)

```python
# Input: "メイジ"
# Top score: 15.5, Ratio: 1.05
# Result: Claude re-ranks based on semantic understanding
```

## Integration with Search Lambda

The search Lambda should call this reranker after OpenSearch query:

```python
# In search Lambda
opensearch_results = query_opensearch(query)

# Call AI reranker
reranker_response = lambda_client.invoke(
    FunctionName='fuzzy-sku-ai-reranker',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'query': query,
        'results': opensearch_results
    })
)

reranked_data = json.loads(reranker_response['Payload'].read())
final_results = json.loads(reranked_data['body'])['reranked_results']
```

## Monitoring

Key CloudWatch metrics to monitor:

- **Invocations**: Total Lambda calls
- **AI Usage Rate**: Percentage of requests using Bedrock
- **Duration**: Average execution time
- **Errors**: Failed invocations
- **Bedrock Throttling**: Rate limit hits

### Custom Metrics

Log structured data for analysis:

```json
{
  "query": "メイジ",
  "confidence_check": {
    "top_score": 15.5,
    "ratio": 1.05,
    "used_ai": true
  },
  "duration_ms": 850,
  "bedrock_latency_ms": 720
}
```

## Cross-Region Inference

When using Claude Sonnet 4.5 in `ap-northeast-3`:

- **Inference Region**: `us-east-1` (automatic)
- **Latency**: ~200-300ms additional
- **Cost**: Same as native region
- **Reliability**: AWS handles routing

No configuration needed - Bedrock handles cross-region inference transparently.

## Future Enhancements

1. **Caching**: Cache AI results for common queries (DynamoDB)
2. **Batch Processing**: Process multiple queries in single Bedrock call
3. **A/B Testing**: Compare AI vs non-AI results
4. **Fine-tuning**: Collect feedback to improve prompts
5. **Multi-model**: Test different Claude versions

## License

Internal use only - Lion Garden Welfan
