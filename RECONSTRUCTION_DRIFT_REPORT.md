# Reconstruction Drift Report

MAX_ALLOWED_CRITICAL_LOSS = 0
MAX_ALLOWED_HIGH_LOSS = 0

## can_bus_reference.jsonl
- passed: True
- semantic_retention: 1.0
- anomaly_survivability: 1.0
- anchor_retention: 1.0
- safety_critical_retention: 1.0
- source_sha256: `b91eebc433d58d3b3da3d1e61c3f8e8542cb0ffdbb84fe823f71adf24231ed4b`
- compressed_sha256: `6dc194071f1217828be12ea4f651d6dcc64fe460390a222dcbda7704543fc2cd`
- reconstruction_sha256: `761da93fcad4b23074e28f397ee7b9d13199974909f7adbec1b05d20805b5875`
- findings: []

## mixed_incident_reference.jsonl
- passed: True
- semantic_retention: 1.0
- anomaly_survivability: 1.0
- anchor_retention: 1.0
- safety_critical_retention: 1.0
- source_sha256: `fa2c2125fcb27ab9c0dc2b08283cbb63aa17890add71684538fefbafb4eaf0ee`
- compressed_sha256: `41528385b969c3c3ec3ef2dba1e57465127732590b9ef356d7fefd1856f83f50`
- reconstruction_sha256: `5b1e31d06e41a74572bae74445231e0d405fe5df4612052680f15451c0a5c5f8`
- findings: []

## scada_reference.jsonl
- passed: True
- semantic_retention: 1.0
- anomaly_survivability: 1.0
- anchor_retention: 1.0
- safety_critical_retention: 1.0
- source_sha256: `0654ddffea1aec3af2bc4979b0694f52e631edb473b55b9bbf235af2d6d9ca4c`
- compressed_sha256: `b6cc71a30751abad9e99b66f2894f725c8467c06f4c15242c8a0a9f2dd0bcae5`
- reconstruction_sha256: `0860a2754cc45833694948d71346d52c8031ff2ffc7cc24a8b7db4dd5478d6e2`
- findings: []

## sparse_alarm_reference.jsonl
- passed: True
- semantic_retention: 1.0
- anomaly_survivability: 1.0
- anchor_retention: 1.0
- safety_critical_retention: 1.0
- source_sha256: `b31dd4ce7678ed1806a51f187a9f6aa5d14c0c598218aebbe021984b01941307`
- compressed_sha256: `572997b801b903d669ac6b7d99d94fb3843f7c54342cad16585c41b594685e28`
- reconstruction_sha256: `ee97e2846663ccbd0d6d12a4ddb65cb573f691e42e5450908a9b010e748919a5`
- findings: []

## Drift classification policy

- LOW: presentation-only difference with no operational meaning change.
- MEDIUM: context reduction requiring review but not hiding a safety signal.
- HIGH: severity, causal context, code, or anomaly semantics weakened. Maximum allowed: 0.
- CRITICAL: timestamp mutation, alarm disappearance, anchor loss, event suppression, or hallucinated reconstruction. Maximum allowed: 0.
