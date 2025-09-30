import json
import os
import logging
from typing import Dict, Any, List, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(getattr(logging, os.environ.get("LOG_LEVEL", "INFO")))


class JapaneseSKUSearcher:
    """Japanese SKU search functionality for Lambda"""

    def __init__(self):
        self.opensearch_endpoint = os.environ.get("OPENSEARCH_ENDPOINT")
        self.index_name = os.environ.get("INDEX_NAME", "japanese_sku_index")
        self.region = os.environ.get("AWS_REGION", "ap-northeast-3")
        self.client = self._get_opensearch_client()

    def _get_opensearch_client(self) -> OpenSearch:
        """Initialize OpenSearch client with AWS authentication"""
        try:
            # Get AWS credentials
            session = boto3.Session()
            credentials = session.get_credentials()

            # Create AWS auth
            awsauth = AWSRequestsAuth(
                aws_access_key=credentials.access_key,
                aws_secret_access_key=credentials.secret_key,
                aws_token=credentials.token,
                aws_host=self.opensearch_endpoint.replace("https://", ""),
                aws_region=self.region,
                aws_service="es",
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
                timeout=30,
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

    def search_sku(
        self, query: str, size: int = 20, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Perform Japanese SKU fuzzy search

        Args:
            query: Search query (Japanese text, SKU codes, etc.)
            size: Number of results to return
            filters: Additional filters to apply

        Returns:
            Search results with metadata
        """
        try:
            # Build search body with multi-field strategy
            search_body = self._build_search_query(query, size, filters)

            # Execute search
            response = self.client.search(
                index=self.index_name, body=search_body, timeout="30s"
            )

            # Process and return results
            return self._process_search_results(response, query)

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            raise

    def _build_search_query(
        self, query: str, size: int, filters: Optional[Dict]
    ) -> Dict[str, Any]:
        """Build OpenSearch query with Japanese text optimization"""

        # Multi-field search strategy matching your original implementation
        multi_match_queries = [
            # Exact match (highest priority)
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "sku_code.exact^10",
                        "name.exact^8",
                        "description.exact^6",
                    ],
                    "type": "phrase",
                    "boost": 100,
                }
            },
            # Standard Japanese analysis
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "sku_code.japanese^8",
                        "name.japanese^6",
                        "description.japanese^4",
                    ],
                    "type": "best_fields",
                    "boost": 50,
                }
            },
            # N-gram for partial matches
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "sku_code.ngram^6",
                        "name.ngram^4",
                        "description.ngram^3",
                    ],
                    "type": "best_fields",
                    "boost": 30,
                }
            },
            # Fuzzy matching
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "sku_code.fuzzy^4",
                        "name.fuzzy^3",
                        "description.fuzzy^2",
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "boost": 20,
                }
            },
            # Partial matching
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "sku_code.partial^3",
                        "name.partial^2",
                        "description.partial^1",
                    ],
                    "type": "phrase_prefix",
                    "boost": 15,
                }
            },
            # Reading-based search (hiragana/katakana)
            {
                "multi_match": {
                    "query": query,
                    "fields": ["name.reading^5", "description.reading^3"],
                    "type": "best_fields",
                    "boost": 25,
                }
            },
            # Synonym search
            {
                "multi_match": {
                    "query": query,
                    "fields": ["name.synonym^4", "description.synonym^2"],
                    "type": "best_fields",
                    "boost": 20,
                }
            },
            # Romaji search
            {
                "multi_match": {
                    "query": query,
                    "fields": ["name.romaji^3", "description.romaji^2"],
                    "type": "best_fields",
                    "boost": 15,
                }
            },
        ]

        # Combine queries with should (OR logic)
        bool_query = {"should": multi_match_queries, "minimum_should_match": 1}

        # Add filters if provided
        if filters:
            bool_query["filter"] = []
            for field, value in filters.items():
                if isinstance(value, list):
                    bool_query["filter"].append({"terms": {field: value}})
                else:
                    bool_query["filter"].append({"term": {field: value}})

        # Build complete search body
        search_body = {
            "query": {"bool": bool_query},
            "size": size,
            "sort": [
                {"_score": {"order": "desc"}},
                {"sku_code.keyword": {"order": "asc"}},
            ],
            "highlight": {
                "fields": {
                    "name": {"pre_tags": ["<mark>"], "post_tags": ["</mark>"]},
                    "description": {"pre_tags": ["<mark>"], "post_tags": ["</mark>"]},
                    "sku_code": {"pre_tags": ["<mark>"], "post_tags": ["</mark>"]},
                }
            },
            "_source": {
                "includes": [
                    "sku_code",
                    "name",
                    "description",
                    "category",
                    "price",
                    "stock_status",
                ]
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

            # Build result item
            result_item = {
                "sku_code": source.get("sku_code", ""),
                "name": source.get("name", ""),
                "description": source.get("description", ""),
                "category": source.get("category", ""),
                "price": source.get("price"),
                "stock_status": source.get("stock_status", ""),
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
    AWS Lambda handler for Japanese SKU search

    Expected event formats:

    POST request body:
    {
        "query": "search term",
        "size": 20,
        "filters": {"category": "medicine"}
    }

    GET request query parameters:
    ?q=search_term&size=20&category=medicine
    """

    logger.info(f"Lambda invoked with event: {json.dumps(event, ensure_ascii=False)}")

    try:
        # Initialize searcher
        searcher = JapaneseSKUSearcher()

        # Parse request parameters
        query, size, filters = _parse_request(event)

        if not query:
            return _create_response(400, {"error": "Missing required parameter: query"})

        # Perform search
        results = searcher.search_sku(query, size, filters)

        # Return successful response
        return _create_response(200, results)

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        return _create_response(
            500, {"error": "Internal server error", "message": str(e)}
        )


def _parse_request(event: Dict[str, Any]) -> tuple:
    """Parse Lambda event to extract search parameters"""

    # Default values
    query = None
    size = 20
    filters = {}

    # Handle API Gateway event
    if "httpMethod" in event:
        http_method = event.get("httpMethod", "GET")

        if http_method == "POST":
            # Parse POST body
            body = event.get("body", "{}")
            if isinstance(body, str):
                try:
                    body_data = json.loads(body)
                    query = body_data.get("query")
                    size = body_data.get("size", 20)
                    filters = body_data.get("filters", {})
                except json.JSONDecodeError:
                    logger.warning("Failed to parse POST body as JSON")
            else:
                query = body.get("query")
                size = body.get("size", 20)
                filters = body.get("filters", {})

        elif http_method == "GET":
            # Parse query parameters
            query_params = event.get("queryStringParameters") or {}
            query = query_params.get("q") or query_params.get("query")
            size = int(query_params.get("size", 20))

            # Extract filter parameters
            for key, value in query_params.items():
                if key not in ["q", "query", "size"]:
                    filters[key] = value

    # Handle direct invocation
    else:
        query = event.get("query")
        size = event.get("size", 20)
        filters = event.get("filters", {})

    # Validate and constrain size
    size = max(1, min(size, 100))  # Between 1 and 100

    logger.info(f"Parsed request - query: '{query}', size: {size}, filters: {filters}")

    return query, size, filters


def _create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized Lambda response"""

    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(body, ensure_ascii=False, separators=(",", ":")),
    }

    logger.debug(f"Lambda response: {response}")
    return response
