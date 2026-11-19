"""Streamlit Interactive Web UI for the AI Assistant."""

import os
import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Production AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .metric-card {
        background: #1e293b;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 4px solid #3b82f6;
    }
    .citation-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.88rem;
    }
    .tool-box {
        background-color: #064e3b;
        border: 1px solid #059669;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.88rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Engine Settings")
    
    provider = st.selectbox(
        "LLM Provider",
        options=["gemini", "openai", "vllm", "mock"],
        index=0,
        help="Select primary LLM provider (or local vLLM / mock for testing)"
    )

    st.subheader("Hyperparameters")
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.5, value=0.7, step=0.05)
    top_p = st.slider("Top-p", min_value=0.1, max_value=1.0, value=0.9, step=0.05)
    max_tokens = st.slider("Max Tokens", min_value=128, max_value=2048, value=1024, step=64)

    st.subheader("Capabilities")
    enable_rag = st.checkbox("Enable RAG (Vector DB)", value=True)
    enable_tools = st.checkbox("Enable Tool Calling", value=True)
    use_cache = st.checkbox("Enable Response Cache", value=True)

    st.divider()
    st.subheader("📄 Knowledge Base Ingestion")
    uploaded_file = st.file_uploader("Upload Document (.txt, .md)", type=["txt", "md"])
    if uploaded_file is not None:
        if st.button("Index into Vector Store", use_container_width=True):
            with st.spinner("Chunking & embedding document..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                    res = requests.post(f"{API_URL}/api/rag/upload", files=files, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"Indexed {data['chunks_indexed']} chunks! Total: {data['total_store_count']}")
                    else:
                        st.error(f"Failed to ingest: {res.text}")
                except Exception as err:
                    st.error(f"API Error: {err}")

    st.divider()
    # Metrics
    try:
        metrics_res = requests.get(f"{API_URL}/api/metrics", timeout=2)
        if metrics_res.status_code == 200:
            m = metrics_res.json()
            st.metric("Vector DB Chunks", m.get("vector_store_count", 0))
            c_stats = m.get("cache_stats", {})
            st.metric("Cache Hit Rate", f"{c_stats.get('hit_rate_pct', 0)}%")
    except Exception:
        pass


# ---------------------------------------------------------
# Main Chat Area
# ---------------------------------------------------------
st.title("🤖 Enterprise AI Assistant")
st.caption("RAG-Augmented, Tool-Enabled, High-Availability AI Engine with Fallback & Caching")

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your AI Assistant. I can answer questions using knowledge base documents, evaluate mathematical calculations, check current timestamps, and browse simulated web information. How can I help you today?"}
    ]

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display Citations if available
        if "citations" in msg and msg["citations"]:
            with st.expander("📚 Source Citations & References", expanded=False):
                for c in msg["citations"]:
                    st.markdown(
                        f"<div class='citation-box'><b>Source:</b> {c['document_id']} (Score: {c.get('score', 'N/A')})<br/>"
                        f"<i>\"{c['content_snippet']}\"</i></div>",
                        unsafe_allow_html=True
                    )

        # Display Tool Executions if available
        if "tools_used" in msg and msg["tools_used"]:
            with st.expander("🛠️ Tools Executed", expanded=False):
                for t in msg["tools_used"]:
                    st.markdown(
                        f"<div class='tool-box'><b>Tool:</b> <code>{t['tool_name']}</code><br/>"
                        f"<b>Arguments:</b> <code>{t['arguments']}</code><br/>"
                        f"<b>Result:</b> <code>{t['result']}</code></div>",
                        unsafe_allow_html=True
                    )

        # Display Metadata badge
        if "meta" in msg:
            meta = msg["meta"]
            st.caption(
                f"⚡ Provider: **{meta.get('provider')}** | "
                f"Latency: **{meta.get('latency')} ms** | "
                f"Cached: **{'Yes' if meta.get('cached') else 'No'}**"
            )

# User input
if user_prompt := st.chat_input("Ask a question, request a calculation, or query knowledge..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Generating response with RAG & resilience engine..."):
            payload = {
                "message": user_prompt,
                "enable_rag": enable_rag,
                "enable_tools": enable_tools,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "provider": provider,
                "use_cache": use_cache
            }
            try:
                resp = requests.post(f"{API_URL}/api/chat", json=payload, timeout=120)
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data.get("answer", "")
                    citations = data.get("citations", [])
                    tools_used = data.get("tools_used", [])
                    meta_info = {
                        "provider": data.get("provider_used"),
                        "latency": data.get("latency_ms"),
                        "cached": data.get("cached")
                    }

                    st.markdown(answer)

                    if citations:
                        with st.expander("📚 Source Citations & References", expanded=True):
                            for c in citations:
                                st.markdown(
                                    f"<div class='citation-box'><b>Source:</b> {c['document_id']} (Score: {c.get('score', 'N/A')})<br/>"
                                    f"<i>\"{c['content_snippet']}\"</i></div>",
                                    unsafe_allow_html=True
                                )

                    if tools_used:
                        with st.expander("🛠️ Tools Executed", expanded=True):
                            for t in tools_used:
                                st.markdown(
                                    f"<div class='tool-box'><b>Tool:</b> <code>{t['tool_name']}</code><br/>"
                                    f"<b>Arguments:</b> <code>{t['arguments']}</code><br/>"
                                    f"<b>Result:</b> <code>{t['result']}</code></div>",
                                    unsafe_allow_html=True
                                )

                    st.caption(
                        f"⚡ Provider: **{meta_info['provider']}** | "
                        f"Latency: **{meta_info['latency']} ms** | "
                        f"Cached: **{'Yes' if meta_info['cached'] else 'No'}**"
                    )

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations,
                        "tools_used": tools_used,
                        "meta": meta_info
                    })
                elif resp.status_code == 429:
                    st.error("⚠️ Rate Limit Exceeded (429). Please wait a moment before sending another request.")
                else:
                    st.error(f"Error ({resp.status_code}): {resp.text}")
            except Exception as e:
                st.error(f"Connection Error: Could not reach backend API at {API_URL}. Details: {e}")
