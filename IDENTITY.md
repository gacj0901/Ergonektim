# ERGONEKTIM Identity Constitution

**Official expansion:** *Aptadynamic Viability Assessment for Electric Power Systems*  
**Document status:** Foundational  
**Language:** English  
**Semantic counterpart:** [`IDENTIDAD.md`](IDENTIDAD.md)  
**Constitution date:** 2026-07-21

## 1. Identity

ERGONEKTIM is an auditable diagnostic product for the aptadynamic assessment of electric power systems. It converts causal, timestamped observations into explicit and scientifically traceable viability signals while preserving uncertainty, provenance, and the limits of inference.

ERGONEKTIM is not an independent mathematical theory, a new universal kernel, a power-flow simulator, an energy-management system, or an operator control system.

## 2. Mission

ERGONEKTIM exists to make structural-viability assessment usable without weakening its scientific discipline. It evaluates:

1. integrity and sufficiency of observation;
2. structural viability and deterioration;
3. regeneration-versus-drain performance;
4. condition before and after planned interventions;
5. internally or environmentally dominant displacement signals; and
6. fidelity between the induced state and an operator-owned representation.

## 3. Normative dependency

ERGONEKTIM is an electrical-domain implementation of the universal PRAMA Protokol state machine and contracts. The dependency is one-way:

```text
PRAMA Protokol  --->  ERGONEKTIM
```

ERGONEKTIM MUST:

- consume a declared, certified PRAMA Protokol release;
- preserve the kernel version, recertification hash, implementation hashes, and configuration in every canonical run;
- keep electrical adapters, source contracts, masks, and observers outside the universal kernel; and
- refuse to maintain a divergent internal copy of the kernel.

## 4. Assessment object

An assessment object MAY be a balancing authority, electrical region, identifiable network or subnetwork, asset population, or operational window with sufficient declared coverage.

Completeness of observation is never presumed. Missingness, quarantine, boundary nodes, delayed memory contamination, and source validity are part of the diagnostic record.

## 5. Diagnostic output

The primary output is a distributive diagnostic panel:

```text
Telemetric Status
Stability Status
Performance Status
Condition Report
Causal Link
Estimation Fidelity
```

Each observer retains its own eligibility, provenance, indeterminate states, evidence, and claim boundary. ERGONEKTIM MUST NOT hide contradictory observer states inside a global scalar or a single overall traffic light.

## 6. Product signal contract

Every emitted assessment MUST provide two inseparable layers:

1. a scientific layer containing the canonical code, values, contracts, masks, and evidence; and
2. a presentation layer containing an accessible label, semantic severity, color token, icon, short explanation, evidence summary, period of validity, and suggested review action.

Color MUST NOT be the only carrier of meaning. Every signal MUST remain understandable through text and an accessible icon. A presentation label MUST NOT broaden the scientific claim encoded by its canonical status.

| Level | Token | Meaning |
|---|---|---|
| Favorable | `favorable` | Condition compatible with declared viability |
| Informational | `informational` | Neutral or descriptive condition |
| Attention | `attention` | Adverse tendency requiring review |
| Critical | `critical` | Structurally compromised condition |
| Indeterminate | `indeterminate` | Insufficient evidence; no state inference allowed |

## 7. Bilingual publication

ERGONEKTIM is published in English and Spanish from its first release. The application MUST provide a persistent `EN | ES` language switch.

Changing language MUST NOT recompute or alter an assessment. Canonical codes, mathematical symbols, units, UTC timestamps, numerical values, hashes, and scientific results remain invariant. Only presentation strings and locale formatting change.

User-facing reports MUST be self-describing in both languages. Documentation is maintained in synchronized pairs:

- `README.md` and `README.es.md`;
- `IDENTITY.md` and `IDENTIDAD.md`;
- `GLOSSARY.md` and `GLOSARIO.md`; and
- `USER_GUIDE.md` and `GUIA_DE_USUARIO.md`.

Automated checks MUST verify equal translation-key coverage across English and Spanish catalogs.

## 8. Constitutional principles

1. **Causality.** No diagnostic may use future information.
2. **Fail-closed operation.** Missing coverage, provenance, or contract produces an indeterminate state rather than an imputed conclusion.
3. **Instrument before outcome.** Scales, masks, gates, and contracts are fixed before evaluative outcomes are opened.
4. **Independent external references.** External displacement `w(t)` and operator representation `R(t)` are not reconstructed from PRAMA state variables.
5. **No hidden simulation.** Observed connectivity is not reported as measured power flow; modeled quantities are declared as models.
6. **Distributive diagnosis.** Observer channels are not pooled into a global score without a separate validated contract.
7. **Numerical custody.** Canonical runs embed version, hashes, configuration, recertification, and contracts.
8. **Preservation of negative results.** A valid absence of signal remains a result and is not retrospectively reframed as instrument failure.
9. **Layer separation.** Universal dynamics belong to PRAMA Protokol; electrical realization belongs to ERGONEKTIM.
10. **Authority-specific coupling.** Environmental and operational components are selected according to the physical envelope of each authority, not through a generic template.

## 9. Claim boundaries

ERGONEKTIM does not claim by default to predict blackouts or future outages; prevent cascading failures; establish complete physical causality; know an operator's hidden internal state; replace an EMS, contingency analysis, dispatch optimizer, or protection system; estimate power flow from connectivity alone; establish regulatory compliance; or be validated for real-time operational control.

Any such claim requires a separate preregistered task and appropriate evidence.

## 10. Repository boundary

The product repository contains only consolidated milestones: electrical source adapters and observation contracts; coverage gates and causal masks; operational observers and presentation mappings; deterministic tests and canonical artifacts; synthetic examples and authorized evidence; and methodological and user documentation.

It excludes private or unauthorized data, credentials, modified copies of PRAMA Protokol, outcome-driven sweeps, abandoned attempts without documentary value, unrelated laboratory material, and local absolute paths.

## 11. Publication rule

A milestone may be released only when it has an explicit contract, a reproducible implementation, passing tests, complete provenance, a declared claim boundary, a single verifiable canonical artifact, and documentation consistent with the code.

The experimental laboratory preserves exploratory history. ERGONEKTIM preserves the consolidated product.

## Canonical statement

> **ERGONEKTIM is an auditable, bilingual aptadynamic assessment product for electric power systems. It turns causal observations into understandable, visually explicit, and scientifically traceable viability diagnostics while preserving uncertainty, provenance, and the limits of inference.**
