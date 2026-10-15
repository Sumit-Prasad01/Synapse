import os
import sys
import requests
import streamlit as st
import pandas as pd

# Ensure workspace root is in python path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

st.set_page_config(
    page_title="Synapse - AI Data Analyst",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #6c757d;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .route-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .route-sql {
        background-color: #e3f2fd;
        color: #0d47a1;
        border: 1px solid #bbdefb;
    }
    .route-etl {
        background-color: #f3e5f5;
        color: #4a148c;
        border: 1px solid #e1bee7;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🧠 Synapse Settings")
    st.markdown("Autonomous Data Agent for SQL queries and ETL pipelines.")
    st.divider()

    api_url = st.text_input(
        "FastAPI Backend URL",
        value="http://127.0.0.1:8000",
        help="Address of the running FastAPI server"
    )

    # Health check
    backend_online = False
    try:
        health_resp = requests.get(f"{api_url.rstrip('/')}/health", timeout=2)
        if health_resp.status_code == 200:
            health_data = health_resp.json()
            if health_data.get("database_connected"):
                st.success("🟢 Backend & Database: Connected", icon="✅")
            else:
                st.warning("🟡 Backend Online (Database degraded)")
            backend_online = True
        else:
            st.error("🔴 Backend returned error status")
    except Exception:
        st.error("🔴 Backend Offline (Start with `uvicorn app.api:app --reload`)")

    st.divider()

    # Database Schema viewer
    with st.expander("📊 View Database Schema"):
        if backend_online:
            if st.button("Fetch Latest Schema"):
                try:
                    schema_res = requests.get(f"{api_url.rstrip('/')}/api/schema", timeout=5)
                    if schema_res.status_code == 200:
                        st.code(schema_res.json().get("schema", "No schema available"), language="markdown")
                except Exception as e:
                    st.error(f"Failed to fetch schema: {e}")
        else:
            st.info("Start backend to view live schema, or inspect `data/` tables: users, rides, payments, vehicles, ratings.")

    st.divider()

    # Sample Prompts
    st.subheader("💡 Example Queries")
    example_prompts = [
        "What are the payment methods in our database?",
        "How many active users are in the database?",
        "Show top 5 rides with the highest fare",
        "Extract data from https://pokeapi.co/api/v2/pokemon and save it to data/extract folder in the csv folder",
    ]

    for p in example_prompts:
        if st.button(p, key=f"ex_{p}"):
            st.session_state["pending_prompt"] = p

    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()


# -----------------------------------------------------------------------------
# App Header
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">🧠 Synapse — AI Data Analyst</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Ask natural language questions about your PostgreSQL database or request ETL tasks.</div>',
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "Hello! I am **Synapse**, your AI Data Analyst. Ask me anything about your database (e.g. users, rides, payments) or ask me to perform an ETL task on an external API.",
            "meta": None
        }
    ]

# -----------------------------------------------------------------------------
# Render Chat History
# -----------------------------------------------------------------------------
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        meta = msg.get("meta")
        if meta and meta.get("route"):
            route = meta.get("route").upper()
            badge_class = "route-sql" if route == "SQL" else "route-etl"
            st.markdown(f'<span class="route-badge {badge_class}">🔀 Routed to: {route} Analyst</span>', unsafe_allow_html=True)

        st.markdown(msg["content"])

        if meta and meta.get("sql_query"):
            with st.expander("📝 View Generated SQL Query"):
                st.code(meta["sql_query"], language="sql")
                if meta.get("is_safe"):
                    st.caption(f"**Safety Review:** Safe: `{meta['is_safe']}` | {meta.get('comments', '')}")

        if meta and meta.get("sql_result"):
            with st.expander("📊 Raw SQL Execution Result"):
                st.text(meta["sql_result"])


# -----------------------------------------------------------------------------
# User Input Handling
# -----------------------------------------------------------------------------
prompt = st.chat_input("Ask a question about your database or ETL task...")

if "pending_prompt" in st.session_state and st.session_state["pending_prompt"]:
    prompt = st.session_state.pop("pending_prompt")

if prompt:
    # 1. Display user message
    st.session_state["messages"].append({"role": "user", "content": prompt, "meta": None})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Get response from FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Analyzing request and executing agent workflow..."):
            try:
                endpoint = f"{api_url.rstrip('/')}/api/query"
                response = requests.post(endpoint, json={"question": prompt}, timeout=120)

                if response.status_code == 200:
                    data = response.json()
                    route = data.get("route", "")
                    answer = data.get("answer", "No answer generated.")
                    sql_query = data.get("sql_query")
                    sql_result = data.get("sql_result")
                    is_safe = data.get("is_safe")
                    comments = data.get("comments")

                    meta = {
                        "route": route,
                        "sql_query": sql_query,
                        "sql_result": sql_result,
                        "is_safe": is_safe,
                        "comments": comments,
                    }

                    # Display Route Badge
                    if route:
                        badge_class = "route-sql" if route.lower() == "sql" else "route-etl"
                        st.markdown(f'<span class="route-badge {badge_class}">🔀 Routed to: {route.upper()} Analyst</span>', unsafe_allow_html=True)

                    # Display Answer
                    st.markdown(answer)

                    # Display SQL Query Expander
                    if sql_query:
                        with st.expander("📝 View Generated SQL Query"):
                            st.code(sql_query, language="sql")
                            if is_safe:
                                st.caption(f"**Safety Review:** Safe: `{is_safe}` | {comments or ''}")

                    if sql_result:
                        with st.expander("📊 Raw SQL Execution Result"):
                            st.text(sql_result)

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": answer,
                        "meta": meta
                    })

                else:
                    err_msg = f"Backend returned status {response.status_code}: {response.text}"
                    st.error(err_msg)
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": f"⚠️ {err_msg}",
                        "meta": None
                    })

            except requests.exceptions.ConnectionError:
                offline_msg = f"Could not connect to FastAPI backend at `{api_url}`. Please make sure the backend is running (`uvicorn app.api:app --reload`)."
                st.error(offline_msg)
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"⚠️ {offline_msg}",
                    "meta": None
                })
            except Exception as e:
                err_msg = f"An unexpected error occurred: {str(e)}"
                st.error(err_msg)
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"⚠️ {err_msg}",
                    "meta": None
                })
