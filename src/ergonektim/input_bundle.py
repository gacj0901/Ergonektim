"""Universal, outcome-free file contract for ERGONEKTIM assessments."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

import numpy as np
import pandas as pd

from .contracts import (
    ExternalDisplacementChannel,
    OperatorRepresentationContract,
    realize_external_displacement,
    validate_operator_representation,
)
from .panel import AssessmentInputs
from .telemetry import TelemetricContract


SCHEMA_VERSION = "ergonektim.input-bundle.v1"
MANIFEST_FILE = "manifest.json"
CORE_ROLES = {
    "omega",
    "expected",
    "sigma_op",
    "u_lambda",
    "effective_flow",
    "planned",
    "q",
    "phi_register",
}
KERNEL_FIELDS = {
    "h",
    "tau",
    "theta_scale",
    "lambda_0",
    "lambda_min",
    "lambda_max",
    "kappa_v3",
    "g_smooth",
    "delta_ref",
}
ASSESSMENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class InputBundleError(ValueError):
    """Raised when an input bundle cannot prove its declared contract."""


@dataclass(frozen=True)
class LoadedAssessmentBundle:
    inputs: AssessmentInputs
    telemetric_contract: TelemetricContract
    kernel_config: dict[str, Any]
    input_binding: dict[str, Any]


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _closed_mapping(
    value: object, required: set[str], label: str
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise InputBundleError(f"{label} must be an object")
    result = dict(value)
    missing = sorted(required - set(result))
    extra = sorted(set(result) - required)
    if missing or extra:
        raise InputBundleError(
            f"{label} fields differ from contract: missing={missing}, extra={extra}"
        )
    return result


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputBundleError(f"{label} must be a nonempty string")
    return value.strip()


def _column_name(value: object, label: str) -> str:
    result = _nonempty_string(value, label)
    if result != value:
        raise InputBundleError(f"{label} cannot contain surrounding whitespace")
    return result


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputBundleError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise InputBundleError(f"{label} must be finite")
    return result


def _load_manifest(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        payload = path.read_bytes()
        text = payload.decode("utf-8")

        def reject_constant(token: str) -> None:
            raise InputBundleError(f"non-finite JSON constant is forbidden: {token}")

        manifest = json.loads(text, parse_constant=reject_constant)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputBundleError("manifest.json is not valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict):
        raise InputBundleError("manifest root must be an object")
    return manifest, payload


def _strict_datetime(value: object, label: str) -> pd.Timestamp:
    if not isinstance(value, str) or not value.strip():
        raise InputBundleError(f"{label} must be an explicit ISO-8601 timestamp")
    token = value.strip()
    try:
        parsed = datetime.fromisoformat(token.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InputBundleError(f"{label} is not ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InputBundleError(f"{label} must carry an explicit UTC offset")
    return pd.Timestamp(parsed.astimezone(timezone.utc))


def _datetime_vector(series: pd.Series, label: str) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(
        [_strict_datetime(value, f"{label}[{row}]") for row, value in enumerate(series)]
    )


def _numeric_vector(
    series: pd.Series, label: str, *, require_finite: bool
) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=np.float64)
    if require_finite and not np.isfinite(values).all():
        raise InputBundleError(f"{label} must be finite on every row")
    return values


def _boolean_vector(
    series: pd.Series, label: str, *, reject_unrecognized: bool
) -> tuple[np.ndarray, int]:
    true_tokens = {"1", "true", "t", "yes", "y", "si", "sí"}
    false_tokens = {"0", "false", "f", "no", "n"}
    values = np.zeros(len(series), dtype=np.bool_)
    recognized = np.zeros(len(series), dtype=np.bool_)
    for row, value in enumerate(series.to_numpy(dtype=object)):
        if isinstance(value, (bool, np.bool_)):
            values[row] = bool(value)
            recognized[row] = True
        elif isinstance(value, (int, np.integer, float, np.floating)):
            if math.isfinite(float(value)) and float(value) in (0.0, 1.0):
                values[row] = bool(value)
                recognized[row] = True
        elif isinstance(value, str):
            token = value.strip().lower()
            if token in true_tokens:
                values[row] = True
                recognized[row] = True
            elif token in false_tokens:
                recognized[row] = True
    unrecognized = int((~recognized).sum())
    if reject_unrecognized and unrecognized:
        raise InputBundleError(f"{label} has {unrecognized} invalid boolean tokens")
    return values & recognized, unrecognized


def _validate_kernel_config(value: object) -> dict[str, Any]:
    config = _closed_mapping(value, KERNEL_FIELDS, "kernel_config")
    numbers = {
        name: _finite_number(config[name], f"kernel_config.{name}")
        for name in KERNEL_FIELDS - {"g_smooth"}
    }
    g_smooth = config["g_smooth"]
    if isinstance(g_smooth, bool) or not isinstance(g_smooth, int) or g_smooth <= 0:
        raise InputBundleError("kernel_config.g_smooth must be a positive integer")
    if numbers["h"] <= 0 or numbers["tau"] <= 0 or numbers["theta_scale"] <= 0:
        raise InputBundleError("kernel h, tau, and theta_scale must be positive")
    if numbers["kappa_v3"] < 0 or numbers["delta_ref"] <= 0:
        raise InputBundleError("kernel kappa_v3 or delta_ref is invalid")
    if not 0 <= numbers["lambda_min"] <= numbers["lambda_0"] <= numbers["lambda_max"]:
        raise InputBundleError("kernel lambda bounds are invalid")
    return {**numbers, "g_smooth": g_smooth}


def _telemetric_contract(value: object) -> TelemetricContract:
    required = {field.name for field in fields(TelemetricContract)}
    payload = _closed_mapping(value, required, "telemetry.contract")
    cadence = payload["cadence_hours"]
    if isinstance(cadence, bool) or not isinstance(cadence, int):
        raise InputBundleError("telemetry.contract.cadence_hours must be an integer")
    for name in ("g_per_step", "eta", "q_max", "tol_s", "initial_state"):
        payload[name] = _finite_number(payload[name], f"telemetry.contract.{name}")
    payload["missingness_bias_direction"] = _nonempty_string(
        payload["missingness_bias_direction"],
        "telemetry.contract.missingness_bias_direction",
    )
    payload["q_normalization_id"] = _nonempty_string(
        payload["q_normalization_id"], "telemetry.contract.q_normalization_id"
    )
    try:
        contract = TelemetricContract(**payload)
        contract.validate()
    except (TypeError, ValueError) as exc:
        raise InputBundleError("telemetry.contract is invalid") from exc
    return contract


def _channel_contract(value: object, position: int) -> ExternalDisplacementChannel:
    required = {field.name for field in fields(ExternalDisplacementChannel)}
    payload = _closed_mapping(value, required, f"external component {position}.contract")
    boolean_fields = {
        "reference_available_by_t",
        "independent_of_internal_register",
        "independent_of_kernel",
    }
    if any(not isinstance(payload[name], bool) for name in boolean_fields):
        raise InputBundleError(f"external component {position} has non-boolean guards")
    if isinstance(payload["stress_sign"], bool) or not isinstance(
        payload["stress_sign"], int
    ):
        raise InputBundleError(f"external component {position}.stress_sign is invalid")
    for name in (
        "name",
        "observation_role",
        "reference_role",
        "normalization",
        "normalization_id",
        "source_system",
        "source_owner",
    ):
        payload[name] = _nonempty_string(
            payload[name], f"external component {position}.contract.{name}"
        )
    payload["reference_floor"] = _finite_number(
        payload["reference_floor"],
        f"external component {position}.contract.reference_floor",
    )
    if payload["fixed_scale"] is not None:
        payload["fixed_scale"] = _finite_number(
            payload["fixed_scale"],
            f"external component {position}.contract.fixed_scale",
        )
    try:
        channel = ExternalDisplacementChannel(**payload)
        channel.validate()
    except (TypeError, ValueError) as exc:
        raise InputBundleError(f"external component {position}.contract is invalid") from exc
    return channel


def _operator_contract(value: object) -> OperatorRepresentationContract:
    required = {field.name for field in fields(OperatorRepresentationContract)}
    payload = _closed_mapping(value, required, "operator_representation.contract")
    if not isinstance(payload["prama_variables_used"], list) or any(
        not isinstance(item, str) for item in payload["prama_variables_used"]
    ):
        raise InputBundleError("operator prama_variables_used must be a string list")
    if not isinstance(payload["available_by_t"], bool) or not isinstance(
        payload["generated_independently_from_prama"], bool
    ):
        raise InputBundleError("operator causality guards must be boolean")
    for name in (
        "source_system",
        "source_owner",
        "channel_role",
        "normalization_id",
        "units",
        "coupled_operational_parameter",
        "representation_target",
    ):
        payload[name] = _nonempty_string(
            payload[name], f"operator_representation.contract.{name}"
        )
    payload["prama_variables_used"] = tuple(payload["prama_variables_used"])
    try:
        contract = OperatorRepresentationContract(**payload)
        contract.validate()
    except (TypeError, ValueError) as exc:
        raise InputBundleError("operator_representation.contract is invalid") from exc
    return contract


def load_assessment_bundle(path: str | Path) -> LoadedAssessmentBundle:
    """Load a closed two-file bundle and realize all source contracts."""

    bundle = Path(path).resolve()
    if not bundle.is_dir():
        raise InputBundleError("bundle path must be a directory")
    manifest_path = bundle / MANIFEST_FILE
    if (
        not manifest_path.is_file()
        or manifest_path.resolve().parent != bundle
        or manifest_path.is_symlink()
    ):
        raise InputBundleError("bundle must contain manifest.json")
    manifest, manifest_bytes = _load_manifest(manifest_path)
    root = _closed_mapping(
        manifest,
        {
            "schema_version",
            "assessment_id",
            "data_file",
            "timestamp_column",
            "core_columns",
            "telemetry",
            "external_displacement",
            "operator_representation",
            "kernel_config",
        },
        "manifest",
    )
    if root["schema_version"] != SCHEMA_VERSION:
        raise InputBundleError("unsupported input-bundle schema_version")
    assessment_id = _nonempty_string(root["assessment_id"], "assessment_id")
    if not ASSESSMENT_ID.fullmatch(assessment_id):
        raise InputBundleError("assessment_id must be a portable identifier")
    data_file = _nonempty_string(root["data_file"], "data_file")
    if Path(data_file).name != data_file or not data_file.lower().endswith(".csv"):
        raise InputBundleError("data_file must be one local CSV filename")
    data_path = (bundle / data_file).resolve()
    if data_path.parent != bundle or not data_path.is_file() or data_path.is_symlink():
        raise InputBundleError("declared data_file is missing or escapes the bundle")
    expected_entries = {MANIFEST_FILE, data_file}
    extra_entries = sorted(
        entry.name for entry in bundle.iterdir() if entry.name not in expected_entries
    )
    if extra_entries:
        raise InputBundleError(
            f"input bundle must remain an immutable two-file package: extra={extra_entries}"
        )
    timestamp_column = _column_name(root["timestamp_column"], "timestamp_column")
    core = _closed_mapping(root["core_columns"], CORE_ROLES, "core_columns")
    core_columns = {
        role: _column_name(column, f"core_columns.{role}")
        for role, column in core.items()
    }

    telemetry = _closed_mapping(
        root["telemetry"], {"source_valid_columns", "contract"}, "telemetry"
    )
    source_columns_raw = telemetry["source_valid_columns"]
    if not isinstance(source_columns_raw, list) or not source_columns_raw:
        raise InputBundleError("telemetry.source_valid_columns must be a nonempty list")
    source_columns = [
        _column_name(value, f"telemetry.source_valid_columns[{row}]")
        for row, value in enumerate(source_columns_raw)
    ]
    if len(set(source_columns)) != len(source_columns):
        raise InputBundleError("telemetry source-valid columns must be unique")
    telemetric_contract = _telemetric_contract(telemetry["contract"])

    external = _closed_mapping(
        root["external_displacement"], {"components"}, "external_displacement"
    )
    component_records = external["components"]
    if not isinstance(component_records, list) or not component_records:
        raise InputBundleError("external displacement must declare components")
    channels: list[ExternalDisplacementChannel] = []
    external_columns: list[dict[str, str]] = []
    for position, value in enumerate(component_records):
        record = _closed_mapping(
            value, {"contract", "columns"}, f"external component {position}"
        )
        channels.append(_channel_contract(record["contract"], position))
        columns = _closed_mapping(
            record["columns"],
            {"observation", "reference", "valid", "reference_issued_at"},
            f"external component {position}.columns",
        )
        external_columns.append(
            {
                role: _column_name(
                    column, f"external component {position}.columns.{role}"
                )
                for role, column in columns.items()
            }
        )
    if len({channel.name for channel in channels}) != len(channels):
        raise InputBundleError("external component names must be unique")

    operator = _closed_mapping(
        root["operator_representation"],
        {"contract", "columns"},
        "operator_representation",
    )
    operator_contract = _operator_contract(operator["contract"])
    operator_columns_raw = _closed_mapping(
        operator["columns"],
        {"value", "valid", "issued_at"},
        "operator_representation.columns",
    )
    operator_columns = {
        role: _column_name(column, f"operator_representation.columns.{role}")
        for role, column in operator_columns_raw.items()
    }
    kernel_config = _validate_kernel_config(root["kernel_config"])

    declared_columns = [timestamp_column, *core_columns.values(), *source_columns]
    for columns in external_columns:
        declared_columns.extend(columns.values())
    declared_columns.extend(operator_columns.values())
    if len(set(declared_columns)) != len(declared_columns):
        raise InputBundleError("every declared column must have exactly one role")

    try:
        data_bytes = data_path.read_bytes()
        data_text = data_bytes.decode("utf-8-sig")
        header = next(csv.reader(io.StringIO(data_text)))
    except (OSError, UnicodeDecodeError, StopIteration, csv.Error) as exc:
        raise InputBundleError("data_file is not a readable UTF-8 CSV") from exc
    if not header or any(not name for name in header) or len(set(header)) != len(header):
        raise InputBundleError("CSV header must be nonempty and unique")
    if set(header) != set(declared_columns):
        missing = sorted(set(declared_columns) - set(header))
        undeclared = sorted(set(header) - set(declared_columns))
        raise InputBundleError(
            f"CSV columns differ from manifest: missing={missing}, undeclared={undeclared}"
        )
    try:
        frame = pd.read_csv(io.StringIO(data_text), low_memory=False)
    except Exception as exc:
        raise InputBundleError("data_file cannot be parsed as CSV") from exc
    if frame.empty:
        raise InputBundleError("data_file must contain at least one row")

    index = _datetime_vector(frame[timestamp_column], timestamp_column)
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise InputBundleError("timestamps must be unique and increasing")
    if len(index) > 1:
        expected_cadence = pd.Timedelta(hours=telemetric_contract.cadence_hours)
        if not bool(np.all((index[1:] - index[:-1]) == expected_cadence)):
            raise InputBundleError("timestamps must form the declared complete cadence")

    omega = _numeric_vector(frame[core_columns["omega"]], "omega", require_finite=True)
    expected = _numeric_vector(
        frame[core_columns["expected"]], "expected", require_finite=True
    )
    sigma_op, _ = _boolean_vector(
        frame[core_columns["sigma_op"]], "sigma_op", reject_unrecognized=True
    )
    u_lambda = _numeric_vector(
        frame[core_columns["u_lambda"]], "u_lambda", require_finite=True
    )
    if np.any(u_lambda < 0.0):
        raise InputBundleError("u_lambda must be nonnegative")
    effective_flow = _numeric_vector(
        frame[core_columns["effective_flow"]],
        "effective_flow",
        require_finite=True,
    )
    planned, _ = _boolean_vector(
        frame[core_columns["planned"]], "planned", reject_unrecognized=True
    )
    phi_register = _numeric_vector(
        frame[core_columns["phi_register"]],
        "phi_register",
        require_finite=True,
    )

    observations: dict[str, np.ndarray] = {}
    references: dict[str, np.ndarray] = {}
    source_valid: dict[str, np.ndarray] = {}
    issue_times: dict[str, pd.DatetimeIndex] = {}
    quarantined_boolean_tokens: dict[str, int] = {}
    for channel, columns in zip(channels, external_columns, strict=True):
        observations[channel.name] = _numeric_vector(
            frame[columns["observation"]],
            f"{channel.name}.observation",
            require_finite=False,
        )
        references[channel.name] = _numeric_vector(
            frame[columns["reference"]],
            f"{channel.name}.reference",
            require_finite=False,
        )
        valid, invalid_tokens = _boolean_vector(
            frame[columns["valid"]],
            f"{channel.name}.valid",
            reject_unrecognized=False,
        )
        source_valid[channel.name] = valid
        quarantined_boolean_tokens[f"external:{channel.name}"] = invalid_tokens
        issue_times[channel.name] = _datetime_vector(
            frame[columns["reference_issued_at"]],
            f"{channel.name}.reference_issued_at",
        )
    displacement = realize_external_displacement(
        index, channels, observations, references, source_valid, issue_times
    )
    if not displacement.complete:
        raise InputBundleError("external displacement contract is incomplete")

    operator_values = _numeric_vector(
        frame[operator_columns["value"]], "operator_R.value", require_finite=False
    )
    operator_valid, invalid_operator_tokens = _boolean_vector(
        frame[operator_columns["valid"]],
        "operator_R.valid",
        reject_unrecognized=False,
    )
    quarantined_boolean_tokens["operator_R"] = invalid_operator_tokens
    operator_issue = _datetime_vector(
        frame[operator_columns["issued_at"]], "operator_R.issued_at"
    )
    representation = validate_operator_representation(
        index,
        operator_values,
        operator_valid,
        operator_issue,
        operator_contract,
    )
    if not representation.contract["complete"]:
        raise InputBundleError("operator representation contract is incomplete")

    telemetry_frame = frame[
        [timestamp_column, core_columns["q"], *source_columns]
    ].copy()
    telemetry_frame[timestamp_column] = index
    bundle_digest = hashlib.sha256()
    bundle_digest.update(SCHEMA_VERSION.encode("utf-8"))
    bundle_digest.update(b"\x00")
    bundle_digest.update(manifest_bytes)
    bundle_digest.update(b"\x00")
    bundle_digest.update(data_bytes)
    input_binding = {
        "kind": "file_bundle",
        "verified": True,
        "schema_version": SCHEMA_VERSION,
        "assessment_id": assessment_id,
        "manifest_file": MANIFEST_FILE,
        "manifest_sha256": _sha256_bytes(manifest_bytes),
        "data_file": data_file,
        "data_sha256": _sha256_bytes(data_bytes),
        "bundle_sha256": bundle_digest.hexdigest(),
        "rows": int(len(frame)),
        "start_utc": index[0].isoformat().replace("+00:00", "Z"),
        "stop_utc": index[-1].isoformat().replace("+00:00", "Z"),
        "declared_column_count": len(declared_columns),
        "undeclared_columns_accessed": False,
        "outcome_roles_declared": False,
        "outcome_columns_accessed": False,
        "quarantined_boolean_tokens": quarantined_boolean_tokens,
        "manifest": root,
    }
    return LoadedAssessmentBundle(
        inputs=AssessmentInputs(
            index=index,
            omega=omega,
            expected=expected,
            sigma_op=sigma_op,
            u_lambda=u_lambda,
            effective_flow=effective_flow,
            planned=planned,
            telemetry=telemetry_frame,
            telemetry_timestamp_column=timestamp_column,
            telemetry_q_column=core_columns["q"],
            telemetry_valid_columns=tuple(source_columns),
            displacement=displacement,
            phi_register=phi_register,
            external_cause_labels=None,
            external_cause_labels_independent=None,
            operator_representation=representation,
        ),
        telemetric_contract=telemetric_contract,
        kernel_config=kernel_config,
        input_binding=input_binding,
    )


def canonical_manifest(payload: Mapping[str, Any]) -> bytes:
    """Serialize a manifest deterministically for producers and fixtures."""

    return (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def contract_dict(value: object) -> dict[str, Any]:
    """Return a JSON-ready dataclass contract without changing its semantics."""

    payload = asdict(value)
    for key, item in list(payload.items()):
        if isinstance(item, tuple):
            payload[key] = list(item)
    return payload
