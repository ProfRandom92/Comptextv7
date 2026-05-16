/**
 * Deterministic static sample replay artifacts for the Artifact Workbench.
 * No Date.now, no Math.random. All values are hardcoded.
 * Shaped like ReplayArtifact v1-alpha.1.
 */

export interface EventFingerprint {
  fingerprintId: string;
  eventType: string;
  hash: string;
}

export interface ReferenceIndexEntry {
  refId: string;
  label: string;
  sourceStepId: string;
}

export interface CompressionSignals {
  latestMode: string;
  triggeredWindows: string[];
  unmappedStepIds: string[];
}

export interface TimelineSummary {
  totalSteps: number;
  compressedSteps: number;
  droppedSteps: number;
  compressionRatio: string;
}

export interface Manifest {
  producer: string;
  producerVersion: string;
  pipelineStage: string;
}

export interface SampleArtifact {
  artifactId: string;
  schemaVersion: string;
  executionId: string;
  createdAt: string;
  artifactHash: string;
  validationStatus: 'pass' | 'fail' | 'warn';
  manifest: Manifest;
  timelineSummary: TimelineSummary;
  compressionSignals: CompressionSignals;
  referenceIndex: ReferenceIndexEntry[];
  eventFingerprints: EventFingerprint[];
}

export const sampleArtifacts: SampleArtifact[] = [
  {
    artifactId: 'artifact-c7-001',
    schemaVersion: 'v1-alpha.1',
    executionId: 'exec-2024-09-15-alpha-001',
    createdAt: '2024-09-15T09:00:00.000Z',
    artifactHash: 'sha256:4a8b2e1d9f3c7055abc12345678901234567890abcdef1234567890abcdef1234',
    validationStatus: 'pass',
    manifest: {
      producer: 'ReplayArtifactWriter',
      producerVersion: 'v1-alpha.1',
      pipelineStage: 'deterministic-validation'
    },
    timelineSummary: {
      totalSteps: 42,
      compressedSteps: 38,
      droppedSteps: 4,
      compressionRatio: '0.905'
    },
    compressionSignals: {
      latestMode: 'compact',
      triggeredWindows: ['window-001', 'window-003'],
      unmappedStepIds: []
    },
    referenceIndex: [
      { refId: 'ref-001', label: 'Task: Implement auth flow', sourceStepId: 'step-003' },
      { refId: 'ref-002', label: 'Constraint: No external API calls', sourceStepId: 'step-007' },
      { refId: 'ref-003', label: 'Blocker: Missing DB schema', sourceStepId: 'step-012' }
    ],
    eventFingerprints: [
      { fingerprintId: 'fp-001', eventType: 'task_created', hash: 'fp:a1b2c3d4' },
      { fingerprintId: 'fp-002', eventType: 'constraint_applied', hash: 'fp:e5f6a7b8' },
      { fingerprintId: 'fp-003', eventType: 'blocker_registered', hash: 'fp:c9d0e1f2' },
      { fingerprintId: 'fp-004', eventType: 'recovery_action_logged', hash: 'fp:g3h4i5j6' }
    ]
  },
  {
    artifactId: 'artifact-c7-002',
    schemaVersion: 'v1-alpha.1',
    executionId: 'exec-2024-09-22-alpha-002',
    createdAt: '2024-09-22T14:30:00.000Z',
    artifactHash: 'sha256:7f1a3c5e9b2d4f68def98765432109876543210fedcba9876543210fedcba9876',
    validationStatus: 'warn',
    manifest: {
      producer: 'ReplayArtifactWriter',
      producerVersion: 'v1-alpha.1',
      pipelineStage: 'deterministic-validation'
    },
    timelineSummary: {
      totalSteps: 67,
      compressedSteps: 55,
      droppedSteps: 12,
      compressionRatio: '0.821'
    },
    compressionSignals: {
      latestMode: 'aggressive',
      triggeredWindows: ['window-002', 'window-004', 'window-007'],
      unmappedStepIds: ['step-031', 'step-045']
    },
    referenceIndex: [
      { refId: 'ref-010', label: 'Task: Paper replay validation', sourceStepId: 'step-001' },
      { refId: 'ref-011', label: 'Dependency: agent_trace_bench v2', sourceStepId: 'step-019' }
    ],
    eventFingerprints: [
      { fingerprintId: 'fp-010', eventType: 'task_created', hash: 'fp:k7l8m9n0' },
      { fingerprintId: 'fp-011', eventType: 'dependency_registered', hash: 'fp:o1p2q3r4' },
      { fingerprintId: 'fp-012', eventType: 'drift_detected', hash: 'fp:s5t6u7v8' }
    ]
  },
  {
    artifactId: 'artifact-c7-003',
    schemaVersion: 'v1-alpha.1',
    executionId: 'exec-2024-10-01-alpha-003',
    createdAt: '2024-10-01T08:15:00.000Z',
    artifactHash: 'sha256:3d9e5a7f1b4c6d8e2f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2',
    validationStatus: 'fail',
    manifest: {
      producer: 'ReplayArtifactWriter',
      producerVersion: 'v1-alpha.1',
      pipelineStage: 'deterministic-validation'
    },
    timelineSummary: {
      totalSteps: 28,
      compressedSteps: 19,
      droppedSteps: 9,
      compressionRatio: '0.679'
    },
    compressionSignals: {
      latestMode: 'aggressive',
      triggeredWindows: ['window-001'],
      unmappedStepIds: ['step-008', 'step-015', 'step-022']
    },
    referenceIndex: [
      { refId: 'ref-020', label: 'Task: Iterative degradation test', sourceStepId: 'step-002' }
    ],
    eventFingerprints: [
      { fingerprintId: 'fp-020', eventType: 'task_created', hash: 'fp:w9x0y1z2' },
      { fingerprintId: 'fp-021', eventType: 'validation_failure', hash: 'fp:a3b4c5d6' }
    ]
  }
];
