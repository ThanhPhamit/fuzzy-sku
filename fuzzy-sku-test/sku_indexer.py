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
                        # Converts Japanese (Hiragana/Katakana/Kanji) to Latin alphabet (Romaji)
                        "romaji_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "kuromoji_readingform",  # Converts to Katakana reading
                                "romaji_readingform",  # Converts Katakana → Romaji
                                "cjk_width",
                                "lowercase",
                            ],
                        },
                        # Pure Romaji converter - converts everything to Latin alphabet
                        # Best for cross-language matching (Japanese input → English output)
                        "to_romaji_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_readingform",  # Kanji → Katakana (シャワー)
                                "romaji_readingform",  # Katakana → Romaji (shawaa)
                                "cjk_width",
                                "lowercase",
                            ],
                        },
                        # Latin N-gram analyzer - for substring matching in Latin text
                        # KEY SOLUTION: Index "MOGU" → creates n-grams: "mo", "og", "gu", "mog", "ogu", "mogu"
                        # Then search "もぐっち" → converts to "mogucchi" → matches "mogu" n-gram
                        "latin_ngram_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars"],
                            "tokenizer": "standard",  # Standard tokenizer for Latin text
                            "filter": [
                                "lowercase",
                                "latin_ngram_filter",  # Creates n-grams for Latin text
                            ],
                        },
                        # Romaji Edge N-gram analyzer - for prefix matching on Romaji
                        # Solves: "もぐっち" (mogucchi) should match "MOGU" (mogu) as prefix
                        # Index: "mogucchi" → edge n-grams ["m", "mo", "mog", "mogu", "moguc", "mogucc", "mogucch", "mogucchi"]
                        # Search: "mogu" → matches edge n-gram "mogu"
                        "romaji_edge_ngram_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_readingform",  # Convert to Katakana reading
                                "romaji_readingform",  # Convert to Romaji
                                "lowercase",
                                "romaji_edge_ngram_filter",  # Create edge n-grams
                            ],
                        },
                        # Standard analyzer for Romaji search (no n-gram at search time)
                        "romaji_search_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_readingform",
                                "romaji_readingform",
                                "lowercase",
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
                        # Kuromoji reading form - converts Kanji to Katakana reading
                        # Example: 車椅子 → クルマイス (phonetic reading)
                        "kuromoji_readingform": {
                            "type": "kuromoji_readingform",
                            "use_romaji": False,  # First convert to Katakana
                        },
                        # Romaji reading form - converts Katakana to Latin alphabet
                        # Example: シャワー → shawaa, トイレ → toire
                        "romaji_readingform": {
                            "type": "kuromoji_readingform",
                            "use_romaji": True,  # Convert to Romaji (Latin alphabet)
                        },
                        # Latin N-gram filter - creates n-grams for Latin/ASCII text
                        # Example: "MOGU" → ["mo", "og", "gu", "mog", "ogu", "mogu"]
                        # This allows "mogu" (from もぐっち) to match "MOGU"
                        "latin_ngram_filter": {
                            "type": "ngram",
                            "min_gram": 2,
                            "max_gram": 6,  # Support longer brand names
                        },
                        # Romaji Edge N-gram filter - creates prefix n-grams for Romaji
                        # Example: "mogucchi" → ["m", "mo", "mog", "mogu", "moguc", "mogucc", "mogucch", "mogucchi"]
                        # Allows prefix search: "mogu" matches "mogucchi"
                        "romaji_edge_ngram_filter": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 10,  # Support longer Japanese words in Romaji
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
                            # Allows searching Japanese products using English alphabet
                            # Example: "shawaa" can match "シャワー"
                            "romaji": {"type": "text", "analyzer": "romaji_analyzer"},
                            # Pure Latin alphabet conversion - stores Japanese as Romaji
                            # Example: "車椅子" → "kurumaisu", "トイレ" → "toire"
                            "latin": {"type": "text", "analyzer": "to_romaji_analyzer"},
                            # Latin N-gram field - KEY SOLUTION for Japanese → Latin matching
                            # Indexes Latin text with n-grams: "MOGU" → ["mo","og","gu","mog","ogu","mogu"]
                            # Allows "もぐっち"→"mogucchi" to match "MOGU"→"mogu" n-gram
                            "latin_ngram": {
                                "type": "text",
                                "analyzer": "latin_ngram_analyzer",
                            },
                            # Romaji Edge N-gram field - CRITICAL for prefix matching
                            # Indexes Romaji with edge n-grams: "mogucchi" → ["mo","mog","mogu","moguc"...]
                            # Allows partial search: "もぐっち"→"mogu" to match full "MOGU" brand
                            "romaji_ngram": {
                                "type": "text",
                                "analyzer": "romaji_edge_ngram_analyzer",
                                "search_analyzer": "romaji_search_analyzer",
                            },
                            # Keyword field - for aggregations and exact filtering
                            "keyword": {"type": "keyword", "ignore_above": 256},
                        },
                    },
                    # Timestamp field - when this SKU was indexed
                    "indexed_at": {"type": "date"},
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

                        product = {
                            "sku_name": sku_name,
                            "indexed_at": datetime.now().isoformat(),
                        }
                        products.append(product)

            print(f"📊 Loaded {len(products)} SKU records")

            # Bulk index with progress tracking
            batch_size = 100
            total_indexed = 0

            for i in range(0, len(products), batch_size):
                batch = products[i : i + batch_size]
                bulk_body = []

                for idx, product in enumerate(batch, start=i + 1):
                    bulk_body.extend(
                        [
                            {
                                "index": {
                                    "_index": self.index_name,
                                    "_id": idx,  # Use sequential index as ID
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

        test_cases = []

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
        """
        Production-ready search for Japanese SKU matching
        Optimized for bi-directional Japanese ↔ Latin matching
        """
        try:
            # ===== STRATEGY 1: Japanese Field Matching =====
            # Search in main Japanese fields with various analyzers
            japanese_queries = [
                # Main field - highest boost for exact matches
                {"match": {"sku_name": {"query": query, "boost": 5.0}}},
                # Exact match - for precise queries
                {"match": {"sku_name.exact": {"query": query, "boost": 4.0}}},
                # N-gram - for prefix/autocomplete matching
                {"match": {"sku_name.ngram": {"query": query, "boost": 3.0}}},
                # Fuzzy - for character-level typo tolerance
                {"match": {"sku_name.fuzzy": {"query": query, "boost": 2.5}}},
                # Partial - for incomplete word matching
                {"match": {"sku_name.partial": {"query": query, "boost": 3.0}}},
                # Synonym - for domain-specific term expansion
                {"match": {"sku_name.synonym": {"query": query, "boost": 2.5}}},
            ]

            # ===== STRATEGY 2: Romaji/Latin Field Matching =====
            # These fields use analyzers that convert Japanese → Romaji at INDEX time
            # Query will be converted by field's search_analyzer automatically
            # NO need to set "analyzer" here - let OpenSearch use field's analyzer!
            romaji_queries = [
                # Romaji field - Japanese text indexed as romaji
                {"match": {"sku_name.romaji": {"query": query, "boost": 3.0}}},
                # Latin field - pure romaji conversion
                {"match": {"sku_name.latin": {"query": query, "boost": 3.0}}},
                # Latin N-gram - KEY for substring matching (もぐっち → MOGU)
                # This is the most important field for Japanese → Latin brand matching
                {"match": {"sku_name.latin_ngram": {"query": query, "boost": 5.0}}},
                # Romaji Edge N-gram - CRITICAL for prefix matching (もぐっち → MOGU)
                # Allows partial Japanese input to match Latin brand names
                # Example: "もぐっち"→"mogu" matches "MOGU" brand via edge n-grams
                {"match": {"sku_name.romaji_ngram": {"query": query, "boost": 4.0}}},
            ]

            # ===== STRATEGY 3: Wildcard/Fuzzy Fallback (Low Priority) =====
            # Only used as last resort for edge cases
            # Keep boost low (1.0-1.5) to avoid performance issues
            # NOTE: Consider removing wildcard if index scales beyond 100k documents
            fallback_queries = [
                # Fuzzy matching for typos
                {
                    "fuzzy": {
                        "sku_name": {"value": query, "fuzziness": "AUTO", "boost": 1.2}
                    }
                },
            ]

            # Combine all strategies
            should_queries = []
            should_queries.extend(japanese_queries)
            should_queries.extend(romaji_queries)
            should_queries.extend(fallback_queries)

            response = self.client.search(
                index=self.index_name,
                body={
                    "query": {
                        "bool": {
                            "should": should_queries,
                            "minimum_should_match": 1,
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
