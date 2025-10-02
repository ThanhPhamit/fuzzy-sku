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
        self.index_name = os.environ.get("INDEX_NAME", "sku-master")
        self.region = os.environ.get("AWS_REGION", "ap-northeast-3")
        self.client = self._get_opensearch_client()

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

            # Process and return results
            return self._process_search_results(response, query)

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            raise

    def _build_search_query(self, query: str, size: int) -> Dict[str, Any]:
        """Build simple OpenSearch query for SKU name search only (like validate_index)"""

        # Simple search strategy similar to your indexer's validate_index method
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"sku_name": {"query": query, "boost": 3.0}}},
                        {"match": {"sku_name.exact": {"query": query, "boost": 2.0}}},
                        {"match": {"sku_name.ngram": {"query": query, "boost": 1.5}}},
                        {"match": {"sku_name.fuzzy": {"query": query, "boost": 1.0}}},
                        {"match": {"sku_name.partial": {"query": query, "boost": 1.2}}},
                        {"match": {"sku_name.synonym": {"query": query, "boost": 1.8}}},
                    ]
                }
            },
            "size": size,
            "sort": [{"_score": {"order": "desc"}}],
            "highlight": {
                "fields": {
                    "sku_name": {"pre_tags": ["<mark>"], "post_tags": ["</mark>"]},
                }
            },
        }

        logger.debug(f"Search query: {json.dumps(search_body, ensure_ascii=False)}")
        return search_body

    def _process_search_results(
        self, response: Dict, original_query: str
    ) -> Dict[str, Any]:
        """Process OpenSearch response and format results"""

        hits = response.get("hits", {})
        total_hits = hits.get("total", {}).get("value", 0)
        max_score = hits.get("max_score", 0)

        results = []
        for hit in hits.get("hits", []):
            source = hit.get("_source", {})
            score = hit.get("_score", 0)
            highlight = hit.get("highlight", {})

            # Build result item (simplified)
            result_item = {
                "id": source.get("id", ""),
                "sku_name": source.get("sku_name", ""),
                "score": score,
                "highlights": highlight,
            }

            results.append(result_item)

        # Build response
        processed_response = {
            "query": original_query,
            "total_hits": total_hits,
            "max_score": max_score,
            "results": results,
            "took": response.get("took", 0),
            "timed_out": response.get("timed_out", False),
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
    """Create standardized Lambda response"""

    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(body, ensure_ascii=False, separators=(",", ":")),
    }

    logger.debug(f"Lambda response: {response}")
    return response
