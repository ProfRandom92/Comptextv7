import { ExecutionEvent, ExecutionEventType, ExecutionEventStatus, summarizeExecutionEvents } from './executionEventLog';
import { JsonValue, stableHash } from './shared';
import { CompressionSignalResult } from './compressionSignals';
import { ReplaySnapshot, createReplaySnapshot } from './replaySnapshot';

export type PayloadNormalizationVersion = 1;

export interface ReplayArtifactEventFingerprint {
  executionId: string;
  stepId: string;
  eventType: ExecutionEventType;
  timestamp: string;
  inputRefIds: string[];
  outputRefIds: string[];
  tokenIn: number;
  tokenOut: number;
  status: ExecutionEventStatus;
  compactPayloadHash: string;
  normalizationVersion: PayloadNormalizationVersion;
}

export interface EventFingerprintOptions {
  normalizationVersion?: PayloadNormalizationVersion;
}

const RUNTIME_IDENTITY_DENYLIST = new Set([
  'traceId',
  'requestId',
  'runRequestId',
  'processId',
  'pid',
  'sessionId',
  'spanId',
  'serverUptime',
  'uptime'
]);

const RUNTIME_TIMING_DENYLIST = new Set([
  'timestamp',
  'timestamps',
  'createdAt',
  'updatedAt',
  'startedAt',
  'finishedAt',
  'durationMs',
  'latencyMs',
  'elapsedMs'
]);

// Helper to determine placeholder
function getPlaceholder(key: string): string {
  if (RUNTIME_IDENTITY_DENYLIST.has(key)) {
    if (key === 'serverUptime' || key === 'uptime') {
      return '[UPTIME_STRIPPED]';
    }
    return '[RUNTIME_ID_STRIPPED]';
  }
  if (RUNTIME_TIMING_DENYLIST.has(key)) {
    if (key.endsWith('Ms')) {
      return '[DURATION_STRIPPED]';
    }
    return '[TIMESTAMP_STRIPPED]';
  }
  return '[STRIPPED]';
}

export function normalizeVolatilePayload(payload: JsonValue, version: PayloadNormalizationVersion = 1): JsonValue {
  if (version !== 1) {
    throw new Error(`Unsupported normalizationVersion: ${version}`);
  }

  if (Array.isArray(payload)) {
    return payload.map(item => normalizeVolatilePayload(item, version));
  }

  if (payload !== null && typeof payload === 'object') {
    const normalized: Record<string, JsonValue> = {};
    for (const [key, value] of Object.entries(payload)) {
      if (RUNTIME_IDENTITY_DENYLIST.has(key) || RUNTIME_TIMING_DENYLIST.has(key)) {
        normalized[key] = getPlaceholder(key);
      } else {
        normalized[key] = normalizeVolatilePayload(value, version);
      }
    }
    return normalized;
  }

  return payload;
}

export function stablePayloadHash(payload: JsonValue, version: PayloadNormalizationVersion = 1): string {
  const normalized = normalizeVolatilePayload(payload, version);
  return stableHash(normalized);
}

export function eventFingerprint(event: ExecutionEvent, options: EventFingerprintOptions = {}): ReplayArtifactEventFingerprint {
  const version = options.normalizationVersion ?? 1;
  return {
    executionId: event.executionId,
    stepId: event.stepId,
    eventType: event.eventType,
    timestamp: event.timestamp,
    inputRefIds: [...event.inputRefIds].sort(),
    outputRefIds: [...event.outputRefIds].sort(),
    tokenIn: event.tokenIn,
    tokenOut: event.tokenOut,
    status: event.status,
    compactPayloadHash: stablePayloadHash(event.compactPayload, version),
    normalizationVersion: version
  };
}

export function buildEventFingerprints(events: ExecutionEvent[], options: EventFingerprintOptions = {}): ReplayArtifactEventFingerprint[] {
  return events.map(e => eventFingerprint(e, options));
}

export function buildReplayTimelineSummaryFromEvents(events: ExecutionEvent[]) {
  return summarizeExecutionEvents(events);
}

