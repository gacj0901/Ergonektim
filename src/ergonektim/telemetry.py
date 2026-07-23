"""Fail-closed telemetric observability observer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

import numpy as np
import pandas as pd

from ._strict import StrictTypeError, strict_boolean_vector


SCHEMA = "ergonektim.observer.telemetric-status.v1"
CLEAR = "observability_clear"
INDETERMINATE = "instrument_indeterminate"
PARTIAL = "partially_observable_fail_closed"


class TelemetricStatusError(ValueError):
    """Raised when telemetry violates its declared observation contract."""


@dataclass(frozen=True)
class TelemetricContract:
    cadence_hours: int = 1
    g_per_step: float = 1.0 / 6.0
    eta: float = 2.610497237569061
    q_max: float = 1.0
    tol_s: float = math.exp(-3.0)
    initial_state: float = 1.0
    missingness_bias_direction: str = "two_sided"
    q_normalization_id: str = ""

    def validate(self) -> None:
        if self.cadence_hours < 1:
            raise TelemetricStatusError("cadence_hours must be positive")
        if not 0.0 < self.g_per_step <= 1.0:
            raise TelemetricStatusError("g_per_step must lie in (0,1]")
        if not math.isfinite(self.eta) or self.eta < 0.0:
            raise TelemetricStatusError("eta must be finite and nonnegative")
        if not math.isfinite(self.q_max) or self.q_max <= 0.0:
            raise TelemetricStatusError("q_max must be finite and positive")
        if not 0.0 < self.tol_s < 1.0:
            raise TelemetricStatusError("tol_s must lie in (0,1)")
        if not 0.0 <= self.initial_state <= 1.0:
            raise TelemetricStatusError("initial_state must lie in [0,1]")
        if self.missingness_bias_direction not in {
            "optimistic",
            "pessimistic",
            "two_sided",
            "unknown",
        }:
            raise TelemetricStatusError("unsupported missingness bias direction")
        if not self.q_normalization_id.strip():
            raise TelemetricStatusError("q_normalization_id must be declared")


@dataclass(frozen=True)
class TelemetricStatusResult:
    report: dict[str, Any]
    timeline: pd.DataFrame


def _strict_boolean(series: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    true_tokens = {"1", "true", "t", "yes", "y", "si", "sí"}
    false_tokens = {"0", "false", "f", "no", "n"}
    values = np.zeros(len(series), dtype=np.bool_)
    recognized = np.zeros(len(series), dtype=np.bool_)
    for position, value in enumerate(series.to_numpy(dtype=object)):
        if isinstance(value, (bool, np.bool_)):
            values[position] = bool(value)
            recognized[position] = True
        elif isinstance(value, (int, np.integer, float, np.floating)):
            if math.isfinite(float(value)) and float(value) in (0.0, 1.0):
                values[position] = bool(value)
                recognized[position] = True
        elif isinstance(value, str):
            token = value.strip().lower()
            if token in true_tokens:
                values[position] = True
                recognized[position] = True
            elif token in false_tokens:
                recognized[position] = True
    return values, recognized


def propagate_causal_interval(
    q: object,
    source_valid: object,
    contract: TelemetricContract,
) -> dict[str, np.ndarray]:
    """Propagate lower and upper reserve-state bounds through missing rows."""

    contract.validate()
    drain = np.asarray(q, dtype=np.float64)
    if drain.ndim != 1 or drain.size == 0:
        raise TelemetricStatusError("q and source_valid must be aligned vectors")
    try:
        valid = strict_boolean_vector(
            source_valid, name="source_valid", expected_length=drain.size
        )
    except StrictTypeError as exc:
        raise TelemetricStatusError(str(exc)) from exc

    lower = np.empty(drain.size, dtype=np.float64)
    upper = np.empty(drain.size, dtype=np.float64)
    previous_lower = contract.initial_state
    previous_upper = contract.initial_state
    for position in range(drain.size):
        lower_regeneration = contract.g_per_step * (1.0 - previous_lower)
        upper_regeneration = contract.g_per_step * (1.0 - previous_upper)
        if valid[position]:
            observed = float(drain[position])
            if not math.isfinite(observed) or not 0.0 <= observed <= contract.q_max:
                raise TelemetricStatusError("valid q must lie in [0,q_max]")
            next_lower = previous_lower + lower_regeneration - contract.eta * observed
            next_upper = previous_upper + upper_regeneration - contract.eta * observed
        else:
            next_lower = (
                previous_lower
                + lower_regeneration
                - contract.eta * contract.q_max
            )
            next_upper = previous_upper + upper_regeneration
        previous_lower = float(np.clip(next_lower, 0.0, 1.0))
        previous_upper = float(np.clip(next_upper, 0.0, 1.0))
        lower[position] = min(previous_lower, previous_upper)
        upper[position] = max(previous_lower, previous_upper)
    width = upper - lower
    clear = valid & (width <= contract.tol_s)
    return {"lower": lower, "upper": upper, "width": width, "clear": clear}


def _zones(clear: np.ndarray, index: pd.DatetimeIndex) -> list[dict[str, Any]]:
    padded = np.r_[False, ~clear, False].astype(np.int8)
    starts = np.flatnonzero(np.diff(padded) == 1)
    stops = np.flatnonzero(np.diff(padded) == -1)
    cadence = index[1] - index[0] if len(index) > 1 else pd.Timedelta(hours=1)
    return [
        {
            "start_utc": index[start].isoformat().replace("+00:00", "Z"),
            "stop_exclusive_utc": (index[stop - 1] + cadence)
            .isoformat()
            .replace("+00:00", "Z"),
            "length_rows": int(stop - start),
        }
        for start, stop in zip(starts, stops, strict=True)
    ]


def audit_telemetry_frame(
    frame: pd.DataFrame,
    *,
    timestamp_column: str,
    q_column: str,
    source_valid_columns: list[str],
    contract: TelemetricContract,
) -> TelemetricStatusResult:
    """Place telemetry on a canonical UTC grid and emit a causal clear mask."""

    contract.validate()
    required = {timestamp_column, q_column, *source_valid_columns}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise TelemetricStatusError(f"missing input columns: {missing}")
    if frame.empty or not source_valid_columns:
        raise TelemetricStatusError("telemetry and source list must be nonempty")

    raw = frame.loc[:, list(required)].copy()
    parsed = pd.to_datetime(raw[timestamp_column], errors="coerce", utc=True)
    malformed = parsed.isna().to_numpy(dtype=np.bool_)
    if malformed.all():
        raise TelemetricStatusError("no timestamp can be placed on the UTC grid")
    cadence = pd.Timedelta(hours=contract.cadence_hours)
    floored = parsed.dt.floor(cadence)
    off_grid = (parsed.notna() & (parsed != floored)).to_numpy(dtype=np.bool_)
    aligned = ~malformed & ~off_grid
    duplicate = np.zeros(len(raw), dtype=np.bool_)
    duplicate[aligned] = parsed[aligned].duplicated(keep=False).to_numpy(dtype=np.bool_)
    usable = aligned & ~duplicate

    valid_parsed = parsed[~malformed]
    start = valid_parsed.min().floor(cadence)
    stop = valid_parsed.max().floor(cadence)
    index = pd.date_range(start, stop, freq=cadence, tz="UTC")
    placed = raw.loc[usable].copy()
    placed.index = pd.DatetimeIndex(parsed[usable])
    placed = placed.drop(columns=[timestamp_column]).reindex(index)

    present = index.isin(pd.DatetimeIndex(parsed[usable]))
    duplicate_hours = index.isin(pd.DatetimeIndex(floored[duplicate].dropna().unique()))
    off_grid_hours = index.isin(pd.DatetimeIndex(floored[off_grid].dropna().unique()))
    geometry_valid = present & ~duplicate_hours & ~off_grid_hours
    q = pd.to_numeric(placed[q_column], errors="coerce").to_numpy(dtype=np.float64)
    q_valid = np.isfinite(q) & (q >= 0.0) & (q <= contract.q_max)

    source_masks: dict[str, np.ndarray] = {}
    unrecognized: dict[str, int] = {}
    for column in source_valid_columns:
        values, recognized = _strict_boolean(placed[column])
        source_masks[column] = values & recognized & geometry_valid
        unrecognized[column] = int((geometry_valid & ~recognized).sum())

    joint_valid = geometry_valid & q_valid
    for mask in source_masks.values():
        joint_valid &= mask
    interval = propagate_causal_interval(q, joint_valid, contract)
    clear = interval["clear"]

    reasons: list[str] = []
    for position in range(len(index)):
        row_reasons = []
        if not geometry_valid[position]:
            row_reasons.append("timestamp_geometry_invalid")
        if geometry_valid[position] and not q_valid[position]:
            row_reasons.append("q_missing_or_out_of_range")
        for name, mask in source_masks.items():
            if geometry_valid[position] and not mask[position]:
                row_reasons.append(f"source_invalid:{name}")
        if joint_valid[position] and not clear[position]:
            row_reasons.append("causal_memory_interval")
        reasons.append("|".join(row_reasons))

    timeline = pd.DataFrame(
        {
            "timestamp_utc": index.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "q": q,
            **{f"valid__{name}": mask for name, mask in source_masks.items()},
            "joint_source_valid": joint_valid,
            "s_lower": interval["lower"],
            "s_upper": interval["upper"],
            "interval_width": interval["width"],
            "observability_clear": clear,
            "telemetric_status": np.where(clear, CLEAR, INDETERMINATE),
            "quarantine_reasons": reasons,
        }
    )

    checks = {
        "finite_bounds": bool(
            np.isfinite(interval["lower"]).all()
            and np.isfinite(interval["upper"]).all()
        ),
        "ordered_bounds": bool(np.all(interval["lower"] <= interval["upper"])),
        "bounds_inside_unit_interval": bool(
            np.all((interval["lower"] >= 0.0) & (interval["upper"] <= 1.0))
        ),
        "invalid_rows_never_clear": bool(not np.any(clear & ~joint_valid)),
        "clear_rows_respect_tol_s": bool(
            np.all(interval["width"][clear] <= contract.tol_s)
        ),
    }
    if not all(checks.values()):
        raise RuntimeError("Telemetric Status invariant failure")
    overall = INDETERMINATE if not clear.any() else CLEAR if clear.all() else PARTIAL
    zones = _zones(clear, index)
    report = {
        "schema": SCHEMA,
        "access": {"outcomes_accessed": False, "future_values_accessed": False},
        "contract": asdict(contract),
        "status": overall,
        "coverage": {
            "grid_rows": int(len(index)),
            "joint_source_valid_rows": int(joint_valid.sum()),
            "direct_invalid_rows": int((~joint_valid).sum()),
            "causal_memory_only_excluded_rows": int((joint_valid & ~clear).sum()),
            "observability_clear_rows": int(clear.sum()),
            "instrument_indeterminate_rows": int((~clear).sum()),
            "observability_clear_fraction": float(np.mean(clear)),
            "unrecognized_validity_tokens": unrecognized,
            "indeterminate_zones": zones,
        },
        "invariants": checks,
        "claim_boundary": {
            "emits_operational_action": False,
            "predicts_future_outages": False,
            "optimizes_grid_dispatch": False,
            "relaxes_masks_to_gain_coverage": False,
        },
    }
    return TelemetricStatusResult(report=report, timeline=timeline)
