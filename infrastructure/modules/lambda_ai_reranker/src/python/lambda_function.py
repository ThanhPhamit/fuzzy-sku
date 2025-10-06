"""
AI Re-ranker Lambda Function for Japanese SKU Search
Uses AWS Bedrock Claude Sonnet 4.5 for semantic re-ranking
"""

import json
import os
import logging
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(getattr(logging, os.environ.get("LOG_LEVEL", "INFO")))

# Load environment variables
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "ap-northeast-3")
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-5-v1:0"
)
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "25.0"))
SCORE_GAP_RATIO = float(os.environ.get("SCORE_GAP_RATIO", "2.0"))

# Initialize Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

logger.info(
    f"AI Reranker initialized: Region={BEDROCK_REGION}, Model={BEDROCK_MODEL_ID}, "
    f"ConfidenceThreshold={CONFIDENCE_THRESHOLD}, ScoreGapRatio={SCORE_GAP_RATIO}"
)


def check_confidence(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check if OpenSearch results have high confidence.

    Logic:
    - High confidence if top_score > threshold AND score_gap_ratio > ratio
    - Low confidence triggers AI re-ranking

    Args:
        results: List of search results with scores

    Returns:
        Dict with confidence metrics and needs_ai_reranking flag
    """
    if not results or len(results) == 0:
        return {
            "needs_ai_reranking": False,
            "top_score": 0,
            "second_score": 0,
            "score_gap_ratio": 0,
            "reason": "No results",
        }

    # Sort by score descending
    sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)

    top_score = sorted_results[0].get("score", 0)
    second_score = sorted_results[1].get("score", 0) if len(sorted_results) > 1 else 0

    # Calculate ratio (avoid division by zero)
    ratio = top_score / second_score if second_score > 0 else float("inf")

    # High confidence: top_score > threshold AND ratio > gap_ratio
    high_confidence = top_score > CONFIDENCE_THRESHOLD and ratio > SCORE_GAP_RATIO

    confidence_info = {
        "needs_ai_reranking": not high_confidence,
        "top_score": top_score,
        "second_score": second_score,
        "score_gap_ratio": ratio,
        "reason": (
            "High confidence"
            if high_confidence
            else "Low confidence - needs AI reranking"
        ),
    }

    logger.info(f"Confidence check: {confidence_info}")
    return confidence_info


def rerank_with_claude(
    query: str, results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Use Claude to re-rank OpenSearch results based on semantic relevance.

    Args:
        query: User's search query
        results: List of OpenSearch results with id, sku_name, score

    Returns:
        Re-ranked list of results with updated scores
    """
    try:
        # Prepare SKU list for Claude evaluation
        sku_list = [
            {
                "index": i,
                "sku_name": result["sku_name"],
                "original_score": result["score"],
            }
            for i, result in enumerate(results)
        ]

        # Create prompt for Claude in Japanese
        prompt = f"""あなたは日本の製品検索の専門家です。ユーザーの検索クエリと商品名（SKU）のリストを与えられます。

検索クエリ: "{query}"

商品リスト:
{json.dumps(sku_list, ensure_ascii=False, indent=2)}

以下の基準で商品の関連性を評価し、最も関連性の高い順に並べ替えてください：

1. **意味的関連性**: 商品名が検索クエリの意図と一致しているか
2. **ブランド認識**: 有名ブランドや正確な製品名か
3. **製品文脈**: カテゴリー、用途、特徴が検索意図と合っているか
4. **日本語の自然さ**: 表記が正しく、自然な日本語か

必ず以下のJSON形式で応答してください：

{{
  "reranked_results": [
    {{
      "index": 元のインデックス番号,
      "relevance_score": 0-100の関連性スコア,
      "reason": "ランキング理由（日本語、50文字以内）"
    }}
  ]
}}

注意: 必ずJSONのみを返し、他の説明文は含めないでください。"""

        # Prepare request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.3,  # Low temperature for consistent ranking
            "messages": [{"role": "user", "content": prompt}],
        }

        logger.info(f"Calling Bedrock with model: {BEDROCK_MODEL_ID}")

        # Call Bedrock API
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID, body=json.dumps(request_body)
        )

        # Parse response
        response_body = json.loads(response["body"].read())
        logger.info(
            f"Bedrock response: {json.dumps(response_body, ensure_ascii=False)}"
        )

        # Extract Claude's text response
        claude_text = response_body.get("content", [{}])[0].get("text", "")

        if not claude_text:
            logger.error("Empty response from Claude")
            return results  # Return original results

        # Parse Claude's JSON response
        # Handle potential markdown code blocks
        claude_text = claude_text.strip()
        if claude_text.startswith("```json"):
            claude_text = claude_text[7:]
        if claude_text.startswith("```"):
            claude_text = claude_text[3:]
        if claude_text.endswith("```"):
            claude_text = claude_text[:-3]
        claude_text = claude_text.strip()

        claude_result = json.loads(claude_text)
        reranked = claude_result.get("reranked_results", [])

        if not reranked:
            logger.error("No reranked_results in Claude response")
            return results

        # Apply Claude's ranking to original results
        reranked_results = []
        for item in reranked:
            idx = item.get("index")
            if idx is not None and 0 <= idx < len(results):
                result = results[idx].copy()
                result["ai_relevance_score"] = item.get("relevance_score", 50)
                result["ai_reason"] = item.get("reason", "")
                result["original_score"] = result["score"]
                # Blend AI score with OpenSearch score (70% AI, 30% OpenSearch)
                result["score"] = (item.get("relevance_score", 50) * 0.7) + (
                    result["score"] * 0.3
                )
                reranked_results.append(result)

        logger.info(f"Successfully reranked {len(reranked_results)} results")
        return reranked_results

    except json.JSONDecodeError as e:
        logger.error(
            f"JSON parsing error: {e}, Claude response: {claude_text if 'claude_text' in locals() else 'N/A'}"
        )
        return results
    except Exception as e:
        logger.error(f"Error in rerank_with_claude: {e}", exc_info=True)
        return results  # Return original results on error


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for AI reranking service.

    Expected event format:
    {
        "query": "search query",
        "results": [{"id": "...", "sku_name": "...", "score": 10.5}, ...]
    }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "reranked_results": [...],
            "used_ai": true/false,
            "confidence_info": {...}
        }
    }
    """
    try:
        # Parse input
        if "body" in event:
            # API Gateway format
            body = (
                json.loads(event["body"])
                if isinstance(event["body"], str)
                else event["body"]
            )
        else:
            # Direct invocation format
            body = event

        query = body.get("query", "")
        results = body.get("results", [])

        if not query or not results:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Missing required fields: query and results"}
                ),
            }

        logger.info(f"Processing query: '{query}' with {len(results)} results")

        # Check confidence level
        confidence_info = check_confidence(results)

        if confidence_info["needs_ai_reranking"]:
            logger.info(
                f"Low confidence detected, using AI reranking. Top score: {confidence_info['top_score']:.2f}, Gap ratio: {confidence_info['score_gap_ratio']:.2f}"
            )
            reranked_results = rerank_with_claude(query, results)
            used_ai = True
        else:
            logger.info(
                f"High confidence, skipping AI reranking. Top score: {confidence_info['top_score']:.2f}, Gap ratio: {confidence_info['score_gap_ratio']:.2f}"
            )
            reranked_results = results
            used_ai = False

        response_body = {
            "reranked_results": reranked_results,
            "used_ai": used_ai,
            "confidence_info": confidence_info,
        }

        return {
            "statusCode": 200,
            "body": json.dumps(response_body, ensure_ascii=False),
        }

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
        }
