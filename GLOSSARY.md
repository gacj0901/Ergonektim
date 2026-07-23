# ERGONEKTIM Diagnostic Glossary

**Language:** English  
**Semantic counterpart:** [`GLOSARIO.md`](GLOSARIO.md)  
**Scope:** Product-level observations, state coordinates, evidence metrics, configuration, and diagnostic signals  
**Status:** Foundational glossary

## How to read this glossary

ERGONEKTIM distinguishes four roles:

| Role | Meaning |
|---|---|
| **Input** | A value supplied by a declared source or domain adapter |
| **State** | A causal coordinate produced by the certified kernel |
| **Evidence** | A derived value used by an observer to justify a diagnosis |
| **Configuration** | A value frozen before evaluation; it is not itself a result |

Unless a source contract declares physical units, kernel coordinates are normalized and dimensionless. A diagnostic label is never a substitute for the evidence values that support it.

## 1. Time and record identity

| Symbol or field | Role | Definition and diagnostic use |
|---|---|---|
| `t` | Input | Causal timestamp of an observation, represented canonically in UTC. |
| `k` | Input | Zero-based position of an accepted input in the emitted stream. |
| `h` | Configuration | Duration of one state step, expressed in stream bins. Electrical hourly runs normally declare `h=1 h`. |
| `input_index` | State | Index of the input consumed to produce the current row. |
| `state_index` | State | Index of the resulting state; `state_index = input_index + 1`. |
| `valid` | State | Confirms that the row was emitted under the input contract. An internal invalid row fails closed and is not emitted as a valid state. |

## 2. Observation and universal state

| Symbol or field | Role | Definition and diagnostic use |
|---|---|---|
| `omega`, `ω` | Input | Observed domain quantity after the declared electrical adapter and normalization. |
| `expected`, `ω_hat` | Input | Causal expectation available no later than `t`; it must not use future observations. |
| `sigma_op`, `σ_op` | Input | Boolean operational-eligibility mask. `false` means the system state is not eligible for an operational diagnosis at that row. |
| `delta`, `Δ` | Evidence | Instantaneous normalized discrepancy: `abs(ω-ω_hat)/(ω_hat+1)`. It measures mismatch, not failure severity. |
| `delta_ref` | Configuration | Positive calibration reference used to make discrepancies comparable without reading evaluation outcomes. |
| `delta_tilde`, `Δ_tilde` | Evidence | Reference-scaled discrepancy: `Δ/delta_ref`. |
| `tau`, `τ` | Configuration | Causal memory scale in emitted bins. It governs retention but is not a diagnostic result. |
| `r` | Configuration | Exact retention factor `exp(-h/τ)`. It is derived, never independently tuned. |
| `xi`, `Ξ` | State | Causal accumulated structural tension. `Ξ_next = r Ξ + (1-r) Δ_tilde`. Larger values mean more retained mismatch, not automatically imminent failure. |
| `theta`, `Θ` | State | Endogenous viability threshold induced from remaining capacity: `Θ = theta_scale * λ`. |
| `lambda`, `λ` | State | Bounded remaining capacity or permissivity available to absorb accumulated tension. |
| `e` | State | Positive excess before the current update: `max(Ξ-Θ,0)`. It is the quantity added to accumulated debt. |
| `A` | State | Monotone accumulated excess debt. It records unresolved past excess and is not reset by a temporary recovery input. |
| `u_lambda`, `u_λ` | Input | Declared nonnegative regeneration or capacity-restoration input. It must come from the domain contract. |
| `pi`, `π` | Evidence | Capacity-boundary clip impulse: difference between clipped and raw capacity. It records the arithmetic effect of the declared capacity bounds. |
| `M` | State | Viability margin `Θ-Ξ`. Positive margin means tension is below the current threshold; negative margin means the threshold is exceeded. |
| `smooth_M` | Evidence | Causal trailing arithmetic mean of `M` over the declared emitted-row window. |
| `G` | Evidence | Backward change in `smooth_M`. Negative `G` means the causal margin trend is deteriorating; positive `G` means it is improving. |

