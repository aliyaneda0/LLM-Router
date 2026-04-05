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


st.set_page_config(page_title="LLM Router", layout="wide")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top, rgba(16, 185, 129, 0.12), transparent 30%),
                linear-gradient(180deg, #f7f8fa 0%, #eef2f7 100%);
        }
        .block-container {
            max-width: 1100px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 24px;
            padding: 1.4rem 1.5rem;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.25rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
            color: #0f172a;
        }
        .hero p {
            margin: 0.45rem 0 0;
            color: #475569;
            font-size: 0.98rem;
        }
        .chat-shell {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 24px;
            padding: 1.2rem;
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
        }
        .bubble {
            border-radius: 20px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.9rem;
            border: 1px solid rgba(148, 163, 184, 0.18);
        }
        .bubble-user {
            background: #ecfeff;
        }
        .bubble-assistant {
            background: #ffffff;
        }
        .bubble-label {
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #64748b;
            margin-bottom: 0.45rem;
            font-weight: 600;
        }
        .bubble-text {
            color: #0f172a;
            line-height: 1.65;
            white-space: pre-wrap;
        }
        .meta-strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 1rem 0 0.5rem;
        }
        .meta-card {
            background: #f8fafc;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            padding: 0.85rem;
        }
        .meta-label {
            color: #64748b;
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }
        .meta-value {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 600;
        }
        .dashboard-title {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .dashboard-copy {
            color: #64748b;
            font-size: 0.92rem;
            margin-bottom: 1rem;
        }
        .stTextArea textarea {
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.32);
            background: #ffffff;
        }
        .stButton button {
            border-radius: 999px;
            background: #0f172a;
            color: white;
            border: none;
            padding: 0.65rem 1.2rem;
            font-weight: 600;
        }
        .stButton button:hover {
            background: #111827;
            color: white;
        }
        @media (max-width: 900px) {
            .meta-strip {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>LLM Router</h1>
            <p>Enter a prompt, get the routed model output, and open the dashboard only when you need the metadata.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_result(result: dict[str, object]) -> None:
    prompt = html.escape(str(result["prompt"]))
    response = html.escape(str(result["response"]))
    confidence = float(result["confidence"])
    latency_ms = float(result["latency_ms"])
    estimated_cost = float(result["estimated_cost"])
    predicted_class = html.escape(str(result["predicted_class"]))
    model_used = html.escape(str(result["model_used"]))

    st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="bubble bubble-user">
            <div class="bubble-label">Prompt</div>
            <div class="bubble-text">{prompt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="bubble bubble-assistant">
            <div class="bubble-label">Output</div>
            <div class="bubble-text">{response}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="meta-strip">
            <div class="meta-card">
                <div class="meta-label">Predicted Class</div>
                <div class="meta-value">{predicted_class}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Confidence</div>
                <div class="meta-value">{confidence:.2%}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Model Used</div>
                <div class="meta-value">{model_used}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Latency</div>
                <div class="meta-value">{latency_ms:.2f} ms</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        f"Reason: {result['route_reason']} | Fallback: {'Yes' if result['fallback_applied'] else 'No'} | Estimated cost: ${estimated_cost:.6f}"
    )
    with st.expander("Prompt metadata", expanded=False):
        prob_df = pd.DataFrame(
            {
                "class": list(result["class_probabilities"].keys()),
                "probability": list(result["class_probabilities"].values()),
            }
        )
        st.dataframe(prob_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard(logs: list[dict[str, object]], summary: dict[str, object]) -> None:
    with st.expander("Dashboard", expanded=False):
        st.markdown('<div class="dashboard-title">Routing analytics</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="dashboard-copy">A clean summary of recent prompt traffic and metadata for each routed request.</div>',
            unsafe_allow_html=True,
        )

        if not logs:
            st.info("No routing data yet. Submit a prompt to populate the dashboard.")
            return

        df = pd.DataFrame(logs)
        metric_cols = st.columns(4)
        metric_cols[0].metric("Total Routes", summary["total_routes"])
        metric_cols[1].metric("Avg Latency (ms)", summary["average_latency_ms"])
        metric_cols[2].metric("Estimated Cost", f"${summary['total_estimated_cost']}")
        metric_cols[3].metric("Fallback Routes", summary["fallback_routes"])

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader("Routes by Predicted Class")
            st.bar_chart(df["predicted_class"].value_counts())
        with chart_col2:
            st.subheader("Routes by Model")
            st.bar_chart(df["model_used"].value_counts())

        st.subheader("Recent Prompt Metadata")
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
                    "response",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


def submit_prompt(prompt: str) -> dict[str, object]:
    result = route_prompt(prompt)
    record = {
        "prompt": prompt,
        "predicted_class": result["predicted_class"],
        "confidence": result["confidence"],
        "model_used": result["model_used"],
        "fallback_applied": result["fallback_applied"],
        "route_reason": result["route_reason"],
        "latency_ms": result["latency_ms"],
        "estimated_cost": result["estimated_cost"],
        "response": result["response"],
        "class_probabilities": result["class_probabilities"],
    }
    insert_route_log(record)
    return record


init_db()
inject_styles()
render_header()

if "last_result" not in st.session_state:
    st.session_state.last_result = None

with st.form("prompt_form", clear_on_submit=False):
    prompt_input = st.text_area(
        "Message",
        placeholder="Ask anything. The router will classify the prompt, choose a model, and return the response here.",
        height=140,
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Send")

if submitted:
    clean_prompt = prompt_input.strip()
    if not clean_prompt:
        st.warning("Enter a prompt before sending.")
    else:
        with st.spinner("Routing prompt and generating response..."):
            st.session_state.last_result = submit_prompt(clean_prompt)

if st.session_state.last_result:
    render_chat_result(st.session_state.last_result)
else:
    st.info("Your latest routed response will appear here.")

recent_logs = fetch_recent_logs(limit=200)
summary = fetch_summary()
render_dashboard(recent_logs, summary)
