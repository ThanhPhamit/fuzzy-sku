"""
AI-Powered Fuzzy SKU Search Tester
Multi-step reasoning for Japanese product name matching
POC for reducing manual SKU lookup from 1,500 to 500 cases
"""

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json
import re
from datetime import datetime


class AIFuzzySearcher:
    def __init__(self):
        self.aws_profile = "welfan-lg-mfa"
        self.aws_region = "ap-northeast-3"
        self.endpoint = (
            "search-fuzzy-sku-ppba34qtds6ocweyl62wmgv5we.aos.ap-northeast-3.on.aws"
        )
        self.index_name = "sku-master"
        self.client = None

        # AI reasoning strategies
        self.search_strategies = [
            "exact_match",
            "normalized_search",
            "fuzzy_search",
            "partial_match",
            "ngram_search",
            "relaxed_search",
        ]

    def connect(self):
        """Connect to OpenSearch"""
        try:
            session = boto3.Session(profile_name=self.aws_profile)
            credentials = session.get_credentials()

            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                self.aws_region,
                "es",
                session_token=credentials.token,
            )

            self.client = OpenSearch(
                hosts=[{"host": self.endpoint, "port": 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
            )

            # Quick health check
            health = self.client.cluster.health()
            print(f"🔗 Connected to OpenSearch: {health['status']}")
            return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def normalize_japanese_text(self, text):
        """Normalize Japanese text for better matching"""
        # Full-width to half-width conversion
        normalize_map = {
            "０": "0",
            "１": "1",
            "２": "2",
            "３": "3",
            "４": "4",
            "５": "5",
            "６": "6",
            "７": "7",
            "８": "8",
            "９": "9",
            "Ａ": "A",
            "Ｂ": "B",
            "Ｃ": "C",
            "Ｄ": "D",
            "Ｅ": "E",
            "Ｆ": "F",
            "Ｇ": "G",
            "Ｈ": "H",
            "Ｉ": "I",
            "Ｊ": "J",
            "Ｋ": "K",
            "Ｌ": "L",
            "Ｍ": "M",
            "Ｎ": "N",
            "Ｏ": "O",
            "Ｐ": "P",
            "Ｑ": "Q",
            "Ｒ": "R",
            "Ｓ": "S",
            "Ｔ": "T",
            "Ｕ": "U",
            "Ｖ": "V",
            "Ｗ": "W",
            "Ｘ": "X",
            "Ｙ": "Y",
            "Ｚ": "Z",
            "（": "(",
            "）": ")",
            "－": "-",
            "　": " ",
        }

        normalized = text
        for full_width, half_width in normalize_map.items():
            normalized = normalized.replace(full_width, half_width)

        return normalized.strip()

    def extract_key_terms(self, query):
        """Extract key terms for focused search"""
        # Extract alphanumeric patterns (SKU-like)
        sku_patterns = re.findall(r"[A-Z0-9]+[-]?[A-Z0-9]*", query.upper())

        # Extract Japanese words (2+ characters)
        jp_words = re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{2,}", query)

        # Extract numbers
        numbers = re.findall(r"\d+", query)

        return {
            "sku_patterns": sku_patterns,
            "japanese_words": jp_words,
            "numbers": numbers,
        }

    def search_strategy_exact_match(self, query):
        """Strategy 1: Exact match search"""
        search_body = {"query": {"term": {"sku_name.keyword": query}}, "size": 10}
        return self._execute_search(search_body, "exact_match")

    def search_strategy_normalized(self, query):
        """Strategy 2: Normalized text search"""
        normalized_query = self.normalize_japanese_text(query)

        search_body = {
            "query": {
                "match": {"sku_name.exact": {"query": normalized_query, "boost": 2.0}}
            },
            "size": 10,
        }
        return self._execute_search(search_body, "normalized_search")

    def search_strategy_fuzzy(self, query):
        """Strategy 3: Fuzzy matching with AUTO fuzziness"""
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "fuzzy": {
                                "sku_name": {
                                    "value": query,
                                    "fuzziness": "AUTO",
                                    "boost": 2.0,
                                }
                            }
                        },
                        {
                            "match": {
                                "sku_name": {
                                    "query": query,
                                    "fuzziness": "AUTO",
                                    "boost": 1.5,
                                }
                            }
                        },
                    ]
                }
            },
            "size": 10,
        }
        return self._execute_search(search_body, "fuzzy_search")

    def search_strategy_partial(self, query):
        """Strategy 4: Partial matching with wildcards"""
        terms = self.extract_key_terms(query)

        should_queries = []

        # Search by SKU patterns
        for pattern in terms["sku_patterns"]:
            should_queries.append(
                {"wildcard": {"sku_name": {"value": f"*{pattern}*", "boost": 2.0}}}
            )

        # Search by Japanese words
        for word in terms["japanese_words"]:
            should_queries.append(
                {"wildcard": {"sku_name": {"value": f"*{word}*", "boost": 1.5}}}
            )

        if not should_queries:
            should_queries.append({"wildcard": {"sku_name": {"value": f"*{query}*"}}})

        search_body = {
            "query": {"bool": {"should": should_queries, "minimum_should_match": 1}},
            "size": 10,
        }
        return self._execute_search(search_body, "partial_match")

    def search_strategy_ngram(self, query):
        """Strategy 5: N-gram based search"""
        search_body = {
            "query": {
                "match": {
                    "sku_name.ngram": {"query": query, "minimum_should_match": "70%"}
                }
            },
            "size": 10,
        }
        return self._execute_search(search_body, "ngram_search")

    def search_strategy_relaxed(self, query):
        """Strategy 6: Most relaxed search with low threshold"""
        terms = self.extract_key_terms(query)

        should_queries = []

        # Add all possible variations
        all_terms = terms["sku_patterns"] + terms["japanese_words"] + terms["numbers"]

        for term in all_terms:
            if len(term) >= 2:  # Minimum 2 characters
                should_queries.extend(
                    [
                        {"match": {"sku_name": {"query": term, "boost": 1.0}}},
                        {
                            "wildcard": {
                                "sku_name": {"value": f"*{term}*", "boost": 0.8}
                            }
                        },
                    ]
                )

        if not should_queries:
            should_queries.append(
                {"match": {"sku_name": {"query": query, "minimum_should_match": "50%"}}}
            )

        search_body = {
            "query": {"bool": {"should": should_queries, "minimum_should_match": 1}},
            "size": 15,
        }
        return self._execute_search(search_body, "relaxed_search")

    def _execute_search(self, search_body, strategy_name):
        """Execute search and return results with metadata"""
        try:
            response = self.client.search(index=self.index_name, body=search_body)

            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]

            return {
                "strategy": strategy_name,
                "total_found": total,
                "results": hits,
                "success": True,
            }

        except Exception as e:
            return {
                "strategy": strategy_name,
                "total_found": 0,
                "results": [],
                "success": False,
                "error": str(e),
            }

    def ai_multi_step_search(self, customer_query, max_results=10):
        """AI Agent: Multi-step reasoning search process"""
        print(f"\n🤖 AI Agent analyzing: '{customer_query}'")
        print("=" * 60)

        # Step 1: Query analysis
        normalized_query = self.normalize_japanese_text(customer_query)
        key_terms = self.extract_key_terms(normalized_query)

        print(f"📊 Query Analysis:")
        print(f"   Original: {customer_query}")
        print(f"   Normalized: {normalized_query}")
        print(f"   SKU patterns: {key_terms['sku_patterns']}")
        print(f"   Japanese words: {key_terms['japanese_words']}")
        print(f"   Numbers: {key_terms['numbers']}")

        # Step 2: Multi-strategy search execution
        all_candidates = {}
        strategy_results = {}

        strategies = [
            ("exact_match", self.search_strategy_exact_match),
            ("normalized_search", self.search_strategy_normalized),
            ("fuzzy_search", self.search_strategy_fuzzy),
            ("partial_match", self.search_strategy_partial),
            ("ngram_search", self.search_strategy_ngram),
            ("relaxed_search", self.search_strategy_relaxed),
        ]

        print(f"\n🔍 Multi-step Search Execution:")

        for strategy_name, strategy_func in strategies:
            print(f"   Step {len(strategy_results) + 1}: {strategy_name}...", end=" ")

            if strategy_name in ["exact_match", "normalized_search"]:
                result = strategy_func(customer_query)
            else:
                result = strategy_func(normalized_query)

            strategy_results[strategy_name] = result

            if result["success"]:
                print(f"✅ {result['total_found']} found")

                # Collect unique candidates
                for hit in result["results"]:
                    doc_id = hit["_id"]
                    if doc_id not in all_candidates:
                        all_candidates[doc_id] = {
                            "document": hit,
                            "strategies": [],
                            "total_score": 0,
                            "max_score": 0,
                        }

                    all_candidates[doc_id]["strategies"].append(
                        {"strategy": strategy_name, "score": hit["_score"]}
                    )
                    all_candidates[doc_id]["total_score"] += hit["_score"]
                    all_candidates[doc_id]["max_score"] = max(
                        all_candidates[doc_id]["max_score"], hit["_score"]
                    )

                # Early exit if exact match found
                if strategy_name == "exact_match" and result["total_found"] > 0:
                    print("   🎯 Exact match found - stopping search")
                    break

            else:
                print(f"❌ Error: {result.get('error', 'Unknown')}")

        # Step 3: Candidate ranking and confidence scoring
        print(f"\n📈 AI Ranking & Confidence Analysis:")

        if not all_candidates:
            print("   ❌ No candidates found with any strategy")
            return []

        # Sort by combined score (max_score * strategy_count + total_score)
        ranked_candidates = sorted(
            all_candidates.items(),
            key=lambda x: (
                len(x[1]["strategies"]) * 10 + x[1]["max_score"] + x[1]["total_score"]
            ),
            reverse=True,
        )[:max_results]

        # Step 4: Present results with confidence
        final_results = []

        print(f"   🏆 Top {len(ranked_candidates)} candidates:")

        for rank, (doc_id, candidate_info) in enumerate(ranked_candidates, 1):
            doc = candidate_info["document"]["_source"]
            strategies_used = len(candidate_info["strategies"])
            confidence = min(
                95, max(60, strategies_used * 15 + candidate_info["max_score"] * 10)
            )

            result_item = {
                "rank": rank,
                "id": doc["id"],
                "sku_name": doc["sku_name"],
                "confidence": confidence,
                "strategies_matched": strategies_used,
                "max_score": candidate_info["max_score"],
                "total_score": candidate_info["total_score"],
                "strategy_details": candidate_info["strategies"],
            }

            final_results.append(result_item)

            print(f"   {rank:2d}. {doc['sku_name']}")
            print(
                f"       信頼度: {confidence}% | マッチ戦略: {strategies_used}/6 | スコア: {candidate_info['max_score']:.2f}"
            )

        return final_results

    def test_specific_case(self, target_sku, search_query):
        """Test specific case with detailed analysis"""
        print(f"\n🎯 Testing Specific Case:")
        print(f"   Target SKU: '{target_sku}'")
        print(f"   Customer Query: '{search_query}'")
        print("=" * 60)

        # First, check if target exists in index
        exact_search = self.client.search(
            index=self.index_name,
            body={"query": {"match": {"sku_name.keyword": target_sku}}, "size": 1},
        )

        if exact_search["hits"]["total"]["value"] == 0:
            print(f"⚠️  Target SKU '{target_sku}' not found in index")
            return False

        target_doc = exact_search["hits"]["hits"][0]
        print(f"✅ Target SKU found in index (ID: {target_doc['_id']})")

        # Test all search strategies
        strategies_to_test = [
            (
                "multi_field",
                {
                    "query": {
                        "bool": {
                            "should": [
                                {"match": {"sku_name": search_query}},
                                {"match": {"sku_name.ngram": search_query}},
                                {"match": {"sku_name.fuzzy": search_query}},
                                {"match": {"sku_name.partial": search_query}},
                            ]
                        }
                    },
                    "size": 10,
                },
            ),
            (
                "fuzzy_only",
                {
                    "query": {
                        "match": {
                            "sku_name.fuzzy": {
                                "query": search_query,
                                "minimum_should_match": "60%",
                            }
                        }
                    },
                    "size": 10,
                },
            ),
            (
                "ngram_only",
                {
                    "query": {
                        "match": {
                            "sku_name.ngram": {
                                "query": search_query,
                                "minimum_should_match": "70%",
                            }
                        }
                    },
                    "size": 10,
                },
            ),
            (
                "partial_only",
                {
                    "query": {
                        "match": {
                            "sku_name.partial": {
                                "query": search_query,
                                "minimum_should_match": "60%",
                            }
                        }
                    },
                    "size": 10,
                },
            ),
        ]

        found_target = False
        best_rank = None
        best_score = None

        for strategy_name, search_body in strategies_to_test:
            try:
                response = self.client.search(index=self.index_name, body=search_body)
                hits = response["hits"]["hits"]

                print(f"\n🔍 Strategy: {strategy_name}")
                print(f"   Total results: {len(hits)}")

                # Check if target is in results
                target_found_in_strategy = False
                for rank, hit in enumerate(hits, 1):
                    if hit["_source"]["sku_name"] == target_sku:
                        target_found_in_strategy = True
                        found_target = True
                        current_rank = rank
                        current_score = hit["_score"]

                        if best_rank is None or current_rank < best_rank:
                            best_rank = current_rank
                            best_score = current_score

                        print(
                            f"   ✅ Target found at rank {rank} (score: {current_score:.3f})"
                        )
                        break

                if not target_found_in_strategy:
                    print(f"   ❌ Target not found in top 10 results")

                # Show top 3 results for context
                print(f"   Top 3 results:")
                for i, hit in enumerate(hits[:3], 1):
                    name = hit["_source"]["sku_name"]
                    score = hit["_score"]
                    is_target = "🎯" if name == target_sku else "  "
                    print(f"   {is_target} {i}. '{name}' (score: {score:.3f})")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        # Summary
        print(f"\n📊 Test Summary:")
        if found_target:
            print(f"   ✅ Target SKU found!")
            print(f"   🏆 Best ranking: #{best_rank}")
            print(f"   📈 Best score: {best_score:.3f}")
        else:
            print(f"   ❌ Target SKU not found in any search strategy")
            print(f"   💡 Suggestion: Index needs further optimization")

        return found_target

    def interactive_poc_mode(self):
        """Interactive POC demonstration mode"""
        print("\n🎯 Fuzzy SKU Search POC - Interactive Mode")
        print("=" * 60)
        print("📋 Simulating customer order processing:")
        print("   • Enter fuzzy/incorrect SKU names")
        print("   • AI will provide ranked candidates")
        print("   • Reduces manual lookup time")
        print("")
        print("Type 'quit' to exit, 'test' for sample scenarios")

        # Sample test cases for demonstration
        test_cases = [
            (
                "メイジバランスソフト",
                "Missing characters from メイジメイバランスソフトフ",
            ),
            ("FX1", "Missing dash from FX-1"),
            ("便座", "Generic term - should find multiple matches"),
            ("KX-SDR　暖房", "Full-width space and partial match"),
            ("KXSDR", "No dashes, compressed format"),
        ]

        while True:
            try:
                print("\n" + "-" * 60)
                user_input = input("🔎 Enter customer SKU/product name: ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 POC session ended. Results summary available.")
                    break

                elif user_input.lower() == "test":
                    print("\n🧪 Running sample test cases...")
                    for test_query, description in test_cases:
                        print(f"\n📝 Test case: {description}")
                        results = self.ai_multi_step_search(test_query, max_results=5)
                        if results:
                            print(f"✅ Found {len(results)} candidates")
                        else:
                            print("❌ No matches found")
                        input("Press Enter for next test...")
                    continue

                elif not user_input:
                    continue

                # Run AI search
                start_time = datetime.now()
                results = self.ai_multi_step_search(user_input, max_results=8)
                end_time = datetime.now()

                search_time = (end_time - start_time).total_seconds()

                # Show summary
                print(f"\n⏱️  Search completed in {search_time:.2f} seconds")

                if results:
                    high_confidence = [r for r in results if r["confidence"] >= 80]
                    medium_confidence = [
                        r for r in results if 60 <= r["confidence"] < 80
                    ]

                    print(f"\n💯 Summary:")
                    print(
                        f"   High confidence (≥80%): {len(high_confidence)} candidates"
                    )
                    print(
                        f"   Medium confidence (60-79%): {len(medium_confidence)} candidates"
                    )
                    print(f"   Total candidates: {len(results)}")

                    if high_confidence:
                        print(
                            f"\n🎯 Recommended action: Select from top {len(high_confidence)} high-confidence matches"
                        )
                    else:
                        print(
                            f"\n⚠️  Recommended action: Review medium-confidence matches or escalate to manual search"
                        )
                else:
                    print("\n❌ No candidates found. Manual search required.")

            except KeyboardInterrupt:
                print("\n\n👋 POC session interrupted.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    """Main POC demonstration"""
    print("🚀 AI-Powered Fuzzy SKU Search POC")
    print("=" * 50)
    print("🎯 Target: Reduce manual lookups from 1,500 to 500 cases")
    print("🤖 AI Strategy: Multi-step reasoning + confidence scoring")
    print("🔍 Optimized for Japanese text variations")
    print("")

    searcher = AIFuzzySearcher()

    # Connect
    if not searcher.connect():
        print("💥 Connection failed. Run indexer first.")
        return

    # Check if index exists
    try:
        stats = searcher.client.indices.stats(index=searcher.index_name)
        doc_count = stats["indices"][searcher.index_name]["total"]["docs"]["count"]
        print(f"📊 SKU Master loaded: {doc_count:,} products")
    except:
        print("❌ Index not found. Run 'python sku_indexer.py' first.")
        return

    # Test specific case first
    print("\n🧪 Testing specific case from user request...")
    target_sku = "メイジメイバランスソフトフ"
    search_query = "メイジバランスソフト"

    # Note: This will only work if the target SKU exists in your CSV data
    test_result = searcher.test_specific_case(target_sku, search_query)

    if test_result:
        print("✅ Specific case test passed!")
    else:
        print(
            "⚠️ Specific case test needs attention - check if target SKU exists in data"
        )

    # Ask user what to do next
    print("\n" + "=" * 50)
    choice = input("Continue to interactive mode? (y/N): ").lower()

    if choice in ["y", "yes"]:
        # Start interactive POC
        searcher.interactive_poc_mode()
    else:
        print("👋 Testing completed.")


if __name__ == "__main__":
    main()
