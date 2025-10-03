# Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│                    (React/TypeScript Frontend)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS POST /search
                             │ { query: "メイジ", size: 20 }
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (REST)                         │
│                     Authorization: Cognito                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Lambda Invoke
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Lambda: Search Function                      │
│                      (Python 3.12)                              │
│                                                                 │
│  1. Parse request                                               │
│  2. Query OpenSearch (fuzzy, ngram, synonym)                    │
│  3. Get results with highlights                                 │
│     ↓                                                           │
│  4. Call AI Reranker Lambda ─────────────────────────┐          │
│     ↓                                                │          │
│  5. Return final results                             │          │
└──────────────────────────────────────────────────────┼──────────┘
                                                       │
                                                       │ Lambda Invoke
                                                       │ {query, results}
                                                       ↓
┌─────────────────────────────────────────────────────────────────┐
│              Lambda: AI Reranker Function                       │
│                    (Python 3.12)                                │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐          │
│  │  1. Check Confidence                             │          │
│  │     • top_score > 25.0?                          │          │
│  │     • ratio > 2.0?                               │          │
│  └──────────────┬───────────────────────────────────┘          │
│                 │                                               │
│                 ├─ High Confidence ──→ Return original results  │
│                 │                                               │
│                 └─ Low Confidence ──→ Call Bedrock              │
│                                        ↓                        │
└────────────────────────────────────────┼────────────────────────┘
                                         │
                                         │ invoke_model()
                                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Bedrock Service                          │
│                   (ap-northeast-3)                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐          │
│  │  Cross-Region Inference                          │          │
│  │  ap-northeast-3 → us-east-1                      │          │
│  └──────────────┬───────────────────────────────────┘          │
│                 ↓                                               │
│  ┌──────────────────────────────────────────────────┐          │
│  │  Claude Sonnet 4.5                               │          │
│  │  • Semantic understanding                        │          │
│  │  • Japanese brand recognition                    │          │
│  │  • Context evaluation                            │          │
│  │  • Score + reasoning                             │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### High Confidence Path (75% of requests)

```
Search Lambda
     ↓
OpenSearch Query
     ↓
Results: [
  { sku: "コカ・コーラ", score: 45.2 },  ← Clear winner
  { sku: "ペプシ", score: 12.9 }        ← Far behind
]
     ↓
AI Reranker: check_confidence()
     ↓
topScore=45.2 > 25 ✓
ratio=3.5 > 2.0 ✓
     ↓
HIGH CONFIDENCE → Skip AI
     ↓
Return original results
     ↓
Frontend (Cost: $0)
```

### Low Confidence Path (25% of requests)

```
Search Lambda
     ↓
OpenSearch Query
     ↓
Results: [
  { sku: "ゆうめいと", score: 15.5 },    ← False positive
  { sku: "明治ヨーグルト", score: 14.8 }  ← Should be #1
]
     ↓
AI Reranker: check_confidence()
     ↓
topScore=15.5 < 25 ✗
ratio=1.05 < 2.0 ✗
     ↓
LOW CONFIDENCE → Use AI
     ↓
Bedrock Claude Sonnet 4.5
     ↓
Semantic Analysis:
  - "メイジ" = 明治 brand
  - "ゆうめいと" = false positive
     ↓
Reranked Results: [
  { sku: "明治ヨーグルト", score: 71.0, ai_score: 95 },  ← Promoted
  { sku: "ゆうめいと", score: 11.7, ai_score: 10 }     ← Demoted
]
     ↓
Frontend (Cost: $0.005)
```

## Component Interactions

```
┌─────────────────┐
│   OpenSearch    │
│                 │
│  • sku_name     │
│  • indexed_at   │
│                 │
│  Analyzers:     │
│  - exact        │
│  - ngram        │
│  - fuzzy        │
│  - partial      │
│  - synonym      │
│  - romaji       │
└────────┬────────┘
         │
         │ Query Results
         ↓
┌─────────────────┐         ┌─────────────────┐
│  Search Lambda  │────────→│  AI Reranker    │
│                 │  invoke │                 │
│ Environment:    │         │ Environment:    │
│ - OS_ENDPOINT   │         │ - AWS_REGION    │
│ - OS_INDEX      │         │ - BEDROCK_MODEL │
│ - AI_RERANKER   │         │ - THRESHOLD     │
└─────────────────┘         │ - GAP_RATIO     │
                            └────────┬────────┘
                                     │
                                     │ invoke_model
                                     ↓
                            ┌─────────────────┐
                            │  AWS Bedrock    │
                            │                 │
                            │ Model:          │
                            │  Claude Sonnet  │
                            │  4.5            │
                            │                 │
                            │ Cross-region:   │
                            │  ap-northeast-3 │
                            │  → us-east-1    │
                            └─────────────────┘
```

