import json
import os
import logging
from typing import Dict, Any, List, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(getattr(logging, os.environ.get("LOG_LEVEL", "INFO")))


class JapaneseSKUSearcher:
    """Japanese SKU search functionality for Lambda"""

    def __init__(self):
        self.opensearch_endpoint = os.environ.get("OPENSEARCH_ENDPOINT")
        self.index_name = os.environ.get(
            "INDEX_NAME", "tm-juchum"
        )  # Changed to tm-juchum
        self.region = os.environ.get("AWS_REGION", "ap-northeast-3")
        self.confidence_threshold = float(
            os.environ.get("CONFIDENCE_THRESHOLD", "25.0")
        )
        self.score_gap_ratio = float(os.environ.get("SCORE_GAP_RATIO", "2.0"))
        self.ai_reranker_function = os.environ.get("AI_RERANKER_FUNCTION_NAME", "")
        self.client = self._get_opensearch_client()
        self.lambda_client = (
            boto3.client("lambda", region_name=self.region)
            if self.ai_reranker_function
            else None
        )

    def _get_opensearch_client(self) -> OpenSearch:
        """Initialize OpenSearch client with AWS authentication"""
        try:
            # Get AWS credentials
            session = boto3.Session()
            credentials = session.get_credentials()

            # Create AWS auth
            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                self.region,
                "es",
                session_token=credentials.token,
            )

            # Create OpenSearch client
            client = OpenSearch(
                hosts=[
                    {
                        "host": self.opensearch_endpoint.replace("https://", ""),
                        "port": 443,
                    }
                ],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=30,  # Fixed: use integer instead of string
                max_retries=3,
                retry_on_timeout=True,
            )

            # Test connection
            if not client.ping():
                raise Exception("Failed to connect to OpenSearch")

            logger.info(
                f"Successfully connected to OpenSearch: {self.opensearch_endpoint}"
            )
            return client

        except Exception as e:
            logger.error(f"Failed to initialize OpenSearch client: {str(e)}")
            raise

    def search_sku(self, query: str, size: int = 20) -> Dict[str, Any]:
        """
        Perform simple Japanese SKU search (no filters)

        Args:
            query: Search query (Japanese text, SKU codes, etc.)
            size: Number of results to return

        Returns:
            Search results with metadata
        """
        try:
            # Build simple search body
            search_body = self._build_search_query(query, size)

            # Execute search
            response = self.client.search(
                index=self.index_name, body=search_body, timeout=30
            )

            print("Search response:", json.dumps(response, ensure_ascii=False))

            # Process and return results
            return self._process_search_results(response, query)

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            raise

    def _build_search_query(self, query: str, size: int) -> Dict[str, Any]:
        """
        Build optimized OpenSearch query for Japanese SKU matching (tm-juchum index)
        Uses function_score with tiered boost strategy for better relevance
        Matches sku_indexer.py simple_search strategy
        """

        # 🎯 Optimized boost strategy - prioritize Japanese-only queries
        should_queries = [
            # Japanese-only queries (highest priority)
            {"match": {"search_text": {"query": query, "boost": 8.0}}},
            {"match": {"search_text.exact": {"query": query, "boost": 7.0}}},
            {"match": {"search_text.ngram": {"query": query, "boost": 5.0}}},
            {"match": {"search_text.partial": {"query": query, "boost": 4.0}}},
            # Cross-language matching (lower priority)
            {"match": {"search_text.latin_ngram": {"query": query, "boost": 3.0}}},
            {"match": {"search_text.romaji_ngram": {"query": query, "boost": 2.5}}},
            {"match": {"search_text.romaji": {"query": query, "boost": 2.5}}},
            {"match": {"search_text.latin": {"query": query, "boost": 2.5}}},
            # Fallback strategies (lowest priority)
            {"match": {"search_text.fuzzy": {"query": query, "boost": 2.0}}},
            {"match": {"search_text.synonym": {"query": query, "boost": 1.5}}},
        ]

        search_body = {
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "should": should_queries,
                            "minimum_should_match": "30%",
                        }
                    },
                    "functions": [
                        # Exact hinban match gets highest boost
                        {
                            "filter": {"term": {"hinban": query}},
                            "weight": 10.0,
                        },
                    ],
                    "score_mode": "sum",
                    "boost_mode": "multiply",
                }
            },
            "_source": [
                "hinban",
                "skname1",
                "colorcd",
                "colornm",
                "sizecd",
                "sizename",
            ],
            "size": size,
        }

        logger.debug(f"Search query: {json.dumps(search_body, ensure_ascii=False)}")
        return search_body

    def _check_confidence(self, results: List[Dict]) -> tuple:
        """
        Check if OpenSearch results have high confidence
        Returns: (is_confident, reason)
        """
        if not results or len(results) == 0:
            return False, "No results"

        top_score = results[0]["score"]

        # Check first condition: topScore > threshold
        if top_score <= self.confidence_threshold:
            return False, f"Low score: {top_score:.2f} <= {self.confidence_threshold}"

        # Check second condition: score gap ratio
        if len(results) >= 2:
            second_score = results[1]["score"]
            ratio = top_score / second_score if second_score > 0 else float("inf")

            if ratio <= self.score_gap_ratio:
                return (
                    False,
                    f"Small gap: ratio {ratio:.2f} <= {self.score_gap_ratio} (top={top_score:.2f}, second={second_score:.2f})",
                )

            return (
                True,
                f"High confidence: score {top_score:.2f} > {self.confidence_threshold} AND ratio {ratio:.2f} > {self.score_gap_ratio}",
            )

        # Only one result but high score
        return (
            True,
            f"Single high-score result: {top_score:.2f} > {self.confidence_threshold}",
        )

    def _invoke_ai_reranker(self, query: str, results: List[Dict]) -> List[Dict]:
        """Invoke AI reranker Lambda function"""
        try:
            if not self.lambda_client or not self.ai_reranker_function:
                logger.warning("AI reranker not configured, returning original results")
                return results

            payload = {"query": query, "results": results}

            logger.info(f"Invoking AI reranker for query: '{query}'")

            response = self.lambda_client.invoke(
                FunctionName=self.ai_reranker_function,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload, ensure_ascii=False),
            )

            response_payload = json.loads(response["Payload"].read())

            if response["StatusCode"] == 200:
                body = json.loads(response_payload.get("body", "{}"))
                reranked_results = body.get("results", results)
                logger.info(f"AI reranking completed: {len(reranked_results)} results")
                return reranked_results
            else:
                logger.error(f"AI reranker failed with status {response['StatusCode']}")
                return results

        except Exception as e:
            logger.error(f"AI reranker invocation failed: {str(e)}")
            # Fallback to original results
            return results

    def _process_search_results(
        self, response: Dict, original_query: str
    ) -> Dict[str, Any]:
        """Process OpenSearch response and format results for tm-juchum index"""

        hits = response.get("hits", {})
        total_hits = hits.get("total", {}).get("value", 0)
        max_score = hits.get("max_score", 0)

        results = []
        for hit in hits.get("hits", []):
            source = hit.get("_source", {})
            score = hit.get("_score", 0)
            highlight = hit.get("highlight", {})

            # Build result item with tm-juchum fields
            result_item = {
                "id": source.get("hinban", ""),  # Use hinban as ID
                "sku_name": source.get("skname1", ""),  # Main SKU name
                "hinban": source.get("hinban", ""),
                "colorcd": source.get("colorcd", ""),
                "colornm": source.get("colornm", ""),
                "sizecd": source.get("sizecd", ""),
                "sizename": source.get("sizename", ""),
                "score": score,
                "highlights": highlight,
            }

            results.append(result_item)

        # # Check confidence
        # is_confident, confidence_reason = self._check_confidence(results)

        # # If not confident, invoke AI reranker
        # if not is_confident and self.ai_reranker_function:
        #     logger.info(f"Low confidence: {confidence_reason} - invoking AI reranker")
        #     results = self._invoke_ai_reranker(original_query, results)
        #     reranked = True
        # else:
        #     logger.info(
        #         f"High confidence: {confidence_reason} - returning OpenSearch results"
        #     )
        #     reranked = False

        # Build response
        processed_response = {
            "query": original_query,
            "total_hits": total_hits,
            "max_score": max_score,
            "results": results,
            "took": response.get("took", 0),
            "timed_out": response.get("timed_out", False),
            # "confidence": {
            #     "is_high": is_confident,
            #     "threshold": self.confidence_threshold,
            #     "score_gap_ratio": self.score_gap_ratio,
            #     "reason": confidence_reason,
            #     "reranked": reranked,
            # },
        }

        logger.info(f"Search completed: {total_hits} hits for query '{original_query}'")
        return processed_response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for simple Japanese SKU search (GET only)

    Expected event format:

    GET request query parameters:
    ?q=search_term&size=20
    """

    logger.info(f"Lambda invoked with event: {json.dumps(event, ensure_ascii=False)}")

    try:
        # Initialize searcher
        searcher = JapaneseSKUSearcher()

        # Parse request parameters (simplified)
        query, size = _parse_request(event)

        if not query:
            return _create_response(400, {"error": "Missing required parameter: query"})

        # Perform simple search
        results = searcher.search_sku(query, size)

        # Return successful response
        return _create_response(200, results)

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        return _create_response(
            500, {"error": "Internal server error", "message": str(e)}
        )


def _parse_request(event: Dict[str, Any]) -> tuple:
    """Parse Lambda event to extract search parameters (GET only)"""

    # Default values
    query = None
    size = 20

    # Handle API Gateway event (GET only)
    if "httpMethod" in event:
        # Parse query parameters
        query_params = event.get("queryStringParameters") or {}
        query = query_params.get("q") or query_params.get("query")
        size = int(query_params.get("size", 20))

    # Handle direct invocation
    else:
        query = event.get("query")
        size = event.get("size", 20)

    # Validate and constrain size
    size = max(1, min(size, 100))  # Between 1 and 100

    logger.info(f"Parsed request - query: '{query}', size: {size}")

    return query, size


def _create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized Lambda response with CORS headers"""

    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # Allow all origins - API Gateway will enforce the actual origin
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Credentials": "false",
        },
        "body": json.dumps(body, ensure_ascii=False, separators=(",", ":")),
    }

    logger.debug(f"Lambda response: {response}")
    return response
