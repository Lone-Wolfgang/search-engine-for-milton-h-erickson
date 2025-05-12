from itertools import chain
from modules.util import (
    lemmatize, 
    remove_stopwords
)
from typing import Dict, List, Tuple
from opensearchpy import OpenSearch

def normalize(weights) -> List[float]:
    """
    Normalizes a list of weights so that they sum to 1.
    """
    total = sum(weights)
    return [w / total if total > 0 else 0 for w in weights]

def pop_weights_from_subquery_kwargs(all_subquery_kwargs: List[dict]):
    """
    Extracts and normalizes 'weight' values from a list of subquery kwargs.
    Returns normalized weights and the updated list without 'weight' keys.
    """
    weights = []
    for kwargs in all_subquery_kwargs:
        weights.append(kwargs.pop("weight"))
    
    weights = normalize(weights)
    return weights, all_subquery_kwargs

def compose_hybrid_pipeline(weights: List[float]):
    """
    Composes an OpenSearch hybrid post-processing pipeline using specified weights.
    """
    return {
        "description": "Post processor for hybrid search",
        "phase_results_processors": [
            {
                "normalization-processor": {
                    "normalization": {
                        "technique": "min_max"
                    },
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {
                            "weights": weights
                        }
                    }
                }
            }
        ]
    }

def init_hybrid_pipeline(
        client: OpenSearch,
        all_subquery_kwargs: List[dict],
        pipeline_id: str = ""
) -> Dict:
    """
    Creates a hybrid search pipeline in OpenSearch if 'neural' subqueries are present.
    Returns updated subquery kwargs with weights removed.
    """
    subquery_types = [kwargs["subquery_type"] for kwargs in all_subquery_kwargs]
    if "neural" not in subquery_types:
        return all_subquery_kwargs

    weights, all_subquery_kwargs = pop_weights_from_subquery_kwargs(all_subquery_kwargs)
    body = compose_hybrid_pipeline(weights)
    if not pipeline_id:
        raise ValueError("No pipeline ID found in configuration.")

    try:
        response = client.transport.perform_request(
            method="PUT",
            url=f"/_search/pipeline/{pipeline_id}",
            body=body
        )
        print(f"Pipeline '{pipeline_id}' initiated:", response)
        return all_subquery_kwargs
    except Exception as e:
        print(f"Failed to initiate pipeline '{pipeline_id}': {e}")

def preprocess_input(query_input: str) -> Dict[str, str]:
    """
    Lemmatizes and removes stopwords from the input query string.
    Returns original, lemmatized, and stripped (stopwords removed) versions.
    """
    if not query_input:
        return {}
    raw = query_input.strip()
    lemmatized = lemmatize(raw).replace('\n', ' ')
    stripped = remove_stopwords(lemmatized)
    return {
        "raw": raw,
        "lemmatized": lemmatized,
        "stripped": stripped
    }

def compose_subquery(
        processed_input: Dict[str, str],
        subquery_kwargs: Dict
) -> Dict:
    """
    Composes a single OpenSearch subquery from processed input and subquery parameters.
    """
    kwargs = subquery_kwargs.copy()
    possible_types = ["neural", "match", "match_phrase", "multi_match"]
    subquery_type = kwargs.pop("subquery_type")
    if subquery_type not in possible_types:
        raise ValueError(f"Not configured to produce {subquery_type} type subquery. Please select one of {possible_types}")

    input_key = "query_text" if subquery_type == "neural" else "query"
    input_value = processed_input[kwargs.pop("input_type")]
    input = {input_key: input_value}

    if subquery_type == "multi_match":
        subquery = {subquery_type: {**input, **kwargs}}
    else:
        field = kwargs.pop("field")
        subquery = {subquery_type: {field: {**input, **kwargs}}}
    
    return subquery

def compose_subqueries(
        processed_input: Dict[str, str],
        all_subquery_kwargs: List[Dict]
) -> List[Dict]:
    """
    Constructs a list of subqueries based on input and individual subquery parameters.
    """
    return [compose_subquery(processed_input, kwargs) for kwargs in all_subquery_kwargs] if processed_input else []

def compose_filter(filter_input: List[Tuple[str, List]]) -> List[Dict]:
    """
    Converts a list of (field, values) tuples into OpenSearch 'terms' filters.
    """
    return [
        {"terms": {field: values if isinstance(values, list) else [values]}}
        for field, values in filter_input
        if values
    ]

def compose_hybrid_query(
    subqueries: List[Dict],
    filter: List[Dict] = []
) -> Dict:
    """
    Builds a hybrid query with optional post-filter clauses.
    """
    query_body = {
        "query": {
            "hybrid": {
                "queries": subqueries
            }
        }
    }
    if filter:
        query_body["post_filter"] = {"bool": {"must": filter}}
    
    return query_body

def compose_bool_query(
        subqueries: List[Dict] = [],
        filter: List[Dict] = []
) -> Dict:
    """
    Builds a standard boolean query using 'should' and 'filter' clauses.
    """
    query_body = {
        "query": {
            "bool": {}
        }
    }
    if subqueries:
        query_body["query"]["bool"]["should"] = subqueries
    if filter:
        query_body["query"]["bool"]["filter"] = filter
    
    return query_body

def compose_sort() -> Dict:
    """
    Returns default sort configuration: by relevance score (desc), then order (asc).
    """
    return {
        "sort": [
            {"_score": {"order": "desc"}},
            {"order": {"order": "asc"}}
        ]
    }

def list_subquery_types(subqueries: List[Dict]) -> List[str]:
    """
    Extracts the subquery types from a list of subqueries.
    """
    return list(chain.from_iterable(sub.keys() for sub in subqueries))

def compose_highlight(
    processed_input: Dict[str, str] = {},
    enable_snippets: bool = False,
    snippet_kwargs: Dict = {}
) -> Dict:
    """
    Builds highlight config for OpenSearch using raw and stripped query input.
    Snippets are optional and can be customized via snippet_kwargs.
    """
    if not enable_snippets:
        return {}
    
    default_content = {
        "fragment_size": 300,
        "number_of_fragments": 3,
        "pre_tags": ["**"],
        "post_tags": ["**"],
        "highlight_query": {
            "bool": {
                "should": [
                    {
                        "match_phrase": {
                            "content": {
                                "query": processed_input.get("raw", "")
                            }
                        }
                    },
                    {
                        "match": {
                            "content": {
                                "query": processed_input.get("stripped", "")
                            }
                        }
                    }
                ]
            }
        }
    }

    return {"highlight": {"fields": {"content": {**default_content, **snippet_kwargs}}}}

def compose_query_body(
        query_input: str = "",
        filter_input: List[Tuple[str, List]] = [],
        all_subquery_kwargs: List[Dict] = [],
        enable_snippets: bool = False,
        snippet_kwargs: Dict = {}
) -> Dict:
    """
    Composes a complete OpenSearch query body, with optional filters, highlights, and hybrid search logic.
    Falls back to 'match_all' if no input is given.
    """
    filter = compose_filter(filter_input)
    if not query_input and not filter:
        query_body = {"query": {"match_all": {}}}
        highlight = {}
    else:
        processed_input = preprocess_input(query_input)
        subqueries = compose_subqueries(processed_input, all_subquery_kwargs)
        compose_query = compose_hybrid_query if "neural" in list_subquery_types(subqueries) else compose_bool_query
        query_body = compose_query(subqueries, filter)
        highlight = compose_highlight(processed_input, enable_snippets, snippet_kwargs)

    sort = compose_sort()
    return {**query_body, **highlight, **sort}

