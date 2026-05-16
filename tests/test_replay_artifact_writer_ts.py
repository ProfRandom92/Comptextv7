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

            const events = [
              {
                executionId: 'exec-1',
                stepId: 'step-1',
                agentId: 'agent-1',
                timestamp: '2026-05-15T00:00:01.000Z',
                eventType: 'context.selected',
                inputRefIds: [],
                outputRefIds: [],
                tokenIn: 10,
                tokenOut: 0,
                latencyMs: 1,
                status: 'succeeded',
                compactPayload: { a: 1 }
              },
              {
                executionId: 'exec-1',
                stepId: 'step-2',
                agentId: 'agent-1',
                timestamp: '2026-05-15T00:00:02.000Z',
                eventType: 'tool.called',
                inputRefIds: [],
                outputRefIds: [],
                tokenIn: 10,
                tokenOut: 0,
                latencyMs: 1,
                status: 'succeeded',
                compactPayload: { b: 2 }
              },
              {
                executionId: 'exec-1',
                stepId: 'step-3',
                agentId: 'agent-1',
                timestamp: '2026-05-15T00:00:03.000Z',
                eventType: 'execution.failed',
                inputRefIds: [],
                outputRefIds: [],
                tokenIn: 10,
                tokenOut: 0,
                latencyMs: 1,
                status: 'failed',
                compactPayload: { c: 3 }
              }
            ];

            const signals = [
              {
                executionId: 'exec-1',
                windowId: 'win-1',
                timestamp: '2026-05-15T00:00:01.500Z',
                profileId: 'prof-1',
                mode: 'habit',
                predictionError: 0.1,
                triggered: true,
                window: {
                  input: {
                      executionId: 'exec-1',
                      windowId: 'win-1',
                      timestamp: '2026-05-15T00:00:01.500Z',
                      profileId: 'prof-1',
                      compressionRatio: 0.5,
                      baselineCompressionRatio: 0.5,
                      sparseFrameRate: 0.1,
                      baselineSparseFrameRate: 0.1,
                      unseenSignatureRate: 0.1,
                      metadata: {
                          startTimestamp: '2026-05-15T00:00:00.000Z',
                          endTimestamp: '2026-05-15T00:00:01.500Z'
                      }
                  },
                  compressionRatioDrop: 0,
                  sparseFrameSpike: 0,
                  unseenSignatureSignal: 0,
                  predictionError: 0.1
                },
                reasons: []
              }
            ];

            const artifact1 = createReplayArtifact({
              artifactId: 'art-1',
              executionId: 'exec-1',
              createdAt: '2026-05-15T00:00:00.000Z',
              referenceIndex: coreFoundationSample.referenceIndex,
              events: events,
              compressionSignals: signals
            });

            const artifact2 = createReplayArtifact({
              artifactId: 'art-1',
              executionId: 'exec-1',
              createdAt: '2026-05-15T00:00:00.000Z',
              referenceIndex: coreFoundationSample.referenceIndex,
              events: events,
              compressionSignals: signals
            });

            assert.equal(serializeReplayArtifact(artifact1), serializeReplayArtifact(artifact2), 'Artifact serialization should be deterministic');
            assert.equal(artifact1.integrity.artifactHash, artifact2.integrity.artifactHash, 'Artifact hash should be stable');

            const validationResult = validateReplayArtifact(artifact1);
            assert.equal(validationResult.valid, true, `Validation failed: ${validationResult.errors.join(', ')}`);

            const parsed = parseReplayArtifact(serializeReplayArtifact(artifact1));
            assert.equal(parsed.integrity.artifactHash, artifact1.integrity.artifactHash, 'Parsed hash should match original');

            // Semantic change
            const eventsChanged = JSON.parse(JSON.stringify(events));
            eventsChanged[0].tokenIn = 999;
            const artifactChanged = createReplayArtifact({
              artifactId: 'art-1',
              executionId: 'exec-1',
              createdAt: '2026-05-15T00:00:00.000Z',
              referenceIndex: coreFoundationSample.referenceIndex,
              events: eventsChanged,
              compressionSignals: signals
            });
            assert.notEqual(artifact1.integrity.artifactHash, artifactChanged.integrity.artifactHash, 'Artifact hash must change if semantic content changes');

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

            const badArtifact2 = JSON.parse(JSON.stringify(coreFoundationSample.sampleReplayArtifact));
            badArtifact2.integrity.normalizationVersion = 2;
            badArtifact2.integrity.artifactHash = 'fnv1a:bad'; // Ensure it fails on norm ver first
            const val2 = validateReplayArtifact(badArtifact2);
            assert.equal(val2.valid, false);
            assert.ok(val2.errors.some(e => e.includes('normalizationVersion: expected 1')), 'Should reject missing normalizationVersion');

            const badArtifact3 = JSON.parse(JSON.stringify(coreFoundationSample.sampleReplayArtifact));
            badArtifact3.integrity.deterministicSerializationVersion = 2;
            const val3 = validateReplayArtifact(badArtifact3);
            assert.equal(val3.valid, false);
            assert.ok(val3.errors.some(e => e.includes('deterministicSerializationVersion')), 'Should reject wrong deterministicSerializationVersion');

            const badArtifact4 = JSON.parse(JSON.stringify(coreFoundationSample.sampleReplayArtifact));
            badArtifact4.integrity.artifactHashAlgorithm = 'md5';
            const val4 = validateReplayArtifact(badArtifact4);
            assert.equal(val4.valid, false);
            assert.ok(val4.errors.some(e => e.includes('artifactHashAlgorithm')), 'Should reject wrong artifactHashAlgorithm');

            const badArtifact5 = JSON.parse(JSON.stringify(coreFoundationSample.sampleReplayArtifact));
            delete badArtifact5.replayTimelineSummary;
            const val5 = validateReplayArtifact(badArtifact5);
            assert.equal(val5.valid, false);
            assert.ok(val5.errors.some(e => e.includes('Missing replayTimelineSummary')));

            const badArtifact6 = JSON.parse(JSON.stringify(coreFoundationSample.sampleReplayArtifact));
            delete badArtifact6.replaySnapshots;
            const val6 = validateReplayArtifact(badArtifact6);
            assert.equal(val6.valid, false);
            assert.ok(val6.errors.some(e => e.includes('Missing replaySnapshots')));

            const badArtifact7 = JSON.parse(JSON.stringify(coreFoundationSample.sampleReplayArtifact));
            badArtifact7.eventFingerprints = [];
            const val7 = validateReplayArtifact(badArtifact7);
            assert.equal(val7.valid, false);
            assert.ok(val7.errors.some(e => e.includes('empty while timelineSummary.eventCount > 0')));

            console.log("SUCCESS");
            """
        )
    )
    assert result == "SUCCESS"

def test_replay_artifact_writer_unmapped_cases(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const {
              createReplayArtifact,
              validateReplayArtifact
            } = require('./core/foundation');
            const { coreFoundationSample } = require('./core/foundation/sampleData');

            const events = [
              {
                executionId: 'exec-1',
                stepId: 'step-1',
                agentId: 'agent-1',
                timestamp: '2026-05-15T00:00:01.000Z',
                eventType: 'context.selected',
                inputRefIds: [],
                outputRefIds: [],
                tokenIn: 10,
                tokenOut: 0,
                latencyMs: 1,
                status: 'succeeded',
                compactPayload: { a: 1 }
              }
            ];

            // No signal case
            const artifactNoSignal = createReplayArtifact({
              artifactId: 'art-1',
              executionId: 'exec-1',
              createdAt: '2026-05-15T00:00:00.000Z',
              referenceIndex: coreFoundationSample.referenceIndex,
              events: events,
              compressionSignals: []
            });

            assert.equal(validateReplayArtifact(artifactNoSignal).valid, true);
            assert.equal(artifactNoSignal.compressionSignalMappings.length, 1);
            assert.equal(artifactNoSignal.compressionSignalMappings[0].windowId, 'synthetic-unmapped-window');
            assert.equal(artifactNoSignal.compressionSignalMappings[0].unmappedStepIds.length, 1);

            // Step in both
            const badArtifact = JSON.parse(JSON.stringify(artifactNoSignal));
            badArtifact.compressionSignalMappings[0].associatedStepIds = ['step-1'];
            badArtifact.compressionSignalMappings[0].unmappedStepIds = ['step-1'];

            const validation = validateReplayArtifact(badArtifact);
            assert.equal(validation.valid, false);
            assert.ok(validation.errors.some(e => e.includes('in both associatedStepIds and unmappedStepIds')));

            // Duplicate across mappings
            const badArtifact2 = JSON.parse(JSON.stringify(artifactNoSignal));
            badArtifact2.compressionSignalMappings.push({
                windowId: 'win-2',
                associatedStepIds: ['step-1'],
                unmappedStepIds: []
            });
            const validation2 = validateReplayArtifact(badArtifact2);
            assert.equal(validation2.valid, false);
            assert.ok(validation2.errors.some(e => e.includes('duplicate mapped stepId')));

            console.log("SUCCESS");
            """
        )
    )
    assert result == "SUCCESS"
