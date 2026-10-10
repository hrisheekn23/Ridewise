import os
import streamlit as st
from dotenv import load_dotenv
from db import get_schema, run_readonly_query
from policy import load_policy_chunks, search_policy
from llm import chat_completion, generate_sql
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

st.set_page_config(page_title="RideWise Assist", page_icon="🛵", layout="wide")
st.title("🛵 RideWise Assist")
st.caption("AI support assistant for RideWise customers and support agents")

@st.cache_data(show_spinner=False)
def schema_text():
    return get_schema(os.getenv("RIDEWISE_DB_PATH", "ridewise.db"))

@st.cache_data(show_spinner=False)
def policy_chunks():
    return load_policy_chunks(os.getenv("POLICY_DIR", "policies"))

with st.sidebar:
    st.header("Start session")
    role = st.radio("I am a", ["Customer", "Support agent"])
    customer_id = ""
    if role == "Customer":
        customer_id = st.text_input("Customer ID", placeholder="e.g. CUST0001").strip().upper()
    if st.button("🆕 New conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Customer mode is restricted to the supplied customer ID.")
    st.caption("Never enter or expose API keys in chat.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if role == "Customer" and not customer_id:
    st.info("Enter your customer ID in the sidebar to start chatting.")
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about bookings, payments, refunds, penalties or EV rules...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    try:
        with st.chat_message("assistant"):
            with st.spinner("Checking the database and policy documents..."):
                schema = schema_text()
                chunks = policy_chunks()
                policy_hits = search_policy(question, chunks, limit=4)

                sql = generate_sql(
                    question=question,
                    schema=schema,
                    role=role,
                    customer_id=customer_id if role == "Customer" else None,
                )
                rows = []
                sql_note = ""
                if sql:
                    try:
                        rows = run_readonly_query(
                            sql,
                            db_path=os.getenv("RIDEWISE_DB_PATH", "ridewise.db"),
                            role=role,
                            customer_id=customer_id if role == "Customer" else None,
                        )
                    except Exception as exc:
                        sql_note = f"Database query could not be safely executed: {exc}"

                policy_text = "\n\n".join(
                    f"[{hit['source']}]\n{hit['text']}" for hit in policy_hits
                ) or "No relevant policy passage was found in the loaded documents."

                answer = chat_completion(
                    system_prompt=(
                        "You are RideWise Assist. Answer using only the supplied database rows "
                        "and policy excerpts. Do not invent facts, policy terms, amounts, or dates. "
                        "If evidence is missing, say so and ask a useful clarification. Distinguish "
                        "database facts from policy guidance. Do not reveal secrets or other customers' "
                        "private data. The database is authoritative for account/transaction facts; "
                        "policy documents are authoritative for rules. If policy versions conflict, "
                        "describe the conflict and do not silently choose a version."
                    ),
                    user_prompt=(
                        f"User role: {role}\n"
                        f"Customer ID (if customer): {customer_id or 'not applicable'}\n"
                        f"Question: {question}\n\n"
                        f"Database result rows (JSON-like Python representation): {rows}\n"
                        f"Database note: {sql_note or 'none'}\n\n"
                        f"Relevant policy excerpts:\n{policy_text}\n\n"
                        "Give a concise, clear answer. Mention when the provided evidence is insufficient."
                    ),
                    history=st.session_state.messages[-7:-1],
                )
            st.markdown(answer)
            with st.expander("Evidence used"):
                st.markdown("**Database query**")
                st.code(sql or "No database query generated", language="sql")
                st.markdown("**Policy excerpts**")
                st.markdown(policy_text)
            st.session_state.messages.append({"role": "assistant", "content": answer})
    except Exception as exc:
        message = (
            "I couldn't complete that request. Check that the NeoStats LLM credentials, "
            "database path, and policy folder are configured correctly."
        )
        st.error(message)
        st.caption(f"Technical detail: {exc}")
