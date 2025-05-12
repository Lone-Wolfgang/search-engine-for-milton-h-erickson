from modules.index import index_documents
from modules.util import get_opensearch_client
from pathlib import Path
import argparse
import sys
from config import INDEX_NAME, OPENSEARCH_HOST, MODEL_ID

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index documents into OpenSearch.")
    parser.add_argument(
        "--folder",
        type=Path,
        default=Path(INDEX_NAME),
        help="Folder containing documents to index (default: ./documents)"
    )
    args = parser.parse_args()

    if not args.folder.exists():
        print(f"Error: Folder '{args.folder}' does not exist.")
        sys.exit(1)

    print(f"Indexing documents in '{args.folder}'...")
    try:
        client = get_opensearch_client(OPENSEARCH_HOST)
        index_documents(client, args.folder, INDEX_NAME, MODEL_ID)
        print("Indexing completed successfully.")
    except Exception as e:
        print(f"Failed to index documents: {e}")
        sys.exit(1)
