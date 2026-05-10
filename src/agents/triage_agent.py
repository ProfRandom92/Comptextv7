"""OBD-focused triage agent for prioritizing diagnostic events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TriageResult:
    """Classification result for a diagnostic code set."""

    severity: str
    codes: list[str]
    rationale: str


class TriageAgent:
    """Classifies OBD codes into deterministic severity buckets."""

    critical_prefixes = ("P0", "B1")

    def classify(self, obd_codes: list[str]) -> TriageResult:
        """Return a deterministic severity assessment for OBD codes."""
        normalized = [code.upper() for code in obd_codes]
        critical = [code for code in normalized if code.startswith(self.critical_prefixes)]
        if critical:
            return TriageResult(
                severity="P1",
                codes=normalized,
                rationale=f"Critical drivetrain/body fault candidates: {', '.join(critical)}",
            )
        if normalized:
            return TriageResult(
                severity="P2",
                codes=normalized,
                rationale="Diagnostic codes present but no critical prefix matched.",
            )
        return TriageResult(severity="P3", codes=[], rationale="No OBD code supplied.")
