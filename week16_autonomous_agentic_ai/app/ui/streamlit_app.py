"""Streamlit Interactive Web UI for the Agentic AI Assistant (Week 16)."""

import os
import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Agentic AI Assistant (Week 16)",
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
    .trajectory-step {
        background: #1e293b;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 4px solid #38bdf8;
    }
    .verifier-pass {
        background-color: #064e3b;
        border: 1px solid #059669;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 8px 0;
    }
    .verifier-fail {
        background-color: #7f1d1d;
        border: 1px solid #dc2626;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 8px 0;
    }
    .token-badge {
        display: inline-block;
        background: #334155;
        color: #e2e8f0;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.title("🤖 Agent Configuration")
    
    agent_mode = st.radio(
        "Architecture Mode",
        options=["multi_agent", "single_agent", "fixed_pipeline_w15"],
        format_func=lambda x: {
            "multi_agent": "Multi-Agent (Researcher + Verifier)",
            "single_agent": "Single-Agent ReAct Loop",
            "fixed_pipeline_w15": "W15 Fixed Pipeline (Baseline)"
        }[x],
        index=0,
        help="Switch between autonomous multi-agent coordination, single-agent loop, or fixed baseline"
    )

    provider = st.selectbox(
        "LLM Provider",
        options=["gemini", "openai", "vllm", "mock"],
        index=0
    )

    max_steps = st.slider("Max Agent Steps", min_value=1, max_value=8, value=5)
    enable_compaction = st.checkbox("Enable Context Compaction", value=True, help="Summarize verbose tool outputs to prevent Context Saturation")

    st.divider()
    st.subheader("🧪 Failure Injection Testing")
    failure_mode = st.selectbox(
        "Inject Simulated Failure",
        options=["None", "tool_unavailable", "malformed_output", "timeout"],
        index=0,
        help="Test agentic recovery when tools fail"
    )

    st.divider()
    st.subheader("📄 Knowledge Ingestion")
    uploaded_file = st.file_uploader("Upload Document (.txt, .md)", type=["txt", "md"])
    if uploaded_file is not None and st.button("Index into Vector Store", use_container_width=True):
        with st.spinner("Chunking & embedding..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                res = requests.post(f"{API_URL}/api/rag/upload", files=files, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"Indexed {data['chunks_indexed']} chunks! Total: {data['total_store_count']}")
                else:
                    st.error(f"Failed: {res.text}")
            except Exception as err:
                st.error(f"API Error: {err}")

# ---------------------------------------------------------
# Main Chat Area
# ---------------------------------------------------------
st.title("🤖 Enterprise Agentic Assistant")
st.caption("Week 16: Multi-Step ReAct Loop, Context Compaction, Independent Verifier, and Fault Resilience")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your Agentic AI Assistant. I iteratively plan, call tools across RAG and web search, perform math, and verify facts before responding. How can I help you?"}
    ]

# Render conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Trajectory display
        if "trajectory" in msg and msg["trajectory"]:
            traj = msg["trajectory"]
            with st.expander(f"🔄 Reasoning Trajectory ({traj.get('total_steps', 0)} steps | {traj.get('total_tokens', 0)} tokens)", expanded=False):
                for step in traj.get("steps", []):
                    st.markdown(
                        f"<div class='trajectory-step'>"
                        f"<b>Step {step['step_number']}</b><br/>"
                        f"💭 <i>Thought:</i> {step['thought']}<br/>"
                        f"⚙️ <i>Action:</i> <code>{step['action']['tool_name'] if step.get('action') else 'finish'}</code> "
                        f"<code>{step['action']['arguments'] if step.get('action') else ''}</code><br/>"
                        f"🔍 <i>Compacted Observation:</i> {step.get('compacted_observation') or step.get('observation')}<br/>"
                        f"<span class='token-badge'>⏱️ {step.get('latency_ms', 0)} ms</span>"
                        f"<span class='token-badge'>🪙 {step.get('prompt_tokens', 0)} in / {step.get('completion_tokens', 0)} out</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

        # Verifier critique display
        if "verification" in msg and msg["verification"]:
            v = msg["verification"]
            box_class = "verifier-pass" if v.get("passed") else "verifier-fail"
            icon = "✅" if v.get("passed") else "⚠️"
            with st.expander(f"{icon} Verifier Evaluation (Score: {v.get('score', 0):.2f})", expanded=False):
                st.markdown(
                    f"<div class='{box_class}'>"
                    f"<b>Status:</b> {'PASSED' if v.get('passed') else 'FAILED'}<br/>"
                    f"<b>Critique:</b> {v.get('critique')}<br/>"
                    f"<b>Recommended Action:</b> <code>{v.get('recommended_action')}</code>"
                    f"</div>",
                    unsafe_allow_html=True
                )

# User input prompt
if user_prompt := st.chat_input("Ask a multi-hop or analytical question..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent evaluating and executing trajectory..."):
            try:
                if agent_mode == "fixed_pipeline_w15":
                    # Call fixed W15 endpoint
                    payload = {
                        "message": user_prompt,
                        "enable_rag": True,
                        "enable_tools": True,
                        "provider": provider
                    }
                    resp = requests.post(f"{API_URL}/api/chat", json=payload, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        ans = data.get("answer", "")
                        st.markdown(ans)
                        st.session_state.messages.append({"role": "assistant", "content": ans})
                else:
                    # Call agentic endpoint
                    payload = {
                        "message": user_prompt,
                        "mode": agent_mode,
                        "max_steps": max_steps,
                        "enable_compaction": enable_compaction,
                        "provider": provider,
                        "failure_injection": None if failure_mode == "None" else failure_mode
                    }
                    resp = requests.post(f"{API_URL}/api/agent/chat", json=payload, timeout=45)
                    if resp.status_code == 200:
                        data = resp.json()
                        ans = data.get("answer", "")
                        traj = data.get("trajectory", {})
                        verif = data.get("verification")
                        
                        st.markdown(ans)

                        # Render Trajectory
                        with st.expander(f"🔄 Reasoning Trajectory ({traj.get('total_steps', 0)} steps | {traj.get('total_tokens', 0)} tokens | ${traj.get('estimated_cost_usd', 0):.6f})", expanded=True):
                            for step in traj.get("steps", []):
                                st.markdown(
                                    f"<div class='trajectory-step'>"
                                    f"<b>Step {step['step_number']}</b><br/>"
                                    f"💭 <i>Thought:</i> {step['thought']}<br/>"
                                    f"⚙️ <i>Action:</i> <code>{step['action']['tool_name'] if step.get('action') else 'finish'}</code> "
                                    f"<code>{step['action']['arguments'] if step.get('action') else ''}</code><br/>"
                                    f"🔍 <i>Compacted Observation:</i> {step.get('compacted_observation') or step.get('observation')}<br/>"
                                    f"<span class='token-badge'>⏱️ {step.get('latency_ms', 0)} ms</span>"
                                    f"<span class='token-badge'>🪙 {step.get('prompt_tokens', 0)} in / {step.get('completion_tokens', 0)} out</span>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )

                        # Render Verification
                        if verif:
                            box_class = "verifier-pass" if verif.get("passed") else "verifier-fail"
                            with st.expander("🛡️ Independent Verifier Critique", expanded=True):
                                st.markdown(
                                    f"<div class='{box_class}'>"
                                    f"<b>Status:</b> {'PASSED' if verif.get('passed') else 'FAILED'}<br/>"
                                    f"<b>Critique:</b> {verif.get('critique')}<br/>"
                                    f"<b>Recommended Action:</b> <code>{verif.get('recommended_action')}</code>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": ans,
                            "trajectory": traj,
                            "verification": verif
                        })
                    else:
                        st.error(f"Error ({resp.status_code}): {resp.text}")
            except Exception as e:
                st.error(f"Connection error to {API_URL}: {e}")
