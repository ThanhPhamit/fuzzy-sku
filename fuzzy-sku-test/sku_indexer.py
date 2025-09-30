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
                                # Basic katakana to hiragana (46 characters)
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
                                # Dakuten (voiced) variants
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
                                # Handakuten (semi-voiced) variants
                                "パ => ぱ",
                                "ピ => ぴ",
                                "プ => ぷ",
                                "ペ => ぺ",
                                "ポ => ぽ",
                                # Small characters
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
                                # Special katakana
                                "ヴ => ゔ",
                                # ADD missing characters:
                                # Extended katakana (for foreign words)
                                "ヷ => わ゙",  # VA (rare)
                                "ヸ => ゐ゙",  # VI (rare)
                                "ヹ => ゑ゙",  # VE (rare)
                                "ヺ => を゙",  # VO (rare)
                                # Long vowel mark (keep as-is)
                                "ー => ー",  # Chōonpu - important for SKUs!
                                # Iteration marks
                                "ヽ => ゝ",  # Katakana iteration mark
                                "ヾ => ゞ",  # Katakana voiced iteration mark
                                # Middle dot (keep as-is for product names)
                                "・ => ・",  # Nakaguro - used in product names
                                # Small TSU variants (for foreign sounds)
                                "ヶ => が",  # Small KE (used in counters)
                                "ヵ => か",  # Small KA
                                # Additional small vowels (modern usage)
                                "ㇰ => く",  # Small KU
                                "ㇱ => し",  # Small SHI
                                "ㇲ => す",  # Small SU
                                "ㇳ => と",  # Small TO
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
                        "japanese_standard": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "kuromoji_part_of_speech",
                                "cjk_width",
                                "lowercase",
                            ],
                        },
                        "japanese_ngram": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "cjk_width",
                                "lowercase",
                                "edge_ngram_filter",
                            ],
                        },
                        "japanese_fuzzy": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "japanese_char_ngram",
                            "filter": [
                                "cjk_width",
                                "lowercase",
                            ],
                        },
                        "japanese_partial": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "cjk_width",
                                "lowercase",
                                "char_ngram_filter",
                            ],
                        },
                        "exact_match": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "keyword",
                            "filter": ["cjk_width", "lowercase"],
                        },
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
                        "synonym_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars", "katakana_hiragana"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "cjk_width",
                                "lowercase",
                                "product_synonyms",
                            ],
                        },
                        "romaji_analyzer": {
                            "type": "custom",
                            "char_filter": ["normalize_chars"],
                            "tokenizer": "kuromoji_tokenizer",
                            "filter": [
                                "kuromoji_baseform",
                                "cjk_width",
                                "lowercase",
                                "asciifolding",
                            ],
                        },
                    },
                    "filter": {
                        "edge_ngram_filter": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 8,
                        },
                        "char_ngram_filter": {
                            "type": "ngram",
                            "min_gram": 2,
                            "max_gram": 4,
                        },
                        "asciifolding": {
                            "type": "asciifolding",
                            "preserve_original": True,
                        },
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
                    "id": {"type": "integer"},
                    "sku_name": {
                        "type": "text",
                        "analyzer": "japanese_standard",
                        "search_analyzer": "japanese_partial",
                        "fields": {
                            "exact": {"type": "text", "analyzer": "exact_match"},
                            "ngram": {"type": "text", "analyzer": "japanese_ngram"},
                            "fuzzy": {"type": "text", "analyzer": "japanese_fuzzy"},
                            "partial": {"type": "text", "analyzer": "japanese_partial"},
                            "synonym": {"type": "text", "analyzer": "synonym_analyzer"},
                            "romaji": {"type": "text", "analyzer": "romaji_analyzer"},
                            "keyword": {"type": "keyword", "ignore_above": 256},
                        },
                    },
                    "original_text": {
                        "type": "text",
                        "analyzer": "japanese_standard",
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                    },
                    "reading": {
                        "type": "text",
                        "analyzer": "reading_analyzer",
                        "search_analyzer": "japanese_fuzzy",
                        "fields": {
                            "keyword": {"type": "keyword", "ignore_above": 256},
                            "romaji": {"type": "text", "analyzer": "romaji_analyzer"},
                        },
                    },
                    "category": {"type": "keyword"},
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

    def index_sku_data(self, csv_file="TM_SYOHIN_202509291906.csv"):
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
            "FX-1",
            "便座",
            "暖房",
            "KX-SDR",
            "メイジ",  # This might not exist but tests fuzzy matching
            "メイジバランスソフト",  # Test case for partial matching
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
    print("Next step: Run 'python fuzzy_search_tester.py'")


if __name__ == "__main__":
    main()