## Decision Tree

```
                        Search Request
                             │
                             ↓
                      OpenSearch Query
                             │
                             ↓
                ┌────────────────────────┐
                │  Check Confidence      │
                │                        │
                │  topScore > 25?        │
                │  ratio > 2.0?          │
                └────────┬───────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
        YES│                           │NO
           ↓                           ↓
    ┌─────────────┐            ┌──────────────┐
    │ High        │            │ Low          │
    │ Confidence  │            │ Confidence   │
    │             │            │              │
    │ Skip AI     │            │ Use AI       │
    └──────┬──────┘            └──────┬───────┘
           │                           │
           │                           ↓
           │                    ┌──────────────┐
           │                    │ Call Bedrock │
           │                    │ Claude API   │
           │                    └──────┬───────┘
           │                           │
           │                           ↓
           │                    ┌──────────────┐
           │                    │ Parse AI     │
           │                    │ Response     │
           │                    └──────┬───────┘
           │                           │
           │                           ↓
           │                    ┌──────────────┐
           │                    │ Blend Scores │
           │                    │ 70% AI       │
           │                    │ 30% OS       │
           │                    └──────┬───────┘
           │                           │
           └───────────┬───────────────┘
                       ↓
              ┌─────────────────┐
              │ Return Results  │
              │ + Metadata      │
              │   - used_ai     │
              │   - confidence  │
              └─────────────────┘
```

## Infrastructure Deployment

```
GitHub Repo
     ↓
Terraform Code
     │
     ├─ modules/lambda_ai_reranker/
     │     ├─ main.tf          (Lambda function)
     │     ├─ data.tf          (IAM policies)
     │     ├─ variables.tf     (Configuration)
     │     ├─ outputs.tf       (ARNs, names)
     │     └─ src/python/      (Code)
     │
     └─ environments/osaka-prod/
           ├─ main.tf          (Module call)
           └─ locals.tf        (Region, tags)

     ↓ terraform apply

AWS Resources Created:
     │
     ├─ Lambda Function (fuzzy-sku-ai-reranker)
     ├─ IAM Role (execution role)
     ├─ IAM Policy (Bedrock access)
     ├─ CloudWatch Log Group (/aws/lambda/...)
     └─ Lambda Permissions (invoke from search Lambda)
```

## Cost Flow

```
                    1000 Searches/Day
                           │
                           ↓
              ┌────────────────────────┐
              │  Confidence Routing    │
              └────────┬───────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
    750 (75%)                 250 (25%)
    High Confidence           Low Confidence
           │                       │
           ↓                       ↓
    ┌──────────────┐        ┌──────────────┐
    │ Skip AI      │        │ Call Bedrock │
    │              │        │              │
    │ Cost: $0     │        │ Cost: $0.005 │
    └──────────────┘        └──────┬───────┘
           │                       │
           │                       ↓
           │                  250 × $0.005
           │                    = $1.25/day
           │                       │
           └───────────┬───────────┘
                       ↓
              Total: $1.25/day
              Monthly: ~$37.50

              vs. All AI: $150/month
              Savings: 75% 🎉
```

## Monitoring Dashboard

```
CloudWatch Metrics
     │
     ├─ Lambda Invocations
     │     ├─ Total: 1000/day
     │     ├─ Success: 995
     │     └─ Errors: 5
     │
     ├─ AI Usage
     │     ├─ Used AI: 250 (25%)
     │     └─ Skipped AI: 750 (75%)
     │
     ├─ Latency
     │     ├─ P50: 600ms
     │     ├─ P95: 850ms
     │     └─ P99: 1200ms
     │
     └─ Cost
           ├─ Daily: $1.25
           ├─ Monthly: $37.50
           └─ vs Budget: 75% under
```

---

**Legend:**

- `→` : Synchronous call
- `↓` : Flow direction
- `✓` : Condition met
- `✗` : Condition failed
- `┌─┐` : Component boundary
