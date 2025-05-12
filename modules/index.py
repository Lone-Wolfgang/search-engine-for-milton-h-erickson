import base64
from opensearchpy import OpenSearch
from pathlib import Path
from tqdm import tqdm
from typing import Optional

from modules.util import (
    extract_headers,
    get_title_and_author,
    lemmatize,
    load_text,
    parse_filename
)

def encode_pdf(file: Path) -> Optional[str]:
    """Encode the PDF as base64 for storage in OpenSearch."""
    try:
        with open(file, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding {file.name}: {e}")
        return None

def setup_ingestion_pipeline_and_index(client: OpenSearch, index_name: str, model_id: str):
    """Creates the embedding pipeline and vector index for semantic search."""
    pipeline_id = "text-embedding-pipeline"

    # 1. Create the ingest pipeline
    pipeline_body = {
        "description": "Generate embeddings for title, headers, and lemmatized content",
        "processors": [
            {
                "text_embedding": {
                    "model_id": model_id,
                    "field_map": {
                        "title": "title_embedding",
                        "lemmatized": "content_embedding"
                    }
                }
            }
        ]
    }

    client.ingest.put_pipeline(id=pipeline_id, body=pipeline_body)
    print("✅ Ingest pipeline created.")

    # 2. Create the vector index
    if not client.indices.exists(index=index_name):
        index_body = {
            "settings": {
                "index.knn": True,
                "default_pipeline": pipeline_id,
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "path": {"type": "keyword"},
                    "content": {"type": "text"},
                    "lemmatized": {"type": "text"},
                    "content_embedding": {
                        "type": "knn_vector",
                        "dimension": 384,
                        "method": {
                            "engine": "lucene",
                            "space_type": "l2",
                            "name": "hnsw",
                            "parameters": {}
                        }
                    },
                    "title": {"type": "text"},
                    "title_embedding": {
                        "type": "knn_vector",
                        "dimension": 384,
                        "method": {
                            "engine": "lucene",
                            "space_type": "l2",
                            "name": "hnsw",
                            "parameters": {}
                        }
                    },
                    "headers": {"type": "text"},
                    "volume": {"type": "keyword"},
                    "order": {"type": "integer"},
                    "section": {"type": "text"},
                    "chapter": {"type": "text"},
                    "author": {"type": "keyword"},
                    "pdf": {"type": "text", "index": False}
                }
            }
        }

        client.indices.create(index=index_name, body=index_body)
        print(f"✅ Vector index '{index_name}' created.")
    else:
        print(f"ℹ️ Index '{index_name}' already exists.")

def index_documents(client: OpenSearch, folder: Path, index_name: str, model_id: str):
    """Load and index documents from a folder, including lemmatized text and embeddings."""

    # Set up pipeline + index if needed
    setup_ingestion_pipeline_and_index(client, index_name, model_id)

    actions = []
    for file in tqdm(list(folder.iterdir()), desc='Indexing Documents'):
        if file.suffix.lower() not in {'.pdf', '.txt', '.text', '.docx'}:
            continue

        text = load_text(file)
        if not text:
            continue

        volume, order, section, chapter = parse_filename(file)
        title, author = get_title_and_author(text)
        headers = extract_headers(text)

        text = text.replace("*", "")

        lemmatized = lemmatize(text).replace('\n', ' ').strip()

        doc = {
            "path": str(file.resolve()),
            "content": text,
            "lemmatized": lemmatized,
            "volume": volume,
            "order": order,
            "section": section,
            "chapter": chapter,
            "title": title or "",
            "author": author if author else [],
            "headers": headers if headers else []
        }

        if file.suffix == ".pdf":
            encoded_pdf = encode_pdf(file)
            if encoded_pdf:
                doc["pdf"] = encoded_pdf

        actions.append({
            "_index": index_name,
            "_id": file.stem,
            "_source": doc
        })

    if actions:
        for action in actions:
            client.index(
            index=action["_index"],
            id=action["_id"],
            body=action["_source"],
            pipeline="text-embedding-pipeline"
        )
    else:
        print("⚠️ No valid files found to index.")
