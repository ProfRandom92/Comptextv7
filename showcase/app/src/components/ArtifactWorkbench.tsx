import { useState } from 'react';
import { ArtifactCodePanel } from './ArtifactCodePanel';
import { sampleArtifacts, type SampleArtifact } from '../lib/sampleArtifacts';

function prettyJson(value: unknown): string {
  return JSON.stringify(value, Object.keys(value as Record<string, unknown>).sort(), 2);
}

function StatusBadge({ status }: { status: SampleArtifact['validationStatus'] }) {
  const colors: Record<SampleArtifact['validationStatus'], string> = {
    pass: '#22c55e',
    warn: '#f59e0b',
    fail: '#ef4444'
  };
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: 3,
      fontSize: 11,
      fontWeight: 600,
      letterSpacing: '0.05em',
      textTransform: 'uppercase',
      color: colors[status],
      border: `1px solid ${colors[status]}`,
      background: `${colors[status]}18`
    }}>
      {status}
    </span>
  );
}

function SummaryRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '140px 1fr',
      gap: '4px 12px',
      padding: '6px 0',
      borderBottom: '1px solid #1e2533'
    }}>
      <span style={{ color: '#6b7280', fontSize: 12, lineHeight: '20px' }}>{label}</span>
      <span style={{ color: '#cbd5e1', fontSize: 12, lineHeight: '20px', wordBreak: 'break-all', fontFamily: 'monospace' }}>
        {value}
      </span>
    </div>
  );
}

/**
 * ArtifactWorkbench — three-panel inspector:
 *   left rail: artifact list
 *   center:    Monaco artifact viewer (read-only JSON)
 *   right:     artifact summary fields
 */
export function ArtifactWorkbench() {
  const [selectedId, setSelectedId] = useState<string>(sampleArtifacts[0].artifactId);

  const selected = sampleArtifacts.find((a) => a.artifactId === selectedId) ?? sampleArtifacts[0];

  const editorContent = prettyJson(selected);

  return (
    <div
      data-testid="artifact-workbench"
      style={{
        display: 'grid',
        gridTemplateColumns: '220px 1fr 280px',
        height: '640px',
        background: '#0d1117',
        border: '1px solid #1e2533',
        borderRadius: 6,
        overflow: 'hidden',
        fontFamily: 'system-ui, sans-serif'
      }}
    >
      {/* Left rail — artifact list */}
      <aside
        data-testid="artifact-list"
        style={{
          borderRight: '1px solid #1e2533',
          overflowY: 'auto',
          background: '#0d1117'
        }}
      >
        <div style={{
          padding: '10px 14px 8px',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: '#4b5563',
          borderBottom: '1px solid #1e2533'
        }}>
          Replay Artifacts
        </div>
        {sampleArtifacts.map((artifact) => {
          const isActive = artifact.artifactId === selectedId;
          return (
            <button
              key={artifact.artifactId}
              onClick={() => setSelectedId(artifact.artifactId)}
              style={{
                display: 'block',
                width: '100%',
                textAlign: 'left',
                padding: '10px 14px',
                background: isActive ? '#1a2236' : 'transparent',
                border: 'none',
                borderLeft: isActive ? '2px solid #3b82f6' : '2px solid transparent',
                cursor: 'pointer',
                color: isActive ? '#e2e8f0' : '#94a3b8'
              }}
            >
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2 }}>
                {artifact.artifactId}
              </div>
              <div style={{ fontSize: 11, color: '#4b5563' }}>
                {artifact.schemaVersion} · {artifact.validationStatus}
              </div>
            </button>
          );
        })}
      </aside>

      {/* Center — Monaco editor */}
      <div style={{ overflow: 'hidden', background: '#0d1117' }}>
        <div style={{
          padding: '8px 14px',
          fontSize: 11,
          color: '#4b5563',
          borderBottom: '1px solid #1e2533',
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}>
          <span style={{
            fontFamily: 'monospace',
            color: '#3b82f6',
            fontSize: 12
          }}>{selected.artifactId}</span>
          <span style={{ color: '#1e2533' }}>·</span>
          <span>read-only</span>
          <StatusBadge status={selected.validationStatus} />
        </div>
        <div style={{ height: 'calc(640px - 37px)' }}>
          <ArtifactCodePanel value={editorContent} language="json" height="100%" />
        </div>
      </div>

      {/* Right panel — summary */}
      <aside
        data-testid="artifact-summary"
        style={{
          borderLeft: '1px solid #1e2533',
          overflowY: 'auto',
          background: '#0a0e17',
          padding: '0 0 16px'
        }}
      >
        <div style={{
          padding: '10px 14px 8px',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: '#4b5563',
          borderBottom: '1px solid #1e2533'
        }}>
          Summary
        </div>
        <div style={{ padding: '4px 14px 0' }}>
          <SummaryRow label="artifactId" value={selected.artifactId} />
          <SummaryRow label="schemaVersion" value={selected.schemaVersion} />
          <SummaryRow
            label="artifactHash"
            value={
              <span title={selected.artifactHash}>
                {selected.artifactHash.slice(0, 24)}…
              </span>
            }
          />
          <SummaryRow label="executionId" value={selected.executionId} />
          <SummaryRow
            label="fingerprints"
            value={`${selected.eventFingerprints.length} events`}
          />
          <SummaryRow
            label="validationStatus"
            value={<StatusBadge status={selected.validationStatus} />}
          />
          {selected.compressionSignals.latestMode && (
            <SummaryRow label="latestMode" value={selected.compressionSignals.latestMode} />
          )}
          {selected.compressionSignals.triggeredWindows.length > 0 && (
            <SummaryRow
              label="triggeredWindows"
              value={selected.compressionSignals.triggeredWindows.join(', ')}
            />
          )}
          {selected.compressionSignals.unmappedStepIds.length > 0 && (
            <SummaryRow
              label="unmappedStepIds"
              value={selected.compressionSignals.unmappedStepIds.join(', ')}
            />
          )}

          <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid #1e2533' }}>
            <div style={{
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: '#4b5563',
              marginBottom: 8
            }}>Timeline</div>
            <SummaryRow label="totalSteps" value={String(selected.timelineSummary.totalSteps)} />
            <SummaryRow label="compressedSteps" value={String(selected.timelineSummary.compressedSteps)} />
            <SummaryRow label="droppedSteps" value={String(selected.timelineSummary.droppedSteps)} />
            <SummaryRow label="compressionRatio" value={selected.timelineSummary.compressionRatio} />
          </div>
        </div>
      </aside>
    </div>
  );
}
