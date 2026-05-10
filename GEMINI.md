# CompText V7 (Cognitive Fabric) Project Memory

## Mission
Build an industrial CompText V7 repository for high-efficiency technical-log compression and auditable AI assistance in Daimler Trucks / Industry 4.0 contexts.

## Architectural Pillars
- **Core:** KVTC-V7 hierarchical token reduction with a 4-layer sandwich: Header, Middle, Window, Frame.
- **Interpretability:** SAE-NLA cognitive layer for monosemantic feature decomposition, activation verbalization, and FVE reconstruction-quality validation.
- **Agents:** Three-stage Intake, Triage, and Analysis pipeline with confidence scoring.
- **Security:** Privacy by design aligned with GDPR / DSGVO Art. 25, including local sanitization before downstream model or copilot access.

## Current Implementation Focus
- `src/core/kvtc_v7.py` implements the deterministic KVTC-V7 compression engine.
- Technical logs are parsed as structured events, preserving timestamps, severity, ECU/module, OBD/SPN/FMI/DTC codes, and key-value measurements.
- Extreme Consonant Mapping aggressively removes low-entropy vowels while preserving high-entropy diagnostic codes, numeric measurements, and domain abbreviations.

## Near-Term Roadmap
1. Add `src/interpretability/sae_nla.py` with sparse autoencoder feature decomposition, activation verbalizer, and FVE metrics.
2. Add `src/agents/intake_agent.py` with `nh3` XSS protection, FIN/VIN masking, email removal, and SHA-256 personal-number hashing.
3. Add `src/agents/triage_agent.py` with OBD-based P1/P2/P3 prioritization.
4. Add `src/copilot/mcp_server.py` as a federated MCP connector exposing compressed results plus SAE explanations.
