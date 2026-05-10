"""Local-only Streamlit dashboard for industrial validation reports.

Run with:
    streamlit run dashboard/industrial_validation_dashboard.py
"""

from __future__ import annotations

import csv
import io
import json

try:
    import streamlit as st
except ModuleNotFoundError as exc:  # pragma: no cover - exercised only without dashboard extras.
    raise SystemExit("Install streamlit to run the local dashboard: python -m pip install streamlit") from exc

from src.validation.validation_harness import ValidationHarness


st.set_page_config(page_title="CompTextV7 Industrial Validation", layout="wide")
st.title("CompTextV7 Industrial Validation Dashboard")
st.caption("Local-only deterministic replay; no cloud dependency.")

encoding = st.selectbox("Tokenizer encoding", ("cl100k_base", "o200k_base"), index=0)
seed = st.number_input("Deterministic seed", value=1701, step=1)

harness = ValidationHarness(seed=int(seed), encoding_name=encoding)
results = harness.replay()
rows = [result.as_dict() for result in results]

avg_token_savings = sum(row["token_reduction_percent"] for row in rows) / len(rows)
avg_semantic = sum(row["semantic_retention_score"] for row in rows) / len(rows)
avg_anomaly = sum(row["anomaly_survivability"] for row in rows) / len(rows)
sparse_count = sum(1 for row in rows if row["sparse_review_payload"])
failure_count = sum(1 for row in rows if row["information_loss_severity"] in {"HIGH", "CRITICAL"})

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Token savings", f"{avg_token_savings:.1f}%")
c2.metric("Semantic retention", f"{avg_semantic:.2f}")
c3.metric("Anomaly survivability", f"{avg_anomaly:.2f}")
c4.metric("Sparse envelopes", sparse_count)
c5.metric("Audit failures", failure_count)

st.subheader("Benchmark history / regression tracking")
st.dataframe(rows, use_container_width=True)

json_payload = json.dumps(rows, indent=2, sort_keys=True)
csv_buffer = io.StringIO()
writer = csv.DictWriter(csv_buffer, fieldnames=list(rows[0]))
writer.writeheader()
writer.writerows(rows)

st.download_button("Export JSON report", json_payload, file_name="comptext_validation.json", mime="application/json")
st.download_button("Export CSV report", csv_buffer.getvalue(), file_name="comptext_validation.csv", mime="text/csv")

st.subheader("Audit summary")
for row in rows:
    st.write(f"**{row['case_name']}** — severity={row['information_loss_severity']} — {row['audit_log']}")
