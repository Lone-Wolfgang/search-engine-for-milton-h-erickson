import os
from opensearchpy import OpenSearch
import streamlit as st
from modules.search import compose_query_body, init_hybrid_pipeline
from modules.util import (
    get_aggs,
    get_opensearch_client,
    format_hit
)

from opensearchpy.exceptions import TransportError

import json


def render_query_debugger(query_body):
    """
    Displays the raw and parsed query body for debugging.
    """
    st.markdown("### 🐞 Debugging: Current Query State")

    """ Show raw query string """
    st.markdown("**Raw Query:**")
    st.text(str(query_body))

    """ Attempt to parse and pretty-print JSON """
    st.markdown("**Parsed JSON (if applicable):**")
    try:
        if isinstance(query_body, str):
            parsed = json.loads(query_body)
        else:
            parsed = query_body

        if isinstance(parsed, (dict, list)):
            st.code(json.dumps(parsed, indent=2, ensure_ascii=False), language="json")
        else:
            st.warning("Parsed query is not a dict or list.")
    except Exception as e:
        st.warning(f"Could not parse query as JSON: {e}")


def setup_page(title):
    """
    Sets page configuration and title.
    """
    st.set_page_config(page_title=title, layout="wide")
    st.title(title)


def initialize_session_state(
    opensearch_host: str,
    pipeline_id: str,
    subquery_kwargs: list[dict],
    snippet_kwargs: dict={}
):
    """
    Sets up session state on first load.  Client & hybrid-pipeline
    registration only happen once.
    """
    # 1) Client
    if "client" not in st.session_state:
        st.session_state.client = get_opensearch_client(opensearch_host)

    # 2) Hybrid pipeline
    if "subquery_kwargs" not in st.session_state:
        st.session_state.subquery_kwargs = init_hybrid_pipeline(
            st.session_state.client,
            pipeline_id,
            subquery_kwargs
        )
    
    if "enable_snippets" not in st.session_state:
        st.session_state.enable_snippets = snippet_kwargs.pop("enable_snippets", False)
        st.session_state.snippet_kwargs = snippet_kwargs

    # 3) Any other defaults
    defaults = {
        "query_input": "",
        "query_body": compose_query_body(),  # or {} if you build later
        "page_number": 1,
        "filters_applied": False,
        "selected_authors": [],
        "selected_volumes": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar(client, index_name):
    """
    Renders sidebar filters, reset and pagination controls.
    """
    st.sidebar.markdown("### 🎯 Refine Your Search")
    st.sidebar.caption("Use the filters below to narrow down your results.")

    """ Fetch available values for filters """
    all_volumes, all_authors = get_aggs(client, index_name)

    """ Ensure session state keys are initialized """
    if "selected_volumes" not in st.session_state:
        st.session_state.selected_volumes = []
    if "selected_authors" not in st.session_state:
        st.session_state.selected_authors = []
    if "query_input" not in st.session_state:
        st.session_state.query_input = ""
    if "page_number" not in st.session_state:
        st.session_state.page_number = 1
    if "filters_applied" not in st.session_state:
        st.session_state.filters_applied = False

    """ Reset button clears all filters and restarts search """
    reset_button = st.sidebar.button("🔄 Reset", type="secondary")
    if reset_button:
        st.session_state.selected_volumes = []
        st.session_state.selected_authors = []
        st.session_state.query_input = ""
        st.session_state.page_number = 1
        st.session_state.filters_applied = False
        st.rerun()

    """ Filter selection widgets """
    st.sidebar.multiselect("📚 Volume", all_volumes, key="selected_volumes")
    st.sidebar.multiselect("👤 Author", all_authors, key="selected_authors")

    """ Apply filter button """
    col1, col2 = st.sidebar.columns(2)
    with col1:
        apply_filters = st.button("🔎 Apply Filters", type="secondary")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📄 Page Navigation")

    """ Pagination controls """
    if st.sidebar.button("⬅️ Previous") and st.session_state.page_number > 1:
        st.session_state.page_number -= 1
    if st.sidebar.button("➡️ Next"):
        st.session_state.page_number += 1

    """ Manual page input """
    page_input = st.sidebar.text_input("Jump to page", value=str(st.session_state.page_number))
    if page_input.isdigit():
        st.session_state.page_number = max(1, int(page_input))

    """ Mark filters as applied when the user clicks Apply """
    if apply_filters:
        st.session_state.filters_applied = True
        st.session_state.page_number = 1


def render_main_input(user_prompt):
    """
    Renders the main search input box.
    """
    query_input = st.text_input(
        user_prompt[0],
        placeholder=user_prompt[1],
        value=st.session_state.get("query_input", ""),
        key="query_input"
    )
    return query_input


def get_filter_input():
    """
    Collects selected filters from session state into a list of field-value tuples.
    """
    return [
        ('volume', st.session_state.selected_volumes),
        ('author', st.session_state.selected_authors)
    ]



def search_documents(
    client: OpenSearch,
    index: str,
    query_body: dict,
    size: int,
    search_pipeline: str=""
):
    """
    Executes a hybrid search and manually deduplicates + reranks the results.
    """
    if "hybrid" not in query_body["query"].keys():
        response = client.search(body=query_body, index=index)
    
    try:
        response = client.search(
            index=index,
            body=query_body,
            size=200,
            params={"search_pipeline": search_pipeline}
        )

        if "hits" not in response or "hits" not in response["hits"]:
            return []

        hits = response["hits"]["hits"]

        # Deduplicate by _id, keep max score
        deduped = {}
        for hit in hits:
            doc_id = hit["_id"]
            score = hit.get("_score", 0)
            if doc_id not in deduped or score > deduped[doc_id]["_score"]:
                deduped[doc_id] = hit

        # Sort by score again
        reranked = sorted(deduped.values(), key=lambda x: x["_score"], reverse=True)

        if not size:
            size = len(reranked)
        response["hits"]["hits"] = reranked
        return response

    except TransportError as e:
        print("OpenSearch Error:")
        print(f"Status code: {e.status_code}")
        print(f"Error message: {e.error}")
        print(f"Additional info: {e.info}")
        raise


def render_results(response, page_size=10):
    """
    Displays paginated search results with titles, metadata, and highlights.
    """
    page = st.session_state.page_number
    results = response["hits"]["hits"]
    total_hits = response["hits"]["total"]["value"]

    if not results:
        st.warning("No results found.")

    offset = (page - 1) * page_size
    page_hits = results[offset : page * page_size]
    st.markdown(f"### Showing page {page} of {((total_hits - 1) // page_size) + 1}")

    for hit in page_hits:
        title, metadata, unsafe, snippets = format_hit(hit)
        st.markdown(f"### {title}", unsafe_allow_html=unsafe)
        st.markdown(metadata)
        if snippets:
            for snippet in snippets:
                st.markdown(snippet)
        st.markdown("---")

