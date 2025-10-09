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
        self.index_name = "tm-juchum"  # Changed to TM_JUCHUM index
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
                "index.max_ngram_diff": 10,  # Increased from 7 to support longer brand names
                "refresh_interval": "1s",  # Real-time search
                "index.translog.durability": "async",
                "index.translog.sync_interval": "5s",
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
                    # 🎯 MAIN COMPOSITE SEARCH FIELD - combines skname1 + hinban + colornm + sizename
                    # This is the PRIMARY field for searching aitehinmei queries
                    "search_text": {
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
                            # Pure Latin alphabet conversion - stores Japanese as Romaji
                            "latin": {"type": "text", "analyzer": "to_romaji_analyzer"},
                            # Latin N-gram field - KEY SOLUTION for Japanese → Latin matching
                            "latin_ngram": {
                                "type": "text",
                                "analyzer": "latin_ngram_analyzer",
                            },
                            # Romaji Edge N-gram field - CRITICAL for prefix matching
                            "romaji_ngram": {
                                "type": "text",
                                "analyzer": "romaji_edge_ngram_analyzer",
                                "search_analyzer": "romaji_search_analyzer",
                            },
                            # Keyword field - for aggregations and exact filtering
                            "keyword": {"type": "keyword", "ignore_above": 256},
                        },
                    },
                    # 📋 ORIGINAL FIELDS - returned in search results (NOT used for search)
                    # These fields are stored but not heavily indexed to save space
                    # hinban - Product code (exact match only, used for filtering)
                    "hinban": {
                        "type": "keyword",  # Keyword type for exact matching
                    },
                    # skname1 - Product name (stored for display)
                    "skname1": {
                        "type": "text",
                        "analyzer": "japanese_standard",
                        "index": False,  # Not indexed - only stored for display
                    },
                    # colorcd - Color code (NOT indexed, only stored for output)
                    "colorcd": {
                        "type": "keyword",
                        "index": False,  # 🔥 NOT indexed - saves space
                        "doc_values": True,  # Can still be returned in results
                    },
                    # colornm - Color name (stored for display)
                    "colornm": {
                        "type": "text",
                        "analyzer": "japanese_standard",
                        "index": False,  # Not indexed - only stored for display
                    },
                    # sizecd - Size code (NOT indexed, only stored for output)
                    "sizecd": {
                        "type": "keyword",
                        "index": False,  # 🔥 NOT indexed - saves space
                        "doc_values": True,  # Can still be returned in results
                    },
                    # sizename - Size name (stored for display)
                    "sizename": {
                        "type": "text",
                        "analyzer": "japanese_standard",
                        "index": False,  # Not indexed - only stored for display
                    },
                    # Timestamp field - when this record was indexed
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

    def index_sku_data(self, csv_file="TM_JUCHUM.csv"):
        """Index TM_JUCHUM data from CSV with composite search field"""

        if not os.path.exists(csv_file):
            print(f"❌ File not found: {csv_file}")
            return False

        try:
            print(f"📄 Reading: {csv_file}")
            products = []

            with open(csv_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(
                    file
                )  # Use DictReader to access columns by name

                for row_id, row in enumerate(reader, start=1):
                    # Extract individual fields
                    hinban = row.get("hinban", "").strip()
                    skname1 = row.get("skname1", "").strip()
                    colorcd = row.get("colorcd", "").strip()
                    colornm = row.get("colornm", "").strip()
                    sizecd = row.get("sizecd", "").strip()
                    sizename = row.get("sizename", "").strip()

                    # 🔥 KEY CHANGE: Create composite search text
                    # Combine searchable fields (skname1, hinban, colornm, sizename)
                    # EXCLUDE colorcd and sizecd (codes - not searchable)
                    search_text = f"{skname1} {hinban} {colornm} {sizename}".strip()

                    product = {
                        # Main search field (composite)
                        "search_text": search_text,
                        # Original fields for response
                        "hinban": hinban,
                        "skname1": skname1,
                        "colorcd": colorcd,
                        "colornm": colornm,
                        "sizecd": sizecd,
                        "sizename": sizename,
                        "indexed_at": datetime.now().isoformat(),
                    }
                    products.append(product)

            print(f"📊 Loaded {len(products)} TM_JUCHUM records")

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
        """Validate indexed data with sample aitehinmei searches"""
        print("\n🔍 Validating index with sample aitehinmei queries...")

        # Test cases based on real aitehinmei examples
        test_cases = [
            "ソフトグリップ SOFT-GA ／ ワイン",  # Example 1
            "503326　KMD-B22-42-SH/ライトブルー",  # Example 2
            "821181PH転びにくいシューズつま先有ワインS",  # Example 3
            "964033　サーティパッドPRO　Ag　600",  # Example 4
            "2303足元応援GW603両足27㎝茶",  # Example 5
            "310015  もぐピヨ イエロー",  # Example 6
            "カルガモファムⅡ折畳　リーフ柄",  # Example 7
            "402921ポータブルトイレFX-30",  # Example 8
            "477004アイソカルゼリーハイカロリー　チョコ",  # Example 9
            "アイソカル 高カロリーのやわらかいごはん 白がゆ",  # Example 10
        ]

        for query in test_cases:
            try:
                # Test search on composite field
                response = self.client.search(
                    index=self.index_name,
                    body={
                        "query": {
                            "bool": {
                                "should": [
                                    {
                                        "term": {
                                            "hinban": {"value": query, "boost": 10.0}
                                        }
                                    },
                                    {
                                        "match": {
                                            "search_text": {
                                                "query": query,
                                                "boost": 5.0,
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "search_text.ngram": {
                                                "query": query,
                                                "boost": 3.0,
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "search_text.fuzzy": {
                                                "query": query,
                                                "boost": 2.5,
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "search_text.partial": {
                                                "query": query,
                                                "boost": 3.0,
                                            }
                                        }
                                    },
                                ]
                            }
                        },
                        "_source": ["hinban", "skname1", "colornm", "sizename"],
                        "size": 3,
                    },
                )

                hits = len(response["hits"]["hits"])
                total = response["hits"]["total"]["value"]
                print(
                    f"\n   Query: '{query[:50]}...' → {hits} results (total: {total})"
                )

                # Show top results
                for i, hit in enumerate(response["hits"]["hits"], 1):
                    source = hit["_source"]
                    score = hit["_score"]
                    print(
                        f"      {i}. {source['hinban']} | {source['skname1']} | {source['colornm']} | {source['sizename']} (score: {score:.2f})"
                    )

            except Exception as e:
                print(f"   '{query}': Error - {e}")

        print("\n✅ Index validation complete")

    def simple_search(self, query, max_results=10):
        """
        Enhanced search with optimized boost strategy and function_score
        Input: aitehinmei (mixed skname1 + hinban + colornm + sizename)
        Output: hinban, skname1, colorcd, colornm, sizecd, sizename
        """
        try:
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

            response = self.client.search(
                index=self.index_name,
                body={
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
                    # 📋 Return all fields needed for output
                    "_source": [
                        "hinban",
                        "skname1",
                        "colorcd",
                        "colornm",
                        "sizecd",
                        "sizename",
                    ],
                    "highlight": {
                        "fields": {
                            "search_text": {},
                            "search_text.exact": {},
                            "search_text.ngram": {},
                        },
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"],
                    },
                    "size": max_results,
                },
            )

            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]

            print(f"\n🔍 Search: '{query}'")
            print(f"📊 Found: {len(hits)} results (total: {total})")
            print(
                f"{'#':<4} {'hinban':<12} {'skname1':<35} {'colorcd':<10} {'colornm':<15} {'sizecd':<10} {'sizename':<12} {'score':<8}"
            )
            print("-" * 130)

            for i, hit in enumerate(hits, 1):
                source = hit["_source"]
                score = hit["_score"]
                highlights = hit.get("highlight", {})
                matched_fields = ", ".join(highlights.keys()) if highlights else "N/A"

                print(
                    f"{i:<4} "
                    f"{source.get('hinban', ''):<12} "
                    f"{source.get('skname1', ''):<35} "
                    f"{source.get('colorcd', ''):<10} "
                    f"{source.get('colornm', ''):<15} "
                    f"{source.get('sizecd', ''):<10} "
                    f"{source.get('sizename', ''):<12} "
                    f"{score:<8.2f}"
                )

                # Show matched fields for debugging
                if highlights:
                    print(f"       └─ Matched: {matched_fields}")

            return hits

        except Exception as e:
            print(f"❌ Search failed: {e}")
            import traceback

            traceback.print_exc()
            return []


def main():
    """Main indexing process for TM_JUCHUM data"""
    print("🚀 TM_JUCHUM Data Indexer (aitehinmei search)")
    print("=" * 60)
    print("📋 Optimized for:")
    print("   - Search with aitehinmei (mixed skname1+hinban+colornm+sizename)")
    print("   - Japanese text variations (全角/半角)")
    print("   - Kanji/Hiragana/Katakana fuzzy matching")
    print("   - Return: hinban, skname1, colorcd, colornm, sizecd, sizename")
    print("   - NOT indexed: colorcd, sizecd (codes only for output)")
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

    # Step 3: Index TM_JUCHUM data
    if not indexer.index_sku_data("TM_JUCHUM.csv"):
        print("💥 Data indexing failed.")
        return

    # Step 4: Validate
    indexer.validate_index()

    print("\n🎉 Indexing complete! Ready for aitehinmei search testing.")
    print("\n💡 Example queries:")
    print("   - ソフトグリップ SOFT-GA ／ ワイン")
    print("   - 503326　KMD-B22-42-SH/ライトブルー")
    print("   - 821181PH転びにくいシューズつま先有ワインS")
    print("   - 310015  もぐピヨ イエロー")

    # Optional: Interactive search mode
    while True:
        try:
            query = input("\n🔎 Enter aitehinmei query (or 'quit' to exit): ").strip()
            if query.lower() in ["quit", "exit", "q", ""]:
                break
            indexer.simple_search(query)
        except KeyboardInterrupt:
            break

    print("👋 Session ended.")


if __name__ == "__main__":
    main()
