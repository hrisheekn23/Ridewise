import os
import streamlit as st
from dotenv import load_dotenv
from db import get_schema, run_readonly_query
from policy import load_policy_chunks, search_policy
from llm import chat_completion, generate_sql
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

st.set_page_config(page_title="RideWise Assist", page_icon="🔋", layout="centered")

# ---------------------------------------------------------------- styling
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Figtree:wght@400;500;600;700&display=swap');

:root {
  --ink: #0F1B33;
  --ink-soft: #1A2A4D;
  --ink-line: #2B3C66;
  --cobalt: #2F4BFF;
  --cobalt-dark: #2339CC;
  --cobalt-tint: #EEF1FF;
  --mist: #F5F7FB;
  --surface: #FFFFFF;
  --line: #E2E7F1;
  --text: #17213A;
  --muted: #61708C;
  --ok: #12B76A;
  --shadow-sm: 0 1px 2px rgba(15, 27, 51, 0.05);
  --shadow-md: 0 6px 20px rgba(15, 27, 51, 0.07);
}

html, body, [class*="css"], .stApp, .stMarkdown, textarea, input, button {
  font-family: 'Figtree', 'Segoe UI', system-ui, sans-serif !important;
}
h1, h2, h3, .rw-wordmark, .rw-welcome h2 {
  font-family: 'Bricolage Grotesque', 'Segoe UI', sans-serif !important;
  letter-spacing: -0.02em;
}

.stApp { background: var(--mist); color: var(--text); }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 800px; padding-top: 1.6rem; padding-bottom: 7rem; }

/* ---- top bar ---- */
.rw-topbar {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
  padding: 14px 20px; box-shadow: var(--shadow-sm); margin-bottom: 1.4rem;
}
.rw-brand { display: flex; align-items: center; gap: 14px; }
.rw-battery {
  display: flex; gap: 3px; padding: 4px; border: 2.5px solid var(--ink);
  border-radius: 8px; position: relative; margin-right: 6px;
}
.rw-battery::after {
  content: ""; position: absolute; right: -8px; top: 7px; width: 5px; height: 10px;
  background: var(--ink); border-radius: 0 3px 3px 0;
}
.rw-battery i { display: block; width: 6px; height: 16px; border-radius: 2px; background: var(--cobalt); }
.rw-battery i:nth-child(4) { background: var(--line); }
.rw-wordmark { font-size: 1.55rem; font-weight: 800; color: var(--ink); line-height: 1.05; }
.rw-wordmark span { font-weight: 500; color: var(--cobalt); }
.rw-tagline { color: var(--muted); font-size: 0.86rem; margin-top: 2px; }
.rw-status {
  display: inline-flex; align-items: center; gap: 8px; white-space: nowrap;
  padding: 6px 12px; border-radius: 999px; background: var(--mist);
  border: 1px solid var(--line); font-size: 0.82rem; font-weight: 600; color: var(--ink);
}
.rw-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 0 3px rgba(18,183,106,0.18); }

/* ---- welcome panel ---- */
.rw-welcome { margin: 0.4rem 0 1.2rem 0; }
.rw-welcome h2 { font-size: 1.7rem; font-weight: 700; color: var(--ink); margin: 0 0 0.35rem 0; }
.rw-welcome p { color: var(--muted); margin: 0; max-width: 56ch; line-height: 1.55; }
.rw-suggest-label { font-weight: 600; color: var(--ink); margin: 1.2rem 0 0.5rem 0; font-size: 0.95rem; }

