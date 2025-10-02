"""
OpenSearch Indexer for Japanese SKU Master Data
Optimized for fuzzy matching with Japanese text variations
"""

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import csv
import os
from datetime import datetime


class JapaneseSKUIndexer:
    def __init__(self):
        self.aws_profile = "welfan-lg-mfa"
        self.aws_region = "ap-northeast-3"
        self.endpoint = (
            "search-fuzzy-sku-ppba34qtds6ocweyl62wmgv5we.aos.ap-northeast-3.on.aws"
        )
        self.index_name = "sku-master"
        self.client = None

    def connect(self):
        """Connect to OpenSearch with AWS authentication"""
        try:
            print(f"🔧 Connecting with profile: {self.aws_profile}")

            session = boto3.Session(profile_name=self.aws_profile)
            credentials = session.get_credentials()

            if not credentials:
                raise Exception(
                    f"AWS credentials not found for profile: {self.aws_profile}"
                )

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
                timeout=30,
            )

            # Test connection
            health = self.client.cluster.health()
            print(f"✅ Connected! Cluster: {health['status']}")
            return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def create_optimized_index(self):
        """Create index optimized for Japanese SKU fuzzy matching"""

        # Advanced mapping for Japanese text with multiple analyzers
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "index.max_ngram_diff": 7,
                "analysis": {
                    "char_filter": {
                        "normalize_chars": {
                            "type": "mapping",
                            "mappings": [
                                # Zenkaku to Hankaku numbers
                                "０ => 0",
                                "１ => 1",
                                "２ => 2",
                                "３ => 3",
                                "４ => 4",
                                "５ => 5",
                                "６ => 6",
                                "７ => 7",
                                "８ => 8",
                                "９ => 9",
                                # Zenkaku to Hankaku alphabets
                                "Ａ => A",
                                "Ｂ => B",
                                "Ｃ => C",
                                "Ｄ => D",
                                "Ｅ => E",
                                "Ｆ => F",
                                "Ｇ => G",
                                "Ｈ => H",
                                "Ｉ => I",
                                "Ｊ => J",
                                "Ｋ => K",
                                "Ｌ => L",
                                "Ｍ => M",
                                "Ｎ => N",
                                "Ｏ => O",
                                "Ｐ => P",
                                "Ｑ => Q",
                                "Ｒ => R",
                                "Ｓ => S",
                                "Ｔ => T",
                                "Ｕ => U",
                                "Ｖ => V",
                                "Ｗ => W",
                                "Ｘ => X",
                                "Ｙ => Y",
                                "Ｚ => Z",
                                # Lowercase versions
                                "ａ => a",
                                "ｂ => b",
                                "ｃ => c",
                                "ｄ => d",
                                "ｅ => e",
                                "ｆ => f",
                                "ｇ => g",
                                "ｈ => h",
                                "ｉ => i",
                                "ｊ => j",
                                "ｋ => k",
                                "ｌ => l",
                                "ｍ => m",
                                "ｎ => n",
                                "ｏ => o",
                                "ｐ => p",
                                "ｑ => q",
                                "ｒ => r",
                                "ｓ => s",
                                "ｔ => t",
                                "ｕ => u",
                                "ｖ => v",
                                "ｗ => w",
                                "ｘ => x",
                                "ｙ => y",
                                "ｚ => z",
                                # Special characters
                                "（ => (",
                                "） => )",
                                "－ => -",
                                "　 => ",
                                "～ => ~",
                                "・ => ・",
                                "／ => /",
                                "＋ => +",
                                "＝ => =",
                            ],
                        },
                        "katakana_hiragana": {
                            "type": "mapping",
                            "mappings": [
                                # ----- Gojūon -----
                                "ア => あ",
                                "イ => い",
                                "ウ => う",
                                "エ => え",
                                "オ => お",
                                "カ => か",
                                "キ => き",
                                "ク => く",
                                "ケ => け",
                                "コ => こ",
                                "サ => さ",
                                "シ => し",
                                "ス => す",
                                "セ => せ",
                                "ソ => そ",
                                "タ => た",
                                "チ => ち",
                                "ツ => つ",
                                "テ => て",
                                "ト => と",
                                "ナ => な",
                                "ニ => に",
                                "ヌ => ぬ",
                                "ネ => ね",
                                "ノ => の",
                                "ハ => は",
                                "ヒ => ひ",
                                "フ => ふ",
                                "ヘ => へ",
                                "ホ => ほ",
                                "マ => ま",
                                "ミ => み",
                                "ム => む",
                                "メ => め",
                                "モ => も",
                                "ヤ => や",
                                "ユ => ゆ",
                                "ヨ => よ",
                                "ラ => ら",
                                "リ => り",
                                "ル => る",
                                "レ => れ",
                                "ロ => ろ",
                                "ワ => わ",
                                "ヲ => を",
                                "ン => ん",
                                # ----- Dakuten / Handakuten -----
                                "ガ => が",
                                "ギ => ぎ",
                                "グ => ぐ",
                                "ゲ => げ",
                                "ゴ => ご",
                                "ザ => ざ",
                                "ジ => じ",
                                "ズ => ず",
                                "ゼ => ぜ",
                                "ゾ => ぞ",
                                "ダ => だ",
                                "ヂ => ぢ",
                                "ヅ => づ",
                                "デ => で",
                                "ド => ど",
                                "バ => ば",
                                "ビ => び",
                                "ブ => ぶ",
                                "ベ => べ",
                                "ボ => ぼ",
                                "パ => ぱ",
                                "ピ => ぴ",
                                "プ => ぷ",
                                "ペ => ぺ",
                                "ポ => ぽ",
                                # ----- Small kana -----
                                "ァ => ぁ",
                                "ィ => ぃ",
                                "ゥ => ぅ",
                                "ェ => ぇ",
                                "ォ => ぉ",
                                "ッ => っ",
                                "ャ => ゃ",
                                "ュ => ゅ",
                                "ョ => ょ",
                                "ヮ => ゎ",
                                # ----- Historical kana -----
                                "ヰ => ゐ",
                                "ヱ => ゑ",
                                # ----- V-sounds (modern; put longer first) -----
                                "ヴァ => ゔぁ",
                                "ヴィ => ゔぃ",
                                "ヴゥ => ゔぅ",
                                "ヴェ => ゔぇ",
                                "ヴォ => ゔぉ",
                                "ヴ => ゔ",
                                # Single-codepoint VA/VI/VE/VO → modern
                                "ヷ => ゔぁ",
                                "ヸ => ゔぃ",
                                "ヹ => ゔぇ",
                                "ヺ => ゔぉ",
                                # ----- Small KA/KE (counters; no auto-voicing) -----
                                "ヵ => か",
                                "ヶ => け",
                                # ----- Iteration marks (use kuromoji_iteration_mark if possible) -----
                                "ヽ => ゝ",
                                "ヾ => ゞ",
                                # ----- Keep-as-is for product formatting -----
                                "ー => ー",
                                "・ => ・",
                                # ----- Ainu small kana (Katakana Phonetic Extensions) -----
                                "ㇰ => く",
                                "ㇱ => し",
                                "ㇲ => す",
                                "ㇳ => と",
                                "ㇴ => ぬ",
                                "ㇵ => は",
                                "ㇶ => ひ",
                                "ㇷ => ふ",
                                "ㇷ゚ => ぷ",
                                "ㇸ => へ",
                                "ㇹ => ほ",
                                "ㇺ => む",
                                "ㇻ => ら",
                                "ㇼ => り",
                                "ㇽ => る",
                                "ㇾ => れ",
                                "ㇿ => ろ",
                            ],
                        },
                    },
                    "tokenizer": {
                        "japanese_char_ngram": {
                            "type": "ngram",
                            "min_gram": 2,
                            "max_gram": 4,
                            "token_chars": ["letter", "digit"],
                        }
                    },
                    "analyzer": {
                        # Standard Japanese analyzer - for basic word-level matching
                        # Normalizes text and uses Kuromoji for proper Japanese tokenization
                        "japanese_standard": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",  # Convert to dictionary form
                                "kuromoji_part_of_speech",  # Filter by POS tags
                                "cjk_width",  # Normalize character width
                                "lowercase",
                            ],
                        },
                        # N-gram analyzer - for prefix/autocomplete matching
                        # Good for "as-you-type" search functionality
                        "japanese_ngram": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "cjk_width",
                                "lowercase",
                                "edge_ngram_filter",  # Creates prefix tokens (2-8 chars)
                            ],
                        },
                        # Character-level fuzzy analyzer - for typo tolerance
                        # Handles character-level variations and misspellings
                        "japanese_fuzzy": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "japanese_char_ngram",  # Character n-grams
                            "filter": [
                                "cjk_width",
                                "lowercase",
                            ],
                        },
                        # Partial word matching - for incomplete queries
                        # Allows matching parts of words within compound terms
                        "japanese_partial": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "cjk_width",
                                "lowercase",
                                "char_ngram_filter",  # Creates 2-4 char n-grams
                            ],
                        },
                        # Exact match analyzer - for precise queries
                        # Treats entire input as single token for exact matching
                        "exact_match": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "keyword",  # No tokenization, exact match
                            "filter": ["cjk_width", "lowercase"],
                        },
                        # Reading analyzer - for phonetic matching
                        # Useful for matching different writings of same pronunciation
                        "reading_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "cjk_width",
                                "lowercase",
                            ],
                        },
                        # Synonym analyzer - for domain-specific term matching
                        # Expands queries with related medical/care product terms
                        "synonym_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "cjk_width",
                                "lowercase",
                                "product_synonyms",  # Applies synonym mappings
                            ],
                        },
                        # Romaji analyzer - for English/ASCII input matching
                        # Converts Japanese to ASCII for cross-language search
                        "romaji_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "cjk_width",
                                "lowercase",
                                "asciifolding",  # Converts to ASCII equivalents
                            ],
                        },
                    },
                    "filter": {
                        # Edge n-gram filter - creates prefix tokens for autocomplete
                        # Generates tokens like: "シャ", "シャワ", "シャワー" from "シャワー"
                        "edge_ngram_filter": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 8,
                        },
                        # Character n-gram filter - creates overlapping character sequences
                        # Generates tokens like: "シャ", "ャワ", "ワー" from "シャワー"
                        "char_ngram_filter": {
                            "type": "ngram",
                            "min_gram": 2,
                            "max_gram": 4,
                        },
                        # ASCII folding filter - converts accented/Japanese chars to ASCII
                        # Helps with cross-language matching (トイレ → toilet)
                        "asciifolding": {
                            "type": "asciifolding",
                            "preserve_original": True,  # Keep both original and ASCII versions
                        },
                        # Product synonym filter - expands medical/care product terminology
                        # Maps related terms: "車椅子" ↔ "車いす" ↔ "車イス" ↔ "ウィールチェア"
                        "product_synonyms": {
                            "type": "synonym",
                            "synonyms": [
                                "介護用おむつ,大人用おむつ,失禁用おむつ,アダルトダイパー,紙おむつ",
                                "尿取りパッド,尿とりパッド,失禁パッド,介護パッド",
                                "ポータブルトイレ,簡易トイレ,介護トイレ,移動式トイレ",
                                "温水洗浄便座,ウォシュレット,シャワートイレ",
                                "便器,便座,便座容器,ベッドパン",
                                "車いす,車椅子,車イス,ウィールチェア",
                                "歩行器,シルバーカー,ロレータ,ローラータ,ローラトール",
                                "杖,つえ,ステッキ,歩行杖",
                                "移乗用リフト,介護リフト,リフター,つり上げリフト",
                                "シニアカー,電動シニアカー,電動カート,モビリティスクーター",
                                "介護ベッド,介護用ベッド,電動ベッド,リクライニングベッド",
                                "体圧分散マットレス,エアマットレス,褥瘡予防マットレス,褥瘡マット",
                                "離床センサー,見守りセンサー,徘徊センサー,起き上がりセンサー",
                                "シャワーチェア,入浴用いす,入浴椅子,風呂いす",
                                "口腔ケア,口腔清拭,口腔用スポンジ,オーラルケア",
                                "使い捨て手袋,使い切り手袋,ニトリル手袋,ラテックス手袋,ビニール手袋",
                                "マスク,サージカルマスク,介護用マスク,不織布マスク",
                                "消毒液,アルコール消毒,除菌液,エタノール消毒",
                                "体温計,デジタル体温計,非接触体温計,でこ温度計",
                                "血圧計,上腕式血圧計,手首式血圧計",
                                "パルスオキシメーター,パルスオキシメータ,血中酸素濃度計,SpO2計",
                                "とろみ剤,増粘剤,トロミ剤",
                                "栄養補助食品,介護食,ソフト食,ミキサー食",
                                "自動,オート,ジドウ,オートマチック",
                                "センサー,感知器,センサ,赤外線センサー",
                                "ポータブル,持ち運び,移動式,携帯",
                                "床ずれ防止,褥瘡予防,じょくそう予防",
                            ],
                        },
                    },
                },
            },
            "mappings": {
                "properties": {
                    # Primary ID field - integer identifier for each SKU
                    "id": {"type": "integer"},
                    # Main SKU name field with multiple sub-fields for different search strategies
                    "sku_name": {
                        "type": "text",
                        "analyzer": "japanese_standard",  # Default analyzer for indexing
                        "search_analyzer": "japanese_partial",  # Different analyzer for search queries
                        "fields": {
                            # Exact match field - for precise queries (highest priority)
                            "exact": {"type": "text", "analyzer": "exact_match"},
                            # N-gram field - for prefix/autocomplete matching
                            "ngram": {"type": "text", "analyzer": "japanese_ngram"},
                            # Fuzzy field - for character-level typo tolerance
                            "fuzzy": {"type": "text", "analyzer": "japanese_fuzzy"},
                            # Partial field - for incomplete word matching
                            "partial": {"type": "text", "analyzer": "japanese_partial"},
                            # Synonym field - for domain-specific term expansion
                            "synonym": {"type": "text", "analyzer": "synonym_analyzer"},
                            # Romaji field - for English/ASCII cross-language search
                            "romaji": {"type": "text", "analyzer": "romaji_analyzer"},
                            # Keyword field - for aggregations and exact filtering
                            "keyword": {"type": "keyword", "ignore_above": 256},
                        },
                    },
                    # Original text field - preserves raw input for reference
                    "original_text": {
                        "type": "text",
                        "analyzer": "japanese_standard",
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                    },
                    # Reading field - for phonetic variations and pronunciation matching
                    "reading": {
                        "type": "text",
                        "analyzer": "reading_analyzer",
                        "search_analyzer": "japanese_fuzzy",  # Use fuzzy for reading searches
                        "fields": {
                            "keyword": {"type": "keyword", "ignore_above": 256},
                            "romaji": {"type": "text", "analyzer": "romaji_analyzer"},
                        },
                    },
                    # Category field - for filtering and grouping products
                    "category": {"type": "keyword"},
                    # Timestamp fields - for data management and versioning
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            },
        }

        try:
            if self.client.indices.exists(index=self.index_name):
                print(f"⚠️  Index '{self.index_name}' exists")
                choice = input("Delete and recreate? (y/N): ").lower()
                if choice in ["y", "yes"]:
                    self.client.indices.delete(index=self.index_name)
                    print(f"🗑️  Deleted: {self.index_name}")
                else:
                    return True

            self.client.indices.create(index=self.index_name, body=mapping)
            print(f"✅ Created optimized index: {self.index_name}")
            return True

        except Exception as e:
            print(f"❌ Index creation failed: {e}")
            return False

    def index_sku_data(self, csv_file="TM_SYOHIN_202509302313.csv"):
        """Index SKU master data from CSV with batch processing"""

        if not os.path.exists(csv_file):
            print(f"❌ File not found: {csv_file}")
            return False

        try:
            print(f"📄 Reading: {csv_file}")
            products = []

            with open(csv_file, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                header = next(reader, None)
                print(f"Header: {header}")

                for row_id, row in enumerate(reader, start=1):
                    if row and row[0].strip():
                        sku_name = row[0].strip()

                        # Extract product info for better categorization
                        category = "unknown"
                        if any(x in sku_name for x in ["便座", "トイレ", "KX", "FX"]):
                            category = "toilet_products"
                        elif any(x in sku_name for x in ["暖房", "温水"]):
                            category = "heating_products"
                        elif any(x in sku_name for x in ["ポータブル", "フレーム"]):
                            category = "portable_products"

                        product = {
                            "id": row_id,
                            "sku_name": sku_name,
                            "original_text": sku_name,
                            "category": category,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                        }
                        products.append(product)

            print(f"📊 Loaded {len(products)} SKU records")

            # Bulk index with progress tracking
            batch_size = 100
            total_indexed = 0

            for i in range(0, len(products), batch_size):
                batch = products[i : i + batch_size]
                bulk_body = []

                for product in batch:
                    bulk_body.extend(
                        [
                            {
                                "index": {
                                    "_index": self.index_name,
                                    "_id": product["id"],
                                }
                            },
                            product,
                        ]
                    )

                response = self.client.bulk(body=bulk_body)

                # Check for errors
                errors = 0
                if response.get("errors"):
                    for item in response["items"]:
                        if "index" in item and "error" in item["index"]:
                            errors += 1
                            print(
                                f"   Error ID {item['index']['_id']}: {item['index']['error']['reason']}"
                            )

                total_indexed += len(batch) - errors
                batch_num = (i // batch_size) + 1
                print(
                    f"📝 Batch {batch_num}: {len(batch) - errors}/{len(batch)} indexed (Total: {total_indexed})"
                )

            # Refresh index for immediate search
            self.client.indices.refresh(index=self.index_name)
            print(f"🎉 Successfully indexed {total_indexed} SKU records")

            # Show index statistics
            stats = self.client.indices.stats(index=self.index_name)
            doc_count = stats["indices"][self.index_name]["total"]["docs"]["count"]
            size = stats["indices"][self.index_name]["total"]["store"]["size_in_bytes"]
            print(f"📈 Index stats: {doc_count} docs, {size:,} bytes")

            return True

        except Exception as e:
            print(f"❌ Indexing failed: {e}")
            return False

    def validate_index(self):
        """Validate indexed data with sample searches"""
        print("\n🔍 Validating index with sample searches...")

        test_cases = [
            # Exact matches - should find exact products
            "FX-1",  # Exact SKU code
            "KX-SDR",  # Another exact SKU code
            "ポータブルトイレEX-T型",  # Full product name
            # Japanese variations - test normalization
            "便座",  # Common toilet seat term
            "暖房",  # Heating term
            "シャワーベンチ",  # Shower bench (katakana)
            "しゃわーべんち",  # Same in hiragana (should match)
            "ｼｬﾜｰﾍﾞﾝﾁ",  # Half-width katakana (should normalize)
            # Partial/typo scenarios - fuzzy matching
            "FX1",  # Missing hyphen
            "KX SDR",  # Space instead of hyphen
            "ﾎﾟｰﾀﾌﾞﾙ",  # Partial katakana
            "ポータブル",  # Full katakana version
            "トイレ",  # Generic toilet term
            # Complex product names from CSV
            "電動便座昇降機",  # Electric toilet seat lift
            "吸着すべり止めマット",  # Anti-slip mat
            "木製玄関台",  # Wooden entrance platform
            "浴槽台",  # Bath platform
            # Synonym testing (when we add synonyms back)
            "ウォシュレット",  # Should match 温水洗浄便座
            "車椅子",  # Should match 車いす variants
            "車イス",  # Another wheelchair variant
            "車いす",  # Yet another variant
            # Edge cases - numbers and special chars
            "22×1",  # Numbers with special chars
            "#3000",  # Hash + numbers
            "45W-30-1段",  # Complex alphanumeric
            # Long product names
            "ひじ掛け付シャワーベンチK-TH",  # Long descriptive name
            "折りたたみシャワーベンチ",  # Foldable shower bench
            # Medical/care products
            "ステソスコープ",  # Stethoscope
            "血圧計",  # Blood pressure monitor
            # Katakana brand names
            "リットマン",  # Littmann (brand)
            "コラリッチ",  # Collagen product
            # Partial matches that should work
            "メイジ",  # Brand prefix (might not exist)
            "グラン",  # GRAN series
            "ルミエ",  # RUMIE series
            "スタイル",  # Style series
            # Numbers only
            "3000",  # Should find #3000 items
            "45",  # Should find various 45* items
            # Common misspellings/variations
            "シヤワー",  # ヤ instead of ャ
            "ベット",  # ッ instead of ド (bed)
            "マット",  # Mat/mattress
            # English/Romaji (if romaji analyzer works)
            "shower",  # English for シャワー
            "toilet",  # English for トイレ
            # Non-existent (should return no results gracefully)
            "存在しない商品",  # Non-existent product
            "NONEXIST-999",  # Non-existent SKU
        ]

        for query in test_cases:
            try:
                # Test multiple field searches for better Japanese matching
                response = self.client.search(
                    index=self.index_name,
                    body={
                        "query": {
                            "bool": {
                                "should": [
                                    {"match": {"sku_name": query}},
                                    {"match": {"sku_name.ngram": query}},
                                    {"match": {"sku_name.fuzzy": query}},
                                    {"match": {"sku_name.partial": query}},
                                ]
                            }
                        },
                        "size": 5,
                    },
                )

                hits = len(response["hits"]["hits"])
                total = response["hits"]["total"]["value"]
                print(f"   '{query}': {hits} results (total: {total})")

                # Show top result for debugging
                if hits > 0:
                    top_result = response["hits"]["hits"][0]
                    score = top_result["_score"]
                    name = top_result["_source"]["sku_name"]
                    print(f"      → Top: '{name}' (score: {score:.2f})")

            except Exception as e:
                print(f"   '{query}': Error - {e}")

        print("✅ Index validation complete")

    def simple_search(self, query, max_results=10):
        """Simple fuzzy search method for testing"""
        try:
            response = self.client.search(
                index=self.index_name,
                body={
                    "query": {
                        "bool": {
                            "should": [
                                {"match": {"sku_name": {"query": query, "boost": 3.0}}},
                                {
                                    "match": {
                                        "sku_name.exact": {"query": query, "boost": 2.0}
                                    }
                                },
                                {
                                    "match": {
                                        "sku_name.ngram": {"query": query, "boost": 1.5}
                                    }
                                },
                                {
                                    "match": {
                                        "sku_name.fuzzy": {"query": query, "boost": 1.0}
                                    }
                                },
                                {
                                    "match": {
                                        "sku_name.partial": {
                                            "query": query,
                                            "boost": 1.2,
                                        }
                                    }
                                },
                                {
                                    "match": {
                                        "sku_name.synonym": {
                                            "query": query,
                                            "boost": 1.8,
                                        }
                                    }
                                },
                            ]
                        }
                    },
                    "size": max_results,
                },
            )

            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]

            print(f"\n🔍 Search: '{query}'")
            print(f"📊 Found: {len(hits)} results (total: {total})")

            for i, hit in enumerate(hits, 1):
                name = hit["_source"]["sku_name"]
                score = hit["_score"]
                print(f"   {i:2d}. '{name}' (score: {score:.2f})")

            return hits

        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []


def main():
    """Main indexing process"""
    print("🚀 Japanese SKU Master Data Indexer")
    print("=" * 50)
    print("📋 Optimized for:")
    print("   - Japanese text variations (全角/半角)")
    print("   - Kanji/Hiragana/Katakana fuzzy matching")
    print("   - Multi-step AI search reasoning")
    print("   - Fast candidate retrieval")
    print("")

    indexer = JapaneseSKUIndexer()

    # Step 1: Connect
    if not indexer.connect():
        print("💥 Connection failed. Check troubleshooter.")
        return

    # Step 2: Create optimized index
    if not indexer.create_optimized_index():
        print("💥 Index creation failed.")
        return

    # Step 3: Index SKU data
    if not indexer.index_sku_data():
        print("💥 Data indexing failed.")
        return

    # Step 4: Validate
    indexer.validate_index()

    print("\n🎉 Indexing complete! Ready for fuzzy search testing.")

    # Optional: Interactive search mode
    while True:
        try:
            query = input("\n🔎 Enter search query (or 'quit' to exit): ").strip()
            if query.lower() in ["quit", "exit", "q", ""]:
                break
            indexer.simple_search(query)
        except KeyboardInterrupt:
            break

    print("👋 Session ended.")


if __name__ == "__main__":
    main()
