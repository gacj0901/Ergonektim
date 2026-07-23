# ERGONEKTIM

*Aptadynamic Viability Assessment for Electric Power Systems*

[Español](README.es.md) | **English**

ERGONEKTIM is an auditable bilingual product that converts causal electrical observations into explicit, distributive, and scientifically traceable viability diagnostics.

## Current status

`0.1.0.dev2` — executable product-contract construction. No real-time operational or predictive claim is made.

The current milestone provides:

- the [identity constitution](IDENTITY.md);
- the [diagnostic glossary](GLOSSARY.md);
- a canonical bilingual diagnostic-signal contract;
- a [universal closed input-bundle contract](INPUT_BUNDLE.md);
- English and Spanish status catalogs; and
- one causal, fail-closed execution path for all six observers;
- an explicit `Phi` custody contract that keeps Causal Link fail-closed until
  the declared A0-to-E1–E5 bridge is validated;
- signed, absolute-reference-relative, and fixed-scale external-displacement
  normalizations without clipping or scalar pooling;
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

Validate a canonical bundle and its certified kernel binding without evaluating:

```console
ergonektim verify --bundle INPUT_BUNDLE --recertification RECERTIFICATION.json --language en
```

Run the complete assessment:

```console
ergonektim assess --bundle INPUT_BUNDLE --recertification RECERTIFICATION.json --output assessment.json --language en
```

The command writes one deterministic JSON artifact containing input custody, the state trajectory, all six observer outputs, both language presentations, source contracts, invariants, and the complete kernel-certification binding.

## Bilingual assessment room

The [`dashboard`](dashboard/) directory contains the product-facing assessment room. It consumes a completed `ergonektim.assessment.v1.1` artifact entirely in the browser and provides:

- separate readings for all six observers;
- input, kernel, and recertification custody;
- structural trajectory and evidence inspection;
- English/Spanish presentation switching; and
- severity filtering without scientific recomputation.

The dashboard never uploads the opened assessment, recalculates observer states, or emits an overall score. A private deployed version is available at [ergonektim.gacj-xci.chatgpt.site](https://ergonektim.gacj-xci.chatgpt.site).

## Development boundary

Only consolidated product milestones belong here. Experimental attempts, private data, local absolute paths, and outcome-driven tuning remain outside this repository.
