import { DecisionQualityEngine } from './decisionQuality';
import { InMemoryExecutionEventStore, appendExecutionEvent, getExecutionTimeline, summarizeExecutionEvents } from './executionEventLog';
import { createReplaySnapshot } from './replaySnapshot';
import { CompactPromptBuilder, ContextManifestBuilder, SemanticReferenceRegistry, TokenBudgetManager } from './semanticReferences';

const registry = new SemanticReferenceRegistry();
const reference = registry.register({
  uri: 'ctx://example/core-promise',
  summary: 'CompTextv7 keeps execution observable through compact semantic references.',
  tokenEstimate: 18,
  relevanceScore: 0.95,
  resolver: 'static-sample',
  createdAt: '2026-05-15T00:00:00.000Z',
  metadata: { rawTokenEstimate: 120 },
});
const manifest = new ContextManifestBuilder(new TokenBudgetManager(64)).build('exec-sample', [reference], '2026-05-15T00:00:01.000Z');
const eventStore = new InMemoryExecutionEventStore();
const event = appendExecutionEvent(eventStore, {
  executionId: 'exec-sample',
  stepId: 'step-1',
  agentId: 'agent-core',
  timestamp: '2026-05-15T00:00:02.000Z',
  eventType: 'context.selected',
  inputRefIds: [],
  outputRefIds: [reference.id],
  tokenIn: 18,
  tokenOut: 0,
  latencyMs: 3,
  status: 'succeeded',
  compactPayload: { manifestId: manifest.manifestId },
});

export const coreFoundationSample = Object.freeze({
  reference,
  manifest,
  compactPrompt: new CompactPromptBuilder().build(manifest),
  timelineSummary: summarizeExecutionEvents(getExecutionTimeline(eventStore, 'exec-sample'), 'exec-sample'),
  replaySnapshot: createReplaySnapshot(event),
  quality: new DecisionQualityEngine({
    weights: { validity: 1, specificity: 1, correctness: 1, traceability: 1, rollbackSafety: 1, tokenEfficiency: 1 },
    tokenBudget: 64,
  }).evaluate({
    validityChecksPassed: 1,
    validityChecksTotal: 1,
    specificCriteriaMet: 1,
    specificCriteriaTotal: 1,
    correctnessChecksPassed: 1,
    correctnessChecksTotal: 1,
    linkedReplayStepIds: ['step-1'],
    linkedReferenceIds: [reference.id],
    artifactRefs: [],
    replaySnapshotIds: [],
    tokenUsed: manifest.totalTokenEstimate,
  }),
});
