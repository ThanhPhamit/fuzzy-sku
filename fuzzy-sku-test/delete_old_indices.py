"""
Delete old OpenSearch indices
Run this before indexing with new structure
"""

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3


def delete_indices():
    """Delete old indices from OpenSearch"""

    aws_profile = "welfan-lg-mfa"
    aws_region = "ap-northeast-3"
    endpoint = "search-fuzzy-sku-ppba34qtds6ocweyl62wmgv5we.aos.ap-northeast-3.on.aws"

    print("🔧 Connecting to OpenSearch...")

    try:
        session = boto3.Session(profile_name=aws_profile)
        credentials = session.get_credentials()

        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            aws_region,
            "es",
            session_token=credentials.token,
        )

        client = OpenSearch(
            hosts=[{"host": endpoint, "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30,
        )

        # List all indices
        print("\n📋 Current indices:")
        indices = client.cat.indices(format="json")

        if not indices:
            print("   (No indices found)")
            return

        for idx in indices:
            index_name = idx["index"]
            # Skip system indices (starting with .)
            if not index_name.startswith("."):
                doc_count = idx.get("docs.count", "0")
                size = idx.get("store.size", "N/A")
                print(f"   - {index_name}: {doc_count} docs, {size}")

        print("\n⚠️  WARNING: This will delete ALL non-system indices!")
        print("   Old indices to delete:")
        print("   - sku-master (old structure)")
        print("   - tm-juchum (if exists)")

        confirm = input("\n❓ Continue? Type 'DELETE' to confirm: ").strip()

        if confirm != "DELETE":
            print("❌ Cancelled. No indices deleted.")
            return

        # Delete non-system indices
        deleted = []
        for idx in indices:
            index_name = idx["index"]
            if not index_name.startswith("."):
                try:
                    client.indices.delete(index=index_name)
                    deleted.append(index_name)
                    print(f"✅ Deleted: {index_name}")
                except Exception as e:
                    print(f"❌ Failed to delete {index_name}: {e}")

        if deleted:
            print(f"\n🎉 Successfully deleted {len(deleted)} indices:")
            for name in deleted:
                print(f"   - {name}")
        else:
            print("\n⚠️  No indices were deleted.")

        print("\n✨ Ready to create new index structure!")
        print("   Run: pipenv run python sku_indexer.py")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    delete_indices()