/* ---- sidebar ---- */
section[data-testid="stSidebar"] { background: var(--ink); border-right: 1px solid var(--ink-line); }
section[data-testid="stSidebar"] * { color: #E7ECF8; }
section[data-testid="stSidebar"] h2 { color: #fff; font-size: 1.15rem; }
section[data-testid="stSidebar"] input {
  background: var(--ink-soft) !important; color: #fff !important;
  border: 1px solid var(--ink-line) !important; border-radius: 10px !important;
}
section[data-testid="stSidebar"] input::placeholder { color: #8B9AC0 !important; }
section[data-testid="stSidebar"] .stButton button {
  background: var(--cobalt); border: 1px solid var(--cobalt); border-radius: 10px;
  color: #fff; font-weight: 600; padding: 0.55rem 0.9rem;
}
section[data-testid="stSidebar"] .stButton button:hover { background: var(--cobalt-dark); border-color: var(--cobalt-dark); }
section[data-testid="stSidebar"] hr { border-color: var(--ink-line); }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: #9DAAD0 !important; font-size: 0.8rem; }
.rw-pill {
  display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px;
  font-size: 0.82rem; background: var(--ink-soft); border: 1px solid var(--ink-line);
  color: #fff !important; font-weight: 600; margin: 6px 0 10px 0;
}
.rw-pill::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--ok); }

/* ---- chat bubbles ---- */
div[data-testid="stChatMessage"] {
  background: var(--surface) !important; border: 1px solid var(--line);
  border-radius: 4px 16px 16px 16px; padding: 1rem 1.15rem; margin-bottom: 0.95rem;
  box-shadow: var(--shadow-sm);
}
div[data-testid="stChatMessage"] *:not(code):not(pre):not(svg):not(path) { color: var(--text) !important; }
div[data-testid="stChatMessage"] [data-testid*="vatar"] {
  background: var(--cobalt-tint) !important; border-radius: 10px !important;
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  background: var(--cobalt) !important; border-color: var(--cobalt);
  border-radius: 16px 4px 16px 16px; margin-left: 14%; box-shadow: var(--shadow-md);
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) *:not(svg):not(path),
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) *:not(svg):not(path) { color: #FFFFFF !important; }
div[data-testid="stChatMessage"] p { line-height: 1.65; margin-bottom: 0.5rem; }
div[data-testid="stChatMessage"] pre, div[data-testid="stChatMessage"] code {
  background: #EEF1F8 !important; color: #12203A !important; border-radius: 8px;
}

/* ---- evidence expander ---- */
div[data-testid="stExpander"] {
  border: 1px solid var(--line); border-radius: 12px; background: var(--mist);
  margin-top: 0.4rem; box-shadow: none;
}
div[data-testid="stExpander"] summary { font-weight: 600; color: var(--ink); font-size: 0.9rem; }

/* ---- input + suggestion buttons ---- */
div[data-testid="stChatInput"] {
  border-radius: 14px; border: 1.5px solid var(--line); box-shadow: var(--shadow-md);
}
div[data-testid="stChatInput"]:focus-within { border-color: var(--cobalt); box-shadow: 0 0 0 4px rgba(47,75,255,0.12); }
[data-testid="stMain"] .stButton button, [data-testid="stMainBlockContainer"] .stButton button {
  border: 1px solid var(--line) !important; background: var(--surface) !important;
  border-radius: 12px; text-align: left; padding: 0.85rem 1rem; font-weight: 500;
  box-shadow: var(--shadow-sm); transition: border-color 0.15s, box-shadow 0.15s;
}
[data-testid="stMain"] .stButton button *, [data-testid="stMainBlockContainer"] .stButton button * {
  color: var(--ink) !important;
}
[data-testid="stMain"] .stButton button:hover {
  border-color: var(--cobalt) !important; box-shadow: var(--shadow-md);
}
[data-testid="stMain"] .stButton button:hover * { color: var(--cobalt-dark) !important; }

/* ---- alerts ---- */
div[data-testid="stAlert"] { border-radius: 12px; border: 1px solid var(--line); }

/* readable text on the light page, even if the browser/Streamlit theme is dark */
[data-testid="stMain"] .stMarkdown, [data-testid="stMain"] .stMarkdown p,
[data-testid="stMain"] label, [data-testid="stMain"] h1, [data-testid="stMain"] h2,
[data-testid="stMain"] h3 { color: var(--text) !important; }
div[data-testid="stExpander"] * { color: var(--ink) !important; }
div[data-testid="stExpander"] pre, div[data-testid="stExpander"] code {
  background: #EEF1F8 !important; color: #12203A !important;
}
div[data-testid="stChatInput"], div[data-testid="stChatInput"] textarea {
  background: #FFFFFF !important; color: var(--text) !important;
}
div[data-testid="stBottom"], div[data-testid="stBottom"] > div { background: var(--mist) !important; }

.rw-footnote { text-align: center; color: var(--muted); font-size: 0.78rem; margin-top: 1.6rem; }

:focus-visible { outline: 3px solid var(--cobalt) !important; outline-offset: 2px; }

@media (max-width: 640px) {
  .rw-topbar { flex-direction: column; align-items: flex-start; }
  div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
  div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) { margin-left: 4%; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def schema_text():
    return get_schema(os.getenv("RIDEWISE_DB_PATH", "ridewise.db"))

@st.cache_data(show_spinner=False)
def policy_chunks():
    return load_policy_chunks(os.getenv("POLICY_DIR", "policies"))

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Your session")
    role = st.radio("I am a", ["Customer", "Support agent"])
    customer_id = ""
    if role == "Customer":
        customer_id = st.text_input("Customer ID", placeholder="e.g. CUST0001").strip().upper()
        if customer_id:
            st.markdown(f'<span class="rw-pill">Signed in as {customer_id}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="rw-pill">Support agent view</span>', unsafe_allow_html=True)
    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Customer mode only shows data for the ID you enter.")
    st.caption("Never type API keys or passwords into the chat.")

# ---------------------------------------------------------------- top bar
session_label = f"Customer {customer_id}" if (role == "Customer" and customer_id) else (
    "Support agent" if role == "Support agent" else "Not signed in"
)
st.markdown(
    f"""
<div class="rw-topbar">
  <div class="rw-brand">
    <div class="rw-battery"><i></i><i></i><i></i><i></i></div>
    <div>
      <div class="rw-wordmark">RideWise <span>Assist</span></div>
      <div class="rw-tagline">Bookings, payments, refunds, penalties and EV rules</div>
    </div>
  </div>
  <div class="rw-status"><span class="rw-dot"></span>{session_label}</div>
</div>
""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if role == "Customer" and not customer_id:
    st.info("Enter your customer ID in the sidebar to start chatting.")
    st.stop()

# ---------------------------------------------------------------- history
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🔋"):
        st.markdown(message["content"])

# ---------------------------------------------------------------- input
queued = None
if not st.session_state.messages:
    st.markdown(
        """
<div class="rw-welcome">
  <h2>How can we help today?</h2>
  <p>Ask in plain language. Answers come from your account records and the official
  RideWise policy documents, and every answer shows the evidence behind it.</p>
</div>
<div class="rw-suggest-label">Popular questions</div>
""",
        unsafe_allow_html=True,
    )
    suggestions = [
        "What are my recent bookings?",
        "How much refund do I get if I cancel?",
        "Why was I charged a late return fee?",
        "What are the EV battery return rules?",
    ]
    cols = st.columns(2)
    for i, text in enumerate(suggestions):
        if cols[i % 2].button(text, key=f"sugg{i}", use_container_width=True):
            queued = text

typed = st.chat_input("Ask about a booking, refund, fee or policy")
question = queued or typed

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(question)

    try:
        with st.chat_message("assistant", avatar="🔋"):
            with st.spinner("Checking your account and the policy documents..."):
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

st.markdown(
    '<div class="rw-footnote">RideWise Assist can make mistakes. For disputes, contact a support agent.</div>',
    unsafe_allow_html=True,
)