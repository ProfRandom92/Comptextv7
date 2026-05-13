# Full Real-World Semantic Continuity Validation Phase

Generated with `python benchmarks/run_replay_continuity.py --iterations 250 --output-dir reports/replay_continuity`.

## Honest answers

1. **Does CompText V7 outperform baseline replay systems?** Yes under this deterministic hostile suite. At 250 iterations, mean final continuity was `0.571783` for `comptext_v7`, versus `0.302497` adaptive, `0.294488` baseline, and `0.039460` naive.
2. **How much evaluator bias existed previously?** The new external judges expose material disagreement that older aggregate-only scoring would have hidden. Mean evaluator divergence at 250 iterations was `0.421743` for CompText V7, `0.718756` adaptive, `0.767992` baseline, and `0.976445` naive. This means prior single-score views were likely overconfident, especially for degraded baselines.
3. **How quickly does continuity degrade under adversarial pressure?** Naive replay collapses at iteration `1.0` on average, baseline at `9.8`, adaptive at `44.7`, and CompText V7 did not cross the collapse threshold during the 250-iteration run, so its reported collapse point is censored at `250.0`.
4. **Does graceful degradation persist under independent judging?** Yes, but not perfectly. CompText V7 dropped from near-perfect continuity at 25 iterations to `0.571783` at 250 iterations. It still degraded slower than all baselines.
5. **Where does replay collapse occur?** Collapse is immediate for naive replay, early for baseline replay, mid-horizon for adaptive replay, and not observed for CompText V7 by iteration 250 in this suite.
6. **Which semantic structures survive longest?** For CompText V7 at 250 iterations, architecture mutation resistance (`0.869847`) and temporal causality retention (`0.955067`) survived best. Hidden truth survival (`0.570173`) and final continuity (`0.571783`) show the real long-horizon weakness.

## 250-iteration summary

| Mode | Final continuity | Mean collapse iteration | Half-life | Hidden truth survival | Temporal causality | Architecture resistance | Evaluator divergence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| naive | 0.039460 | 1.0 | 1.0 | 0.004326 | 0.054500 | 0.002448 | 0.976445 |
| baseline | 0.294488 | 9.8 | 9.8 | 0.236131 | 0.438333 | 0.206661 | 0.767992 |
| adaptive | 0.302497 | 44.7 | 44.7 | 0.314072 | 0.484350 | 0.265288 | 0.718756 |
| comptext_v7 | 0.571783 | 250.0 | 250.0 | 0.570173 | 0.955067 | 0.869847 | 0.421743 |

## Failure visibility

The run intentionally does not hide bad results:

- CompText V7 loses hidden-truth fidelity by long horizon (`0.570173` at 250 iterations).
- Evaluator disagreement remains significant even for CompText V7 (`0.421743`).
- Contradiction pressure is not zero for CompText V7 (`max_contradiction_accumulation=0.111111`).
- Baselines collapse early and remain operationally incoherent under strict judges.

## Visual artifacts

- `replay_collapse_curves.svg`
- `continuity_half_life_chart.svg`
- `contradiction_accumulation_heatmap.svg`
- `temporal_consistency_degradation.svg`
- `architecture_mutation_timeline.svg`
- `evaluator_agreement_divergence.svg`
- `hidden_constraint_survival_curves.svg`