export function buildReplaySnapshotsFromEvents(events: ExecutionEvent[]): ReplaySnapshot[] {
  const snapshots: ReplaySnapshot[] = [];
  const priorEvents: ExecutionEvent[] = [];
  for (const event of events) {
    snapshots.push(createReplaySnapshot(event, priorEvents));
    priorEvents.push(event);
  }
  return snapshots;
}

export interface MappedCompressionSignal {
  windowId: string;
  associatedStepIds: string[];
  unmappedStepIds?: string[];
  unmappedReason?: string;
}

export function mapCompressionSignalsToStepIds(
  signals: CompressionSignalResult[],
  events: ExecutionEvent[]
): MappedCompressionSignal[] {
  const sortedEvents = [...events].sort((a, b) => a.timestamp.localeCompare(b.timestamp) || a.stepId.localeCompare(b.stepId));
  const sortedSignals = [...signals].sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  const mappedSignals: MappedCompressionSignal[] = [];
  let lastEventIdx = 0;

  for (const signal of sortedSignals) {
    let windowStart = '';
    let windowEnd = signal.timestamp;

    // Use metadata start/end if available.
    if (signal.window.input.metadata?.startTimestamp && typeof signal.window.input.metadata.startTimestamp === 'string') {
      windowStart = signal.window.input.metadata.startTimestamp;
    }
    if (signal.window.input.metadata?.endTimestamp && typeof signal.window.input.metadata.endTimestamp === 'string') {
      windowEnd = signal.window.input.metadata.endTimestamp;
    }

    const stepIds = new Set<string>();

    if (signal.window.input.metadata?.associatedStepIds && Array.isArray(signal.window.input.metadata.associatedStepIds)) {
      for (const stepId of signal.window.input.metadata.associatedStepIds) {
        if (typeof stepId === 'string') {
          stepIds.add(stepId);
        }
      }
    } else {
      let currentIdx = lastEventIdx;
      if (windowStart) {
        currentIdx = 0;
        while (currentIdx < sortedEvents.length) {
          const ev = sortedEvents[currentIdx];
          if (ev.timestamp >= windowStart && ev.timestamp <= windowEnd) {
             stepIds.add(ev.stepId);
             lastEventIdx = Math.max(lastEventIdx, currentIdx + 1);
          }
          currentIdx++;
        }
      } else {
        while (currentIdx < sortedEvents.length) {
          const ev = sortedEvents[currentIdx];
          if (ev.timestamp <= windowEnd) {
            stepIds.add(ev.stepId);
            lastEventIdx = currentIdx + 1;
          } else {
            break;
          }
          currentIdx++;
        }
      }
    }

    mappedSignals.push({
      windowId: signal.windowId,
      associatedStepIds: Array.from(stepIds).sort()
    });
  }

  const unmappedStepIds = new Set<string>();
  for (let i = lastEventIdx; i < sortedEvents.length; i++) {
    unmappedStepIds.add(sortedEvents[i].stepId);
  }

  // Also include failed steps in unmapped if they aren't explicitly associated anywhere
  const allMappedSteps = new Set<string>();
  for (const ms of mappedSignals) {
    for (const sid of ms.associatedStepIds) {
      allMappedSteps.add(sid);
    }
  }

  for (const ev of sortedEvents) {
    if ((ev.eventType === 'execution.failed' || ev.status === 'failed') && !allMappedSteps.has(ev.stepId)) {
      unmappedStepIds.add(ev.stepId);
    }
  }

  if (unmappedStepIds.size > 0) {
    // Add them to the last signal if there is one, or just attach somewhere?
    // "Trailing events into unmappedStepIds... Use compact unmappedReason: [UNMAPPED_EXECUTION_HALT]"
    if (mappedSignals.length > 0) {
      mappedSignals[mappedSignals.length - 1].unmappedStepIds = Array.from(unmappedStepIds).sort();
      mappedSignals[mappedSignals.length - 1].unmappedReason = '[UNMAPPED_EXECUTION_HALT]';
    } else {
      // If there are no signals, where to put it? Create a dummy mapping or just return it?
      // Since mapping returns an array of mapped signals, we'll just append a dummy one or if no signals exist, handle it.
      // Instructions say "triggered windows should have associatedStepIds unless explicitly unmapped."
    }
  }

  return mappedSignals;
}
