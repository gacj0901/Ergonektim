# Universal input bundle

[Español](INPUT_BUNDLE.es.md) | **English**

An ERGONEKTIM input bundle is an immutable directory containing exactly two UTF-8 files:

```text
bundle/
├── manifest.json
└── timeseries.csv
```

The manifest uses schema `ergonektim.input-bundle.v1.2`. Its packaged JSON Schema is `resources/schemas/input-bundle-manifest.schema.json`; the executable loader remains authoritative and applies additional cross-field and causal checks.

## Contract by roles

Column names are local. The manifest binds them to these required roles:

| Role | Meaning |
|---|---|
| `timestamp_column` | Explicit-offset ISO-8601 timestamp on a complete, unique, increasing grid. |
| `omega` | Observed operational magnitude supplied to the PRAMA discrepancy channel. |
| `expected` | Causally available expected magnitude paired with `omega`. |
| `sigma_op` | Boolean operational-validity state. |
| `u_lambda` | Declared nonnegative regeneration input for the structural ledger. |
| `effective_flow` | Declared effective-flow channel used by the anti-overoptimization guard. |
| `planned` | Boolean marker for planned maintenance or intervention. |
| `q` | Normalized telemetric drain used by the causal observability interval. |
| `phi_register` | Internal mismatch register offered to Causal Link; the column alone never authorizes attribution. |
| `phi_valid` | Source-validity gate for the internal register. |
| `phi_issued_at` | Row-level issue time; values issued after the evaluated row are quarantined. |

The telemetry section declares one or more source-validity columns and the complete interval contract. Missing or invalid telemetry is never imputed into observability.

## Internal causal register \(\Phi\)

`causal_register.contract` declares the source, owner, role, orientation,
normalization, value bounds, closed input lineage, construction-specification
hash, causal availability, source-validity gate, outcome independence, and
independence from \(w\) and PRAMA variables. The former free
`a0_to_e1_e5_validated` switch no longer exists. Causal Link emits only when a
hash-bound level-1 operational-conformance certificate and prefix-causality
certificate are present, the register is not experimental, and the row-level
runtime checks pass. A representation-theorem claim is recorded separately
and is not synthesized by the software.

## External displacement \(w\)

`external_displacement.components` is a nonempty list. Every component independently declares:

The resulting \(w\) register is observed and contracted for component-wise Causal Link attribution. In the current product contract it is not coupled to the kernel dynamics \((\Omega,\Xi,\mathcal{A},\lambda,\Theta,M,G)\). Assessment artifacts expose this boundary explicitly; a future coupling requires a separately preregistered model.

- observation and reference roles;
- normalization and stress sign;
- source system and owner;
- observation, reference, validity, and reference-issue columns; and
- independence from the internal register and PRAMA kernel.

Components are never pooled into a global scalar. A reference issued after its evaluated timestamp is quarantined. Component selection is authority-specific: the format does not prescribe demand, wind, interchange, hydrology, weather, or any other domain channel.

The allowed normalizations are signed reference-relative, unsigned absolute-reference-relative, and signed fixed-scale. The absolute form requires `stress_sign = 1` and is appropriate when deviation magnitude—rather than direction—is the declared stress quantity.

## External operator representation \(R(t)\)

The operator representation targets `structural_excess_xi_minus_theta`. It must identify an external owner, operational coupling, normalization, hash-bound construction specification, units, validity, and issue time. It must be generated independently of PRAMA and declare an empty `prama_variables_used` list. If its source is reused in another declared role, `source_roles_also_used` and `dual_use_declared` must disclose that reuse exactly.

No evaluation labels are required for Causal Link once \(\Phi\) is conformant. Independent labels may be used in a separate validation study, but they cannot authorize operational attribution.

## Closed-data rule and custody

The CSV header must match the declared columns exactly. Undeclared columns—including accidental outcomes—stop loading. Naive timestamps, duplicate roles, extra bundle files, path traversal, non-finite kernel configuration, and incomplete source contracts also stop loading.

Every result embeds:

- the complete manifest;
- SHA-256 of `manifest.json`;
- SHA-256 of the CSV;
- a domain-separated SHA-256 of the complete bundle;
- row and temporal coverage; and
- explicit declarations that no undeclared or outcome role was accessed.

Absolute local paths are not embedded.

## Command line

Validate the bundle and certified kernel binding without evaluating:

```console
ergonektim verify --bundle INPUT_BUNDLE --recertification RECERTIFICATION.json --language en
```

Run all six observers once and write one deterministic artifact:

```console
ergonektim assess --bundle INPUT_BUNDLE --recertification RECERTIFICATION.json --output assessment.json --language en
```

Verify a received artifact by exact custody replay:

```console
ergonektim verify-artifact --artifact assessment.json --bundle INPUT_BUNDLE --recertification RECERTIFICATION.json --expected-sha256 SHA256 --language en
```

Use `--language es` for Spanish terminal messages. The language selection cannot alter scientific bytes. Existing output is never replaced unless `--overwrite` is explicit, and output cannot be written inside the immutable input bundle.

Exit code `0` means completion. Exit code `2` is a fail-closed contract stop.
