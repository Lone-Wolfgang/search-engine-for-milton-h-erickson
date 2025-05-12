# --- Config

# --- With Debugging enabled, the app diplays query body.
DEBUG = False

# --- Controls OpenSearch Settings.
# --- OPENSEARCH_HOST: Directs session to the appropriate node.
# --- INDEX_NAME: Within the node, identifies the apporiate index.
# --- MODEL_ID: Code for the ML model used in semantic search.
#               Issued when deployed. See OpenSearch Documentation.
# --- HYBRID_PIPELINE_ID: Identifier for the hybrid scoring pipeline.
#                         Dynamically updated with SUBQUERY_KWARGS.

INDEX_NAME = "documents"
OPENSEARCH_HOST = {"host": "localhost", "port": 9200}
MODEL_ID = "<YOUR MODEL ID>"
HYBRID_PIPELINE_ID = 'hybrid_reranker'

#Controls the text displayed in the user interface.
TAB_TITLE = "Document Search"
PAGE_TITLE = "📄 Search the Collected Works"
USER_PROMPT = ("Enter your search query:", "Search documents. . .")

#Controls the search algorithim.
SUBQUERY_KWARGS = [
    {
        "subquery_type": "neural",
        "input_type": "raw",
        "field": "content_embedding",
        "model_id": MODEL_ID,
        "k": 5,
        "weight": 0.2
    },
    {
        "subquery_type": "neural",
        "input_type": "raw",
        "field": "title_embedding",
        "model_id": MODEL_ID,
        "k": 5,
        "weight": 0.2,
    },
    # {
    #     "subquery_type": "neural",
    #     "input_type": "raw",
    #     "field": "headers",
    #     "model_id": MODEL_ID,
    #     "k":5,
    #     "weight": 0.2
    # },
    {
        "subquery_type": "multi_match",
        "input_type": "raw",
        "fields": ["title^3", "content"],
        "type": "best_fields",
        "weight": 0.2
    },
    {
        "subquery_type": "multi_match",
        "input_type": "lemmatized",
        "fields": ["lemmatized_content"],
        "type": "best_fields",
        "weight": 0.2
    }
]

#Controls whether or not to produce snippets, 
#and the number and character length of snippets.
SNIPPET_KWARGS = {
    "enable_snippets": True,
    "number_of_fragments": 3,
    "fragment_size": 300
}

#Controls the maximum number of documents to retrieve from the
#archive, and the number of results per page.
RESULT_SIZE = 200
PAGE_SIZE = 10



