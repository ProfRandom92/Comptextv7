# Golden Corpus

The golden corpus is the immutable deterministic replay fixture set for CompText V7. Files under `datasets/golden/` use JSON Lines, fixed UTC timestamps, stable event IDs, deterministic ordering, repeated normal-operation frames, anomaly anchors, and sparse edge cases.

## Mutation rule

Golden datasets must never be edited in place after release. Any future corpus extension must add a new file or a versioned replacement and must update this document with explicit governance approval.

## SHA256 hashes

| dataset | purpose | sha256 |
| --- | --- | --- |
| `can_bus_reference.jsonl` | CAN-like repeated frames plus sparse wheel-speed anomaly anchor. | `5118b42905c332835881c56491bac5ff0b733590995c9f696361f3b8c26d6468` |
| `scada_reference.jsonl` | SCADA pump/valve sequence with critical valve alarm and causal high-pressure warning. | `237b2666c557748c9661f4ce59fa8d84655bc88e8a46701572a806ccdc343a40` |
| `sparse_alarm_reference.jsonl` | Tiny sparse packet that exercises micro-frame routing while preserving a brake alarm anchor. | `0dc69c5cc956d2c8c7c6114e689008950a89f9db72f5396a2a8846d0803a6997` |
| `mixed_incident_reference.jsonl` | Manufacturing sequence preserving warning-to-stop causal chain. | `8a417afb0ee8db7abcd44be04a698f680f8727a3d428dbcd5cb639b7736a94ec` |

## Required checks

Run `python scripts/validate.py golden` before release. The command refuses to overwrite changed golden files and reports a mutation error if contents drift.
