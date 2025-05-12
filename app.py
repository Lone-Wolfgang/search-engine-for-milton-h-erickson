# app.py
import streamlit as st
from modules.ux import (
    compose_query_body,
    get_filter_input,
    search_documents,
    setup_page,
    initialize_session_state,
    render_sidebar,
    render_main_input,
    render_query_debugger,
    render_results
)

from config import (
    DEBUG,
    HYBRID_PIPELINE_ID,
    INDEX_NAME,
    OPENSEARCH_HOST,
    PAGE_SIZE,
    RESULT_SIZE,
    SNIPPET_KWARGS,
    SUBQUERY_KWARGS,
    TAB_TITLE,
    USER_PROMPT
)

# --- Setup
setup_page(TAB_TITLE)
initialize_session_state(
    OPENSEARCH_HOST,
    SUBQUERY_KWARGS,
    HYBRID_PIPELINE_ID,
    SNIPPET_KWARGS
)

# --- Sidebar and Input
render_sidebar(st.session_state.client, INDEX_NAME)
query_input = render_main_input(USER_PROMPT)
filter_input = get_filter_input()


# --- Dynamically incorporate user input into queries
st.session_state.query_body = compose_query_body(
    query_input = query_input,
    filter_input = filter_input,
    all_subquery_kwargs=st.session_state.subquery_kwargs,
    enable_snippets=st.session_state.enable_snippets,
    snippet_kwargs=st.session_state.snippet_kwargs
)

if DEBUG:
    render_query_debugger(st.session_state.query_body)


# --- Issue the queries to OpenSearch and render the results
results = search_documents(
    client=st.session_state.client, 
    index=INDEX_NAME, 
    query_body=st.session_state.query_body,
    size = RESULT_SIZE,
    search_pipeline=HYBRID_PIPELINE_ID)

render_results(results, PAGE_SIZE)



