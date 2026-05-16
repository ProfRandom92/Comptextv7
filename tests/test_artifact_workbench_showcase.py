"""Static validation tests for the Artifact Workbench showcase components.

These tests parse the TypeScript/TSX source files as text to assert structural
properties that must hold without running a browser or Node environment.
No new test framework is introduced; existing pytest approach is used.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SHOWCASE_SRC = REPO_ROOT / "showcase" / "app" / "src"
COMPONENTS = SHOWCASE_SRC / "components"
LIB = SHOWCASE_SRC / "lib"


class TestSampleArtifacts:
    """sampleArtifacts.ts must contain required fields and no raw prompt data."""

    def _source(self) -> str:
        return (LIB / "sampleArtifacts.ts").read_text(encoding="utf-8")

    def test_file_exists(self) -> None:
        assert (LIB / "sampleArtifacts.ts").is_file()

    def test_has_artifact_id(self) -> None:
        assert "artifactId" in self._source()

    def test_has_schema_version(self) -> None:
        assert "schemaVersion" in self._source()

    def test_has_execution_id(self) -> None:
        assert "executionId" in self._source()

    def test_has_created_at(self) -> None:
        assert "createdAt" in self._source()

    def test_has_manifest(self) -> None:
        assert "manifest" in self._source()

    def test_has_timeline_summary(self) -> None:
        assert "timelineSummary" in self._source()

    def test_has_compression_signals(self) -> None:
        assert "compressionSignals" in self._source()

    def test_has_reference_index(self) -> None:
        assert "referenceIndex" in self._source()

    def test_has_event_fingerprints(self) -> None:
        assert "eventFingerprints" in self._source()

    def test_has_artifact_hash(self) -> None:
        assert "artifactHash" in self._source()

    def test_no_date_now(self) -> None:
        """Determinism guard: no runtime date generation."""
        assert "Date.now" not in self._source()

    def test_no_math_random(self) -> None:
        """Determinism guard: no runtime randomness."""
        assert "Math.random" not in self._source()

    def test_no_raw_prompt_field(self) -> None:
        """Must not include large rawPrompt fields."""
        assert "rawPrompt" not in self._source()


class TestArtifactCodePanel:
    """ArtifactCodePanel.tsx must be read-only by default and use Monaco."""

    def _source(self) -> str:
        return (COMPONENTS / "ArtifactCodePanel.tsx").read_text(encoding="utf-8")

    def test_file_exists(self) -> None:
        assert (COMPONENTS / "ArtifactCodePanel.tsx").is_file()

    def test_uses_monaco_editor_react(self) -> None:
        assert "@monaco-editor/react" in self._source()

    def test_read_only_default_true(self) -> None:
        """Default value for readOnly must be true."""
        src = self._source()
        assert "readOnly = true" in src

    def test_no_external_api_calls(self) -> None:
        assert "fetch(" not in self._source()
        assert "axios" not in self._source()
        assert "XMLHttpRequest" not in self._source()

    def test_no_filesystem_access(self) -> None:
        assert "fs." not in self._source()
        assert "require('fs')" not in self._source()

    def test_minimap_disabled(self) -> None:
        """Minimap must be disabled by default."""
        assert "minimap" in self._source()
        assert "enabled: false" in self._source()


class TestArtifactWorkbench:
    """ArtifactWorkbench.tsx must render three panels with required summary fields."""

    def _source(self) -> str:
        return (COMPONENTS / "ArtifactWorkbench.tsx").read_text(encoding="utf-8")

    def test_file_exists(self) -> None:
        assert (COMPONENTS / "ArtifactWorkbench.tsx").is_file()

    def test_renders_workbench_container(self) -> None:
        """Must include a testid marking the workbench root."""
        assert 'data-testid="artifact-workbench"' in self._source()

    def test_renders_artifact_list(self) -> None:
        assert 'data-testid="artifact-list"' in self._source()

    def test_renders_artifact_summary(self) -> None:
        assert 'data-testid="artifact-summary"' in self._source()

    def test_summary_shows_schema_version(self) -> None:
        assert "schemaVersion" in self._source()

    def test_summary_shows_artifact_hash(self) -> None:
        assert "artifactHash" in self._source()

    def test_summary_shows_artifact_id(self) -> None:
        assert "artifactId" in self._source()

    def test_summary_shows_execution_id(self) -> None:
        assert "executionId" in self._source()

    def test_summary_shows_fingerprint_count(self) -> None:
        assert "eventFingerprints" in self._source()

    def test_summary_shows_validation_status(self) -> None:
        assert "validationStatus" in self._source()

    def test_summary_shows_compression_latest_mode(self) -> None:
        assert "latestMode" in self._source()

    def test_summary_shows_triggered_windows(self) -> None:
        assert "triggeredWindows" in self._source()

    def test_summary_shows_unmapped_step_ids(self) -> None:
        assert "unmappedStepIds" in self._source()

    def test_selecting_artifact_uses_state(self) -> None:
        """Selection must be stateful via useState."""
        assert "useState" in self._source()

    def test_uses_artifact_code_panel(self) -> None:
        assert "ArtifactCodePanel" in self._source()

    def test_no_raw_prompt_rendered(self) -> None:
        assert "rawPrompt" not in self._source()

    def test_json_pretty_printed(self) -> None:
        """JSON output must be formatted, not raw."""
        assert "JSON.stringify" in self._source()


class TestMainIntegration:
    """main.tsx must include the Workbench section without removing existing sections."""

    def _source(self) -> str:
        return (SHOWCASE_SRC / "main.tsx").read_text(encoding="utf-8")

    def test_workbench_nav_item_present(self) -> None:
        assert "Workbench" in self._source()

    def test_workbench_section_id_present(self) -> None:
        assert 'id="workbench"' in self._source()

    def test_artifact_workbench_component_imported(self) -> None:
        assert "ArtifactWorkbench" in self._source()

    def test_existing_overview_section_intact(self) -> None:
        assert 'id="overview"' in self._source()

    def test_existing_benchmarks_section_intact(self) -> None:
        assert 'id="benchmarks"' in self._source()

    def test_existing_demo_section_intact(self) -> None:
        assert 'id="demo"' in self._source()

    def test_workbench_copy_present(self) -> None:
        assert "Inspect compact replay artifacts" in self._source()
