# Universal input bundle

[Español](INPUT_BUNDLE.es.md) | **English**

An ERGONEKTIM input bundle is an immutable directory containing exactly two UTF-8 files:

```text
bundle/
├── manifest.json
└── timeseries.csv
```

The manifest uses schema `ergonektim.input-bundle.v1`. Its packaged JSON Schema is `resources/schemas/input-bundle-manifest.schema.json`; the executable loader remains authoritative and applies additional cross-field and causal checks.

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
| `phi_register` | Internal mismatch register used by Causal Link. |

The telemetry section declares one or more source-validity columns and the complete interval contract. Missing or invalid telemetry is never imputed into observability.

## External displacement \(w\)

`external_displacement.components` is a nonempty list. Every component independently declares:

- observation and reference roles;
- normalization and stress sign;
- source system and owner;
- observation, reference, validity, and reference-issue columns; and
- independence from the internal register and PRAMA kernel.

Components are never pooled into a global scalar. A reference issued after its evaluated timestamp is quarantined. Component selection is authority-specific: the format does not prescribe demand, wind, interchange, hydrology, weather, or any other domain channel.

## External operator representation \(R(t)\)

The operator representation targets `structural_excess_xi_minus_theta`. It must identify an external owner, operational coupling, normalization, units, validity, and issue time. It must be generated independently of PRAMA and declare an empty `prama_variables_used` list.

No evaluation labels are required for Causal Link. Independent labels may be used in a separate validation study, but operational attribution is computed without them.

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

Run all six observers once and write one bilingual artifact:

```console
ergonektim assess --bundle INPUT_BUNDLE --recertification RECERTIFICATION.json --output assessment.json --language en
```

Use `--language es` for Spanish terminal messages. The artifact always embeds both languages, and the language switch cannot alter scientific bytes. Existing output is never replaced unless `--overwrite` is explicit, and output cannot be written inside the immutable input bundle.

Exit code `0` means completion. Exit code `2` is a fail-closed contract stop.
