import json
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_APP = REPO_ROOT / "dashboard" / "app"
TSC = DASHBOARD_APP / "node_modules" / ".bin" / "tsc"

def run_foundation_script(tmp_path: Path, script: str):
    out_dir = tmp_path / "compiled"
    source_files = sorted((DASHBOARD_APP / "src" / "core" / "foundation").glob("*.ts"))
    subprocess.run(
        [
            str(TSC),
            "--target",
            "ES2022",
            "--module",
            "CommonJS",
            "--moduleResolution",
            "Node",
            "--rootDir",
            str(DASHBOARD_APP / "src"),
            "--outDir",
            str(out_dir),
            "--strict",
            "--skipLibCheck",
            *[str(path) for path in source_files],
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    script_path = out_dir / "runner.js"
    script_path.write_text(script)

    result = subprocess.run(
        ["node", str(script_path)],
        cwd=out_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()

def test_replay_artifact_writer_deterministic(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const {
              createReplayArtifact,
              serializeReplayArtifact,
              parseReplayArtifact,
              validateReplayArtifact
            } = require('./core/foundation');
            const { coreFoundationSample } = require('./core/foundation/sampleData');

            // 1. Core generation is deterministic
            const artifact1 = createReplayArtifact({
              artifactId: 'art-1',
              executionId: 'exec-1',
              createdAt: '2026-05-15T00:00:00.000Z',
              referenceIndex: coreFoundationSample.referenceIndex,
              events: coreFoundationSample.timelineSummary.eventCount > 0 ? [] : [], // We use a copy of events
              compressionSignals: coreFoundationSample.compressionSignalWindows.map(w => ({
                executionId: 'exec-1',
                windowId: w.windowId,
                timestamp: w.timestamp,
                profileId: w.profileId,
                mode: 'habit',
                predictionError: 0.1,
                triggered: false,
                window: {
                  input: w,
                  compressionRatioDrop: 0,
                  sparseFrameSpike: 0,
                  unseenSignatureSignal: 0,
                  predictionError: 0.1
                },
                reasons: []
              }))
            });

            // Re-create to verify determinism
            const artifact2 = createReplayArtifact({
              artifactId: 'art-1',
              executionId: 'exec-1',
              createdAt: '2026-05-15T00:00:00.000Z',
              referenceIndex: coreFoundationSample.referenceIndex,
              events: [],
              compressionSignals: coreFoundationSample.compressionSignalWindows.map(w => ({
                executionId: 'exec-1',
                windowId: w.windowId,
                timestamp: w.timestamp,
                profileId: w.profileId,
                mode: 'habit',
                predictionError: 0.1,
                triggered: false,
                window: {
                  input: w,
                  compressionRatioDrop: 0,
                  sparseFrameSpike: 0,
                  unseenSignatureSignal: 0,
                  predictionError: 0.1
                },
                reasons: []
              }))
            });

            assert.equal(serializeReplayArtifact(artifact1), serializeReplayArtifact(artifact2), 'Artifact serialization should be deterministic');
            assert.equal(artifact1.integrity.artifactHash, artifact2.integrity.artifactHash, 'Artifact hash should be stable');

            const validationResult = validateReplayArtifact(artifact1);
            assert.equal(validationResult.valid, true, `Validation failed: ${validationResult.errors.join(', ')}`);

            const parsed = parseReplayArtifact(serializeReplayArtifact(artifact1));
            assert.equal(parsed.integrity.artifactHash, artifact1.integrity.artifactHash, 'Parsed hash should match original');

            // Ensure invalid artifactHash is caught
            const badArtifact = JSON.parse(JSON.stringify(artifact1));
            badArtifact.integrity.artifactHash = 'fnv1a:badhash';
            const badValidation = validateReplayArtifact(badArtifact);
            assert.equal(badValidation.valid, false, 'Should fail validation on bad hash');
            assert.ok(badValidation.errors.some(e => e.includes('artifactHash mismatch')), 'Should contain hash mismatch error');

            console.log("SUCCESS");
            """
        )
    )
    assert result == "SUCCESS"

def test_replay_artifact_writer_rejects_bad_schema(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const {
              validateReplayArtifact
            } = require('./core/foundation');
            const { coreFoundationSample } = require('./core/foundation/sampleData');

            const badArtifact = JSON.parse(JSON.stringify(coreFoundationSample.sampleReplayArtifact));
            badArtifact.schemaVersion = 'v2-beta';

            const validation = validateReplayArtifact(badArtifact);
            assert.equal(validation.valid, false);
            assert.ok(validation.errors.some(e => e.includes('schemaVersion')), 'Should reject wrong schema version');
            console.log("SUCCESS");
            """
        )
    )
    assert result == "SUCCESS"
