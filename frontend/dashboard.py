from __future__ import annotations

from pathlib import Path
import site
import sys

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

import pandas as pd
import streamlit as st

from backend.db import fetch_recent_logs, fetch_summary, init_db


BASE_DIR = Path(__file__).resolve().parent.parent


st.set_page_config(page_title="LLM Router Dashboard", layout="wide")
st.title("LLM Router Dashboard")
st.caption("Week 1 MVP analytics for routing decisions.")

init_db()
logs = fetch_recent_logs(limit=200)

if not logs:
    st.info("No routing data yet. Call the API first, then refresh this page.")
else:
    df = pd.DataFrame(logs)
    summary = fetch_summary()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Routes", summary["total_routes"])
    col2.metric("Avg Latency (ms)", summary["average_latency_ms"])
    col3.metric("Estimated Cost", f"${summary['total_estimated_cost']}")

    st.metric("Fallback Routes", summary["fallback_routes"])

    st.subheader("Routes by Predicted Class")
    st.bar_chart(df["predicted_class"].value_counts())

    st.subheader("Routes by Model")
    st.bar_chart(df["model_used"].value_counts())

    st.subheader("Recent Logs")
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
    )