## 3. Frozen kernel configuration

| Field | Role | Definition |
|---|---|---|
| `theta_scale` | Configuration | Positive scale converting `λ` into `Θ`. |
| `lambda_0` | Configuration | Initial capacity, inside the declared capacity interval. |
| `lambda_min` | Configuration | Capacity floor. Reaching it does not erase debt or tension. |
| `lambda_max` | Configuration | Capacity ceiling. |
| `kappa_v3`, `κ` | Configuration | Coupling from accumulated debt to capacity drain. |
| `g_smooth` | Configuration | Number of emitted margins used by the causal trailing mean. |

## 4. Telemetric Status and observability

| Symbol or field | Role | Definition and diagnostic use |
|---|---|---|
| `q` | Input | Normalized observed drain used by the telemetric reserve-state envelope. Its normalization is declared by the source contract. |
| `source_valid` | Input | Validity of an individual source at the current timestamp. |
| `joint_source_valid` | Evidence | Logical conjunction of every source required by the observer. |
| `s_lower`, `s_minus` | State | Causal lower bound of the admissible reserve state after missing observations. |
| `s_upper`, `s_plus` | State | Causal upper bound of the admissible reserve state. |
| `interval_width` | Evidence | `s_upper-s_lower`; the uncertainty induced by missingness and retained memory. |
| `g_per_step` | Configuration | Contraction/regeneration coefficient of the telemetric interval. It is distinct from the margin trend `G`. |
| `eta` | Configuration | Maximum missing-row drain coefficient under the frozen interval contract. |
| `q_max` | Configuration | Maximum admissible normalized drain used for causal worst-case propagation. |
| `tol_s` | Configuration | Maximum interval width compatible with a clear observation. It is fixed independently of outcome survival. |
| `observability_clear` | Evidence | Boolean gate: source values are valid and the causal interval width is no larger than `tol_s`. |
| `quarantine_reasons` | Evidence | Explicit reasons why a timestamp cannot support downstream diagnosis. |

## 5. Graph-enabled electrical carrier

These fields are present only when an assessment declares a physical graph source.

| Symbol or field | Role | Definition and diagnostic use |
|---|---|---|
| `v` | Input | Substation represented as a primal graph node. |
| `edge`, `e_graph` | Input | Individually identified transmission circuit represented as a primal graph edge. |
| `boundary_node` | Input | Interconnection endpoint with partial state because it is not a fully observed host substation. |
| `c_v` | Input | Boolean indicator that an automatic nodal or incident-circuit outage compromises node `v`. |
| `z_v` | State | Attack-release compromise envelope: instantaneous latch at an event and exponential recovery afterward. It is a state, not event intensity. |
| `T_r` | Configuration | Recovery time used by the `z_v` release envelope, selected by the preregistered calibration rule. |
| `edge_state` | Input | `conducting` or `isolated`, derived from observed line-outage intervals. |
| `planned` | Input | Declared planned intervention. It is an observed exogenous isolation policy, not an inferred failure. |
| `active_subgraph` | Evidence | Nodes and conducting edges available at `t`. It represents observed connectivity, not measured power flow. |
| `E_z` | Evidence | Gluing incompatibility energy across conducting edges. Isolated edges contribute no coupling term. |
| `conducting_fraction` | Evidence | Fraction of eligible physical edges currently conducting. |

## 6. External displacement and Causal Link

