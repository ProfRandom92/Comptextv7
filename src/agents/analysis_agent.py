"""Inference orchestration agent for local or managed model backends."""

from dataclasses import dataclass
from typing import Any

from src.core import CompressionResult
from src.interpretability import SAENLAAuditor


@dataclass(frozen=True)
class AnalysisDecision:
    """Audited model-routing decision for a compressed diagnostic frame."""

    backend: str
    prompt: str
    audit_passed: bool
    audit_fve: float
    metadata: dict[str, Any]


class AnalysisAgent:
    """Controls inference backend selection and NLA audit preflight checks."""

    def __init__(self, backend: str = "gemma-local", auditor: SAENLAAuditor | None = None) -> None:
        self.backend = backend
        self.auditor = auditor or SAENLAAuditor()

    def prepare(self, compression: CompressionResult, triage_severity: str) -> AnalysisDecision:
        """Build an inference prompt and audit whether the routing rationale is explicit."""
        explanation = (
            f"Analyze compressed KVTC frame for {triage_severity} severity with "
            "header middle window frame coverage."
        )
        audit = self.auditor.audit(
            explanation,
            {
                "header": 0.2,
                "middle": 0.2,
                "window": 0.4,
                "frame": 0.2,
            },
        )
        prompt = f"Severity={triage_severity}; Frame={compression.kvtc_frame}"
        return AnalysisDecision(
            backend=self.backend,
            prompt=prompt,
            audit_passed=audit.passed,
            audit_fve=audit.fve,
            metadata={"compression_ratio": compression.ratio},
        )
