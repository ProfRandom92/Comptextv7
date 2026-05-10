"""Immutable synthetic golden corpus definitions for industrial replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

GOLDEN_ROOT = Path("datasets/golden")


def _record(stream: str, seq: int, ts: str, severity: str, source: str, code: str, message: str, *, anchor: str = "", values: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "event_id": f"{stream}-{seq:04d}",
        "timestamp": ts,
        "severity": severity,
        "source": source,
        "code": code,
        "message": message,
        "anomaly_anchor": anchor,
        "values": values or {},
    }


def corpus_records() -> dict[str, list[dict[str, object]]]:
    return {
        "can_bus_reference.jsonl": [
            _record("CAN", 1, "2026-01-01T00:00:00Z", "INFO", "PTCAN", "0x18FEF100", "normal engine speed frame", values={"rpm": 1200}),
            _record("CAN", 2, "2026-01-01T00:00:01Z", "INFO", "PTCAN", "0x18FEF100", "normal engine speed frame", values={"rpm": 1201}),
            _record("CAN", 3, "2026-01-01T00:00:02Z", "WARN", "ABS", "C0035", "wheel speed intermittent drop", anchor="ANOM-CAN-WHEEL-0001", values={"wheel_speed_kph": 0}),
            _record("CAN", 4, "2026-01-01T00:00:03Z", "INFO", "PTCAN", "0x18FEF100", "normal engine speed frame", values={"rpm": 1200}),
        ],
        "scada_reference.jsonl": [
            _record("SCADA", 1, "2026-01-01T01:00:00Z", "INFO", "PLC-7", "PUMP-RUN", "pump running steady", values={"pressure_bar": 4.2}),
            _record("SCADA", 2, "2026-01-01T01:00:01Z", "INFO", "PLC-7", "PUMP-RUN", "pump running steady", values={"pressure_bar": 4.2}),
            _record("SCADA", 3, "2026-01-01T01:00:02Z", "CRITICAL", "PLC-7", "VALVE-STUCK", "feed valve stuck open alarm", anchor="ANOM-SCADA-VALVE-0001", values={"position_pct": 100}),
            _record("SCADA", 4, "2026-01-01T01:00:03Z", "WARN", "PLC-7", "PRESSURE-HIGH", "pressure high after valve alarm", anchor="ANOM-SCADA-PRESS-0002", values={"pressure_bar": 8.9}),
        ],
        "sparse_alarm_reference.jsonl": [
            _record("SPARSE", 1, "2026-01-01T02:00:00Z", "INFO", "MCM", "BOOT", "controller startup complete", values={"voltage_v": 24.1}),
            _record("SPARSE", 2, "2026-01-01T02:00:03Z", "ERROR", "EBS", "EBS-ALARM", "single sparse brake pressure alarm", anchor="ANOM-SPARSE-BRAKE-0001", values={"pressure_bar": 0.8}),
            _record("SPARSE", 3, "2026-01-01T02:00:08Z", "INFO", "MCM", "HEARTBEAT", "normal heartbeat restored", values={"voltage_v": 24.0}),
        ],
        "mixed_incident_reference.jsonl": [
            _record("MIXED", 1, "2026-01-01T03:00:00Z", "INFO", "CELL-A", "CYCLE", "normal station cycle", values={"cycle_s": 42}),
            _record("MIXED", 2, "2026-01-01T03:00:01Z", "WARN", "CELL-A", "TORQUE-LIMIT", "torque trend warning before stop", anchor="ANOM-MIX-TORQUE-0001", values={"torque_nm": 31}),
            _record("MIXED", 3, "2026-01-01T03:00:02Z", "ERROR", "CELL-A", "ROBOT-STOP", "robot stopped after torque warning", anchor="ANOM-MIX-STOP-0002", values={"stop_code": 17}),
            _record("MIXED", 4, "2026-01-01T03:00:03Z", "INFO", "CELL-A", "CYCLE", "normal station cycle held for review", values={"cycle_s": 43}),
        ],
    }


def write_golden_corpus(root: Path = GOLDEN_ROOT) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for filename, records in corpus_records().items():
        path = root / filename
        lines = [json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for record in records]
        content = "\n".join(lines) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"golden corpus mutation detected: {path}")
        path.write_text(content, encoding="utf-8")
        hashes[filename] = hashlib.sha256(content.encode()).hexdigest()
    return hashes


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def records_to_log(records: Iterable[dict[str, object]]) -> str:
    rows = []
    for record in records:
        values = " ".join(f"{key}={value}" for key, value in sorted(dict(record.get("values", {})).items()))
        anchor = f" anchor={record['anomaly_anchor']}" if record.get("anomaly_anchor") else ""
        rows.append(f"{record['timestamp']} {record['severity']} source={record['source']} {record['code']} event_id={record['event_id']}{anchor} {record['message']} {values}".strip())
    return "\n".join(rows)