| Symbol or field | Role | Definition and diagnostic use |
|---|---|---|
| `w_j(t)` | Input | External displacement component with its own observation, causal reference, declared signed or absolute normalization, validity, and provenance. Components are not pooled by default. |
| `w_valid` | Evidence | Eligibility mask for each external component. Invalid values remain quarantined and are not imputed. |
| `Phi`, `Φ` | Input | Declared internal or organizational register offered to the attribution comparison. Causal Link remains fail-closed without executable row custody and a hash-bound level-1 conformance certificate. |
| `phi_valid` | Evidence | Source-validity mask for `Φ`; Causal Link requires both adjacent rows to be valid. |
| `phi_issued_at` | Evidence | Row issue time. A value issued after its evaluation timestamp is quarantined. |
| `construction_spec_sha256` | Custody | Hash binding `Φ` or `R` to its declared construction specification. |
| `operational_conformance_certificate_sha256` | Custody | Hash of the external level-1 certificate authorizing a particular `Φ` construction. It is distinct from a representation-theorem claim. |
| `representation_theorem_claimed` | Claim boundary | Records whether a separate representation theorem is claimed; software does not infer this from numerical checks. |
| `Psi_j`, `Ψ_j` | Evidence | External-response arm associated with component `j`. |
| `mismatch` | Evidence | Local discrepancy `abs(Φ-Ψ_j)`. |
| `mismatch_change` | Evidence | Change in mismatch from the preceding eligible row. Nonpositive values mean no new deterioration under this local contract. |
| `phi_contribution` | Evidence | Symmetric two-input Shapley contribution assigned to the change in `Φ`. |
| `psi_contribution` | Evidence | Symmetric two-input Shapley contribution assigned to the change in `Ψ_j`. |
| `external_cause_labels` | Input | Independent validation labels. They test attribution but never enter its calculation. |

The Causal Link labels identify the dominant signal contribution. They do not by themselves prove complete physical causality.

## 7. Operator representation and Estimation Fidelity

| Symbol or field | Role | Definition and diagnostic use |
|---|---|---|
| `R(t)` | Input | External, operator-owned representation of structural excess, issued no later than `t` and normalized under a declared contract. |
| `structural_excess` | Evidence | Kernel excess `Ξ-Θ`. |
| `representation_error` | Evidence | Absolute difference `abs(R-(Ξ-Θ))`. |
| `fidelity`, `F` | Evidence | Normalized representation fidelity `1-representation_error/Θ`. Positive values indicate error smaller than the current threshold; zero is the critical boundary; negative values indicate error larger than the threshold. |
| `R_valid` | Evidence | Row eligibility of the external operator representation. |
| `source_roles_also_used` | Custody | Other declared roles that reuse the same operator source. |
| `dual_use_declared` | Custody | Must be true exactly when `source_roles_also_used` is nonempty. |

Fidelity measures agreement with a declared external representation. It does not establish that either representation is the complete physical truth.

## 8. Performance Status evidence

| Field | Role | Definition and diagnostic use |
|---|---|---|
| `structural_drain` | Evidence | Capacity drain ledger term `κ h A`. |
| `regeneration` | Evidence | Regeneration ledger term `h u_lambda`. |
| `net_solvency` | Evidence | `regeneration-structural_drain`. Positive is regeneration-dominant; negative is drain-dominant. |
| `effective_flow` | Input | Separately declared electrical service or throughput quantity. It is never inferred from `M`. |
| `flow_change` | Evidence | Backward difference of `effective_flow`. |
| `margin_change` | Evidence | Backward difference of `M`. |
| `regeneration_to_drain_ratio` | Evidence | `regeneration/structural_drain` when drain is positive. It is undefined when the denominator is zero. |
| `overoptimization_guard` | Evidence | Triggered when effective flow rises while viability margin falls. It is an anti-overoptimization signal, not a dispatch command. |

## 9. Condition Report evidence

