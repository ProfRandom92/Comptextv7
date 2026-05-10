"""Deterministic industrial replay datasets for CompText validation."""

from __future__ import annotations


def can_bus_telemetry(frames: int = 240) -> str:
    rows = []
    for idx in range(frames):
        anomaly = idx in {47, 119, 181}
        rows.append(
            "2026-05-10T08:{minute:02d}:{second:02d}Z {severity} CAN id=0x{can_id:X} "
            "rpm={rpm} voltage={voltage}V temp={temp}C torque={torque}Nm {marker}".format(
                minute=(idx // 60) % 60,
                second=idx % 60,
                severity="ERROR" if anomaly else "INFO",
                can_id=0x180 + (idx % 8),
                rpm=1420 + (idx % 12),
                voltage=24.0 if not anomaly else 18.6,
                temp=82 + (idx % 4) if not anomaly else 117,
                torque=410 + (idx % 5),
                marker="alarm undervoltage overheat" if anomaly else "normal_operation",
            )
        )
    return "\n".join(rows)


def manufacturing_logs(lines: int = 210) -> str:
    cells = ("body", "paint", "battery", "final")
    rows = []
    for idx in range(lines):
        defect = idx in {55, 56, 144}
        rows.append(
            "2026-05-10T09:{minute:02d}:{second:02d}Z {severity} source={cell} station=S{station:02d} "
            "DTC:{code} cycle={cycle} pressure={pressure}kPa torque={torque}Nm {marker}".format(
                minute=(idx // 60) % 60,
                second=idx % 60,
                severity="WARN" if defect else "INFO",
                cell=cells[idx % len(cells)],
                station=idx % 12,
                code="SEAL-LEAK" if defect else "OK",
                cycle=idx,
                pressure=220 if not defect else 148,
                torque=42 + (idx % 3),
                marker="anomaly causal_chain seal_loss" if defect else "normal_operation",
            )
        )
    return "\n".join(rows)


def scada_event_stream(lines: int = 260) -> str:
    rows = []
    for idx in range(lines):
        trip = idx in {88, 89, 90, 177}
        rows.append(
            "2026-05-10T10:{minute:02d}:{second:02d}Z {severity} source=SCADA SPN 700 FMI {fmi} "
            "pump=P{pump} flow={flow}L pressure={pressure}bar latency={latency}ms {marker}".format(
                minute=(idx // 60) % 60,
                second=idx % 60,
                severity="CRITICAL" if trip else "INFO",
                fmi=31 if trip else 0,
                pump=idx % 5,
                flow=510 if not trip else 130,
                pressure=7.2 if not trip else 2.1,
                latency=14 if not trip else 990,
                marker="emergency_trip alarm_burst caused_by pressure_drop" if trip else "steady_state",
            )
        )
    return "\n".join(rows)


def alarm_bursts(lines: int = 180) -> str:
    rows = []
    for idx in range(lines):
        burst = 70 <= idx <= 78
        rows.append(
            "2026-05-10T11:{minute:02d}:{second:02d}Z {severity} ECU=ALARM P1B23 "
            "alarm_id=A{alarm} severity_anchor={anchor} voltage={voltage}V temp={temp}C {marker}".format(
                minute=(idx // 60) % 60,
                second=idx % 60,
                severity="ERROR" if burst else "INFO",
                alarm=idx % 3,
                anchor="HIGH" if burst else "LOW",
                voltage=18.2 if burst else 24.1,
                temp=121 if burst else 84,
                marker="sparse anomaly event safety-critical" if burst else "normal repeated frame",
            )
        )
    return "\n".join(rows)


def industrial_replay_cases() -> tuple[tuple[str, str], ...]:
    return (
        ("can_bus_telemetry", can_bus_telemetry()),
        ("manufacturing_logs", manufacturing_logs()),
        ("scada_event_stream", scada_event_stream()),
        ("alarm_bursts", alarm_bursts()),
    )
