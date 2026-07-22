# ERGONEKTIM

*Aptadynamic Viability Assessment for Electric Power Systems*

[Español](README.es.md) | **English**

ERGONEKTIM is an auditable bilingual product that converts causal electrical observations into explicit, distributive, and scientifically traceable viability diagnostics.

## Current status

`0.1.0.dev0` — executable product-contract construction. No real-time operational or predictive claim is made.

The current milestone provides:

- the [identity constitution](IDENTITY.md);
- the [diagnostic glossary](GLOSSARY.md);
- a canonical bilingual diagnostic-signal contract;
- English and Spanish status catalogs; and
- one causal, fail-closed execution path for all six observers;
- a hash-verified binding to PRAMA Protokol `0.3.0` and its numeric recertification artifact; and
- executable parity, ledger, gating, and attribution-invariant tests.

The universal state machine is supplied by a declared certified release of PRAMA Protokol. ERGONEKTIM contains the electrical realization and does not maintain a divergent kernel copy.

A canonical assessment embeds the PRAMA version, the Python kernel hash, the numeric-recertification hash, and the result of every binding check. A version string alone is insufficient.

## Diagnostic panel

ERGONEKTIM preserves six separate observer outputs:

1. Telemetric Status;
2. Stability Status;
3. Performance Status;
4. Condition Report;
5. Causal Link; and
6. Estimation Fidelity.

No global scalar or overall traffic light is emitted.

## One-run verification

With the certified PRAMA Protokol `0.3.0` package installed, the complete synthetic fixture is evaluated with:

```console
python examples/run_synthetic_assessment.py --recertification PATH/TO/v0_3_0_numeric_recertification.json --output assessment.json
```

The command writes one deterministic JSON artifact containing the state trajectory, all six observer outputs, both language presentations, source contracts, invariants, and the complete kernel-certification binding. The fixture contains no real data and supports verification only.

## Development boundary

Only consolidated product milestones belong here. Experimental attempts, private data, local absolute paths, and outcome-driven tuning remain outside this repository.
