"""Stdlib industrial validation dashboard for CompText V7."""

from __future__ import annotations

import argparse
import csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_kvtc_v7_benchmarks import run_benchmarks
from src.validation.forensic import run_forensic_audit
from src.validation.replay import replay_summary, run_replay
from src.validation.token_telemetry import drift_fingerprint, tokenizer_version


def dashboard_data() -> dict[str, object]:
    benchmarks = [result.as_dict() for result in run_benchmarks(iterations=1, warmups=0)]
    forensic = [result.as_dict() for result in run_forensic_audit()]
    replay = replay_summary(run_replay(passes=2))
    return {
        "audit_summary": {
            "forensic_failures": sum(0 if row["passed"] else 1 for row in forensic),
            "replay_determinism": replay["stable"],
            "tokenizer_version": tokenizer_version(),
            "tokenizer_drift_fingerprint": drift_fingerprint(),
        },
        "benchmarks": benchmarks,
        "forensic": forensic,
        "replay": replay,
        "drift_severity_timeline": [
            {"dataset": row["dataset"], "critical": sum(1 for f in row["findings"] if f["severity"] == "CRITICAL"), "high": sum(1 for f in row["findings"] if f["severity"] == "HIGH")}
            for row in forensic
        ],
    }


def csv_export(data: dict[str, object]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["case", "compression_ratio", "token_savings", "semantic_retention", "anomaly_survivability", "sparse_envelope", "forensic_failures", "replay_determinism", "compressed_hash"])
    writer.writeheader()
    forensic_by_name = {row["dataset"]: row for row in data["forensic"]}  # type: ignore[index]
    for row in data["benchmarks"]:  # type: ignore[index]
        writer.writerow({
            "case": row["name"],
            "compression_ratio": row["compression_ratio"],
            "token_savings": row["reduction_percent"],
            "semantic_retention": "see_forensic",
            "anomaly_survivability": "see_forensic",
            "sparse_envelope": row["name"] == "short_sparse_3",
            "forensic_failures": data["audit_summary"]["forensic_failures"],  # type: ignore[index]
            "replay_determinism": data["audit_summary"]["replay_determinism"],  # type: ignore[index]
            "compressed_hash": "benchmark-runtime",
        })
    for name, row in forensic_by_name.items():
        writer.writerow({
            "case": name,
            "semantic_retention": row["semantic_retention"],
            "anomaly_survivability": row["anomaly_survivability"],
            "forensic_failures": 0 if row["passed"] else 1,
            "replay_determinism": data["audit_summary"]["replay_determinism"],  # type: ignore[index]
            "compressed_hash": row["compressed_sha256"],
        })
    return output.getvalue()


def html_page(data: dict[str, object]) -> str:
    return f"""<!doctype html><meta charset='utf-8'><title>CompText V7 Industrial Dashboard</title>
<style>body{{font-family:system-ui;margin:2rem}} .card{{display:inline-block;border:1px solid #999;padding:1rem;margin:.5rem}} table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:.35rem}}</style>
<h1>CompText V7 Industrial Validation Dashboard</h1>
<p><a href='/export.json'>JSON export</a> | <a href='/export.csv'>CSV export</a> | <a href='/replay'>Run replay controls</a></p>
<div class='card'><b>Forensic failures</b><br>{data['audit_summary']['forensic_failures']}</div>
<div class='card'><b>Replay determinism</b><br>{data['audit_summary']['replay_determinism']}</div>
<div class='card'><b>Tokenizer</b><br>{data['audit_summary']['tokenizer_version']}</div>
<div class='card'><b>Deterministic hash</b><br><code>{data['audit_summary']['tokenizer_drift_fingerprint']}</code></div>
<h2>Compression / Token Savings / Sparse Utilization</h2><table><tr><th>case</th><th>ratio</th><th>token savings %</th><th>sparse envelope</th></tr>{''.join(f"<tr><td>{row['name']}</td><td>{row['compression_ratio']}</td><td>{row['reduction_percent']}</td><td>{row['name']=='short_sparse_3'}</td></tr>" for row in data['benchmarks'])}</table>
<h2>Semantic Retention / Anomaly Survivability / Forensic Failures</h2><table><tr><th>dataset</th><th>semantic</th><th>anomaly</th><th>anchor</th><th>safety</th><th>passed</th><th>compressed hash</th></tr>{''.join(f"<tr><td>{row['dataset']}</td><td>{row['semantic_retention']}</td><td>{row['anomaly_survivability']}</td><td>{row['anchor_retention']}</td><td>{row['safety_critical_retention']}</td><td>{row['passed']}</td><td><code>{row['compressed_sha256']}</code></td></tr>" for row in data['forensic'])}</table>
<h2>Drift Severity Timeline</h2><pre>{json.dumps(data['drift_severity_timeline'], indent=2)}</pre>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        data = dashboard_data()
        if self.path == "/export.json" or self.path == "/replay":
            body = json.dumps(data, indent=2, sort_keys=True).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body); return
        if self.path == "/export.csv":
            body = csv_export(data).encode()
            self.send_response(200); self.send_header("Content-Type", "text/csv"); self.end_headers(); self.wfile.write(body); return
        body = html_page(data).encode()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers(); self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        data = dashboard_data()
        Path("reports/dashboard_export.json").write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        Path("reports/dashboard_export.csv").write_text(csv_export(data), encoding="utf-8")
        print(json.dumps(data["audit_summary"], indent=2, sort_keys=True))
        return 0
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
