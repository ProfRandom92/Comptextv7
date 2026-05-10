"""Privacy-by-design intake agent for local DSGVO sanitation."""

import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SanitizedLog:
    """Sanitized log text and privacy metadata."""

    text: str
    replacements: dict[str, str]


class IntakeAgent:
    """Masks vehicle identifiers before cloud or model inference."""

    fin_regex = re.compile(r"\b(?:FIN|VIN)[_-]?[A-HJ-NPR-Z0-9]{6,17}\b", re.IGNORECASE)

    def sanitize(self, raw_log: str) -> SanitizedLog:
        """Replace FIN/VIN-like identifiers with stable SHA-256 pseudonyms."""
        replacements: dict[str, str] = {}

        def replace(match: re.Match[str]) -> str:
            value = match.group(0)
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
            pseudonym = f"FIN_HASH_{digest}"
            replacements[value] = pseudonym
            return pseudonym

        return SanitizedLog(text=self.fin_regex.sub(replace, raw_log), replacements=replacements)