| Field | Role | Definition and diagnostic use |
|---|---|---|
| `planned_episode` | Input | Maximal contiguous interval marked as a planned intervention. |
| `pre_margin_median` | Evidence | Median margin in the declared window before the episode. |
| `during_margin_minimum` | Evidence | Minimum margin during the planned episode. |
| `post_margin_median` | Evidence | Median margin in the declared recovery window after the episode. |
| `invested_drain` | Evidence | `max(pre_margin_median-during_margin_minimum,0)`. |
| `restored_margin` | Evidence | `post_margin_median-during_margin_minimum`. |
| `net_margin_vs_pre` | Evidence | `post_margin_median-pre_margin_median`; it determines regenerative, neutral, or non-restitutive classification. |
| `restoration_per_invested_drain` | Evidence | `restored_margin/invested_drain` when invested drain is positive. |
| `restricted_shift_tail_probability` | Validation | Upper-tail probability under the admissible circular-shift reference set. It is not presented as an exact unrestricted permutation p-value. |
| `null_effect` | Validation | Observed regenerative fraction minus the median circular-shift reference fraction. |

The analytic regulatory audit reports `observed_crossing`,
`reachable_not_observed`, or `unreachable_under_empirical_bound`. An empirical
bound is a property of the declared data window, not a physical system limit.

## 10. Diagnostic status dictionary

| Observer | Canonical code | User label | Scientific reading |
|---|---|---|---|
| Telemetric Status | `observability_clear` | Reliable observation | The observation and causal-memory gate are clear. |
| Telemetric Status | `partially_observable_fail_closed` | Partial coverage | Some intervals are eligible and others remain quarantined. |
| Telemetric Status | `instrument_indeterminate` | Insufficient visibility | Evidence does not support downstream state inference. |
| Stability Status | `viable` | Viable margin | `σ_op=1`, `M>=0`, and `G>=0`. This is not a theorem of global stability. |
| Stability Status | `viable_with_negative_gradient` | Viable margin with negative gradient | `σ_op=1`, `M>=0`, and `G<0`. This is a sign-only reading without a magnitude or persistence threshold; it is not a collapse alarm. |
| Stability Status | `collapsing` | Compromised viability | `M<0` or the declared operational mask is inactive on an otherwise observable row. |
| Performance Status | `solvent` | Regeneration-dominant | Regeneration exceeds structural drain. |
| Performance Status | `balanced` | Neutral balance | Regeneration and structural drain are equal. |
| Performance Status | `structural_ledger_inactive` | Structural ledger inactive | Regeneration and structural drain are both zero. This reports branch coverage, not balance evidence. |
| Performance Status | `insolvent` | Drain-dominant | Structural drain exceeds regeneration. |
| Performance Status | `overoptimization_guard_triggered` | Over-optimization alert | Effective flow increased while viability margin decreased. |
| Condition Report | `regenerative` | Regenerative intervention | Post-episode median margin exceeds its pre-episode value. |
| Condition Report | `neutral_restitution` | Neutral restitution | Post- and pre-episode median margins are equal. |
| Condition Report | `non_restitutive` | Insufficient recovery | Post-episode median margin remains below its pre-episode value. |
| Causal Link | `no_new_deterioration` | No new deterioration | Local mismatch did not increase. |
| Causal Link | `phi_internal` | Internal signal dominant | The `Φ` contribution to increased mismatch is larger. |
| Causal Link | `psi_environmental` | Environmental signal dominant | The external `Ψ_j` contribution is larger. |
| Causal Link | `joint` | Joint contribution | Both contributions are equal within the declared tolerance. |
| Estimation Fidelity | `faithful_self_image` | Aligned representation | Normalized fidelity is positive. |
| Estimation Fidelity | `critical_self_image` | Representation at critical boundary | Fidelity is zero within numerical tolerance. |
| Estimation Fidelity | `epistemically_saturated` | Representation decoupling | Representation error exceeds `Θ`. |
| Any observer | `instrument_indeterminate` | Insufficient evidence | The observer is not eligible and emits no substantive state claim. |

## 11. What the signals do not mean

- Favorable does not mean risk-free.
- Attention does not predict a future outage.
- Critical does not identify a unique physical cause.
- Indeterminate is not favorable or unfavorable; it is a refusal to infer.
- A dominant causal-link arm is not, by itself, proof of complete physical causation.
- No observer output is an automatic dispatch, switching, or protection instruction.
