from __future__ import annotations

import html
from pathlib import Path
import site
import sys

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

import pandas as pd
import streamlit as st

from backend.db import fetch_recent_logs, fetch_summary, init_db, insert_route_log
from backend.router import route_prompt


BASE_DIR = Path(__file__).resolve().parent.parent


st.set_page_config(
    page_title="LLM Router",
    page_icon=":speech_balloon:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(34, 197, 94, 0.14), transparent 28%),
                radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 24%),
                linear-gradient(180deg, #0b1020 0%, #0f172a 100%);
            color: #e5eefc;
        }

        [data-testid="stAppViewContainer"] {
            background: transparent;
        }

        [data-testid="stHeader"] {
            background: rgba(11, 16, 32, 0.88);
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(9, 14, 28, 0.98) 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.12);
        }

        [data-testid="stSidebar"] * {
            color: #dbe7ff;
        }

        .block-container {
            max-width: 1120px;
            padding-top: 1.6rem;
            padding-bottom: 2rem;
        }

        .app-shell {
            max-width: 920px;
            margin: 0 auto;
        }

        .hero {
            padding: 0.35rem 0 1rem;
        }

        .hero-title {
            color: #f8fbff;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 0.35rem;
        }

        .hero-copy {
            color: #98a7c3;
            font-size: 1rem;
            line-height: 1.6;
            max-width: 760px;
        }

        .chat-wrap {
            background: rgba(15, 23, 42, 0.68);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 26px;
            padding: 1rem;
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
            backdrop-filter: blur(18px);
        }

        .empty-state {
            padding: 1.1rem 1.15rem;
            border-radius: 18px;
            background: rgba(30, 41, 59, 0.62);
            border: 1px dashed rgba(148, 163, 184, 0.22);
            color: #b8c5dd;
            margin-bottom: 0.75rem;
        }

        .chat-meta {
            margin-top: 0.9rem;
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.7rem;
        }

        .chat-meta-card {
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 16px;
            padding: 0.8rem 0.9rem;
        }

        .chat-meta-label {
            color: #8ea0bf;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.3rem;
        }

        .chat-meta-value {
            color: #f8fbff;
            font-size: 0.98rem;
            font-weight: 600;
            line-height: 1.35;
        }

        .chat-caption {
            color: #9fb0cd;
            font-size: 0.88rem;
            margin-top: 0.8rem;
            line-height: 1.6;
        }

        .composer-shell {
            position: sticky;
            bottom: 0.75rem;
            margin-top: 1rem;
            padding: 0.85rem;
            border-radius: 24px;
            background: rgba(9, 14, 28, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.16);
            box-shadow: 0 18px 60px rgba(0, 0, 0, 0.26);
            backdrop-filter: blur(18px);
        }

        .sidebar-block {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.12);
            border-radius: 18px;
            padding: 0.95rem;
            margin-bottom: 1rem;
        }

        .sidebar-title {
            font-size: 1rem;
            font-weight: 700;
            color: #f8fbff;
            margin-bottom: 0.3rem;
        }

        .sidebar-copy {
            color: #9fb0cd;
            font-size: 0.9rem;
            line-height: 1.5;
        }

        .stChatMessage {
            background: transparent;
        }

        .stChatMessage [data-testid="stMarkdownContainer"] p {
            color: #e8eefb;
            line-height: 1.7;
        }

        .stChatInputContainer,
        .stChatFloatingInputContainer {
            background: transparent !important;
        }

        .stTextArea textarea {
            background: rgba(15, 23, 42, 0.96) !important;
            color: #edf4ff !important;
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            border-radius: 18px !important;
            min-height: 118px !important;
            padding-top: 0.95rem !important;
            padding-bottom: 0.95rem !important;
        }

        .stTextArea textarea::placeholder {
            color: #7f92b2 !important;
        }

        .stButton button {
            width: 100%;
            min-height: 52px;
            border-radius: 16px;
            border: 1px solid rgba(96, 165, 250, 0.3);
            background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%);
            color: #eff6ff;
            font-weight: 700;
            font-size: 0.98rem;
            box-shadow: 0 14px 30px rgba(29, 78, 216, 0.22);
        }

        .stButton button:hover {
            color: #ffffff;
            border-color: rgba(125, 211, 252, 0.55);
            background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
        }

        .stMetric {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(148, 163, 184, 0.12);
            border-radius: 16px;
            padding: 0.8rem;
        }

        .stMetric label, .stMetric div {
            color: #dbe7ff !important;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid rgba(148, 163, 184, 0.12);
            border-radius: 14px;
            overflow: hidden;
        }

        @media (max-width: 900px) {
            .chat-meta {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .hero-title {
                font-size: 1.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(logs: list[dict[str, object]], summary: dict[str, object]) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-block">
                <div class="sidebar-title">Dashboard</div>
                <div class="sidebar-copy">Expand this left panel whenever you want routing analytics, recent prompts, and metadata history.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not logs:
            st.info("No routed prompts yet. Send one from the main chat to populate the dashboard.")
            return

        top_cols = st.columns(2)
        top_cols[0].metric("Routes", summary["total_routes"])
        top_cols[1].metric("Fallbacks", summary["fallback_routes"])

        bottom_cols = st.columns(2)
        bottom_cols[0].metric("Avg ms", summary["average_latency_ms"])
        bottom_cols[1].metric("Cost", f"${summary['total_estimated_cost']}")

        df = pd.DataFrame(logs)

        with st.expander("Routes by class", expanded=True):
            st.bar_chart(df["predicted_class"].value_counts())

        with st.expander("Models used", expanded=False):
            st.bar_chart(df["model_used"].value_counts())

        with st.expander("Recent prompt metadata", expanded=False):
            st.dataframe(
                df[
                    [
                        "created_at",
                        "predicted_class",
                        "confidence",
                        "model_used",
                        "fallback_applied",
                        "route_reason",
                        "latency_ms",
                        "estimated_cost",
                        "prompt",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )


def record_prompt(prompt: str) -> dict[str, object]:
    result = route_prompt(prompt)
    record = {
        "prompt": prompt,
        "predicted_class": result["predicted_class"],
        "confidence": result["confidence"],
        "class_probabilities": result["class_probabilities"],
        "model_used": result["model_used"],
        "fallback_applied": result["fallback_applied"],
        "route_reason": result["route_reason"],
        "latency_ms": result["latency_ms"],
        "estimated_cost": result["estimated_cost"],
        "response": result["response"],
    }
    insert_route_log(record)
    return record


def render_history() -> None:
    if not st.session_state.messages:
        st.markdown(
            '<div class="empty-state">Your responses will appear here in a chat-style view. The input box stays below, just like a normal assistant interface.</div>',
            unsafe_allow_html=True,
        )
        return

    for item in st.session_state.messages:
        with st.chat_message("user"):
            st.markdown(html.escape(item["prompt"]))

        with st.chat_message("assistant"):
            st.markdown(html.escape(item["response"]))
            st.markdown(
                f"""
                <div class="chat-meta">
                    <div class="chat-meta-card">
                        <div class="chat-meta-label">Class</div>
                        <div class="chat-meta-value">{html.escape(str(item["predicted_class"]))}</div>
                    </div>
                    <div class="chat-meta-card">
                        <div class="chat-meta-label">Confidence</div>
                        <div class="chat-meta-value">{float(item["confidence"]):.2%}</div>
                    </div>
                    <div class="chat-meta-card">
                        <div class="chat-meta-label">Model</div>
                        <div class="chat-meta-value">{html.escape(str(item["model_used"]))}</div>
                    </div>
                    <div class="chat-meta-card">
                        <div class="chat-meta-label">Latency</div>
                        <div class="chat-meta-value">{float(item["latency_ms"]):.2f} ms</div>
                    </div>
                </div>
                <div class="chat-caption">
                    Reason: {html.escape(str(item["route_reason"]))}<br/>
                    Fallback: {"Yes" if item["fallback_applied"] else "No"}<br/>
                    Estimated cost: ${float(item["estimated_cost"]):.6f}
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Prompt metadata", expanded=False):
                probability_df = pd.DataFrame(
                    {
                        "class": list(item["class_probabilities"].keys()),
                        "probability": list(item["class_probabilities"].values()),
                    }
                )
                st.dataframe(probability_df, use_container_width=True, hide_index=True)


def handle_submit(prompt_text: str) -> None:
    prompt = prompt_text.strip()
    if not prompt:
        st.warning("Enter a prompt before sending.")
        return

    with st.spinner("Routing prompt and generating response..."):
        record = record_prompt(prompt)
    st.session_state.messages.append(record)


init_db()
inject_styles()

if "messages" not in st.session_state:
    st.session_state.messages = []

recent_logs = fetch_recent_logs(limit=200)
summary = fetch_summary()
render_sidebar(recent_logs, summary)

st.markdown('<div class="app-shell">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero">
        <div class="hero-title">LLM Router</div>
        <div class="hero-copy">Readable dark-mode chat, routed model output above the composer, and a left dashboard panel that can be expanded or collapsed whenever you need it.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
render_history()
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="composer-shell">', unsafe_allow_html=True)
with st.form("prompt_form", clear_on_submit=True):
    prompt_text = st.text_area(
        "Message",
        placeholder="Type your prompt here...",
        label_visibility="collapsed",
    )
    _, button_col = st.columns([4.6, 1.2])
    with button_col:
        submitted = st.form_submit_button("Send")

if submitted:
    handle_submit(prompt_text)
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
