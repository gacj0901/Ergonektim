"""Deterministic circular-shift reference for Condition Report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any

import numpy as np
import pandas as pd

from ..observers import condition_report


class ConditionNullContractError(ValueError):
    """Raised when a Condition Report reference contract is malformed."""


@dataclass(frozen=True)
class ConditionNullDesign:
    """Pre-registered geometry and decision rule for the reference set."""

    pre_window: int = 6
    post_window: int = 6
    memory_exclusion_rows: int = 336
    minimum_eligibility_fraction: float = 0.90
    minimum_reference_shifts: int = 1000
    upper_tail_probability_maximum: float = 0.05
    minimum_effect: float = 0.05
    cadence_hours: float = 1.0

    def validate(self) -> None:
        integer_fields = {
            "pre_window": self.pre_window,
            "post_window": self.post_window,
            "memory_exclusion_rows": self.memory_exclusion_rows,
            "minimum_reference_shifts": self.minimum_reference_shifts,
        }
        for name, value in integer_fields.items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise ConditionNullContractError(f"{name} must be an integer")
        if self.pre_window < 1 or self.post_window < 1:
            raise ConditionNullContractError("analysis windows must be positive")
        if self.memory_exclusion_rows < 0:
            raise ConditionNullContractError(
                "memory_exclusion_rows must be nonnegative"
            )
        if self.minimum_reference_shifts < 1:
            raise ConditionNullContractError(
                "minimum_reference_shifts must be positive"
            )
        fractions = {
            "minimum_eligibility_fraction": self.minimum_eligibility_fraction,
            "upper_tail_probability_maximum": (
                self.upper_tail_probability_maximum
            ),
        }
        for name, value in fractions.items():
            if not math.isfinite(float(value)) or not 0.0 < float(value) <= 1.0:
                raise ConditionNullContractError(f"{name} must be in (0,1]")
        if not math.isfinite(float(self.minimum_effect)) or self.minimum_effect < 0:
            raise ConditionNullContractError(
                "minimum_effect must be finite and nonnegative"
            )
        if not math.isfinite(float(self.cadence_hours)) or self.cadence_hours <= 0:
            raise ConditionNullContractError(
                "cadence_hours must be positive and finite"
            )


def _episodes(plan: np.ndarray) -> list[tuple[int, int]]:
    padded = np.r_[False, plan, False].astype(np.int8)
    starts = np.flatnonzero(np.diff(padded) == 1)
    stops = np.flatnonzero(np.diff(padded) == -1)
    return list(zip(starts.tolist(), stops.tolist(), strict=True))


def _hash_array(values: np.ndarray) -> str:
    canonical = np.ascontiguousarray(values)
    return hashlib.sha256(canonical.tobytes(order="C")).hexdigest()


def _design_hash(design: ConditionNullDesign) -> str:
    payload = json.dumps(
        asdict(design), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _index_hash(index: pd.DatetimeIndex) -> str:
    payload = json.dumps(
        [timestamp.isoformat() for timestamp in index],
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _indeterminate(
    *,
    reason: str,
    design: ConditionNullDesign,
    rows: int,
    planned_rows: int,
    episode_count: int,
    eligible_episode_count: int,
    timeline_sha256: str,
    planned_sha256: str,
    margin_sha256: str,
    clear_sha256: str,
    rejected_shift_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "ergonektim.condition-null.v1",
        "status": "instrument_indeterminate",
        "reason": reason,
        "decision": "no_empirical_claim",
        "design": asdict(design),
        "design_sha256": _design_hash(design),
        "custody": {
            "rows": rows,
            "planned_rows": planned_rows,
            "planned_episode_count": episode_count,
            "eligible_observed_episode_count": eligible_episode_count,
            "timeline_sha256": timeline_sha256,
            "planned_sha256": planned_sha256,
            "margin_sha256": margin_sha256,
            "observability_clear_sha256": clear_sha256,
        },
        "reference": {
            "kind": "restricted_exhaustive_circular_shift",
            "admissible_shift_count": 0,
            "rejected_shift_counts": dict(
                sorted((rejected_shift_counts or {}).items())
            ),
            "restricted_shift_tail_probability": None,
            "exact_unrestricted_permutation_p_value_claimed": False,
        },
        "kernel_modified": False,
        "outcomes_accessed": False,
    }


def circular_shift_condition_reference(
    index: pd.DatetimeIndex,
    planned: object,
    margin: object,
    observability_clear: object,
    *,
    design: ConditionNullDesign = ConditionNullDesign(),
) -> dict[str, Any]:
    """Compare the observed regenerative fraction with admissible rotations.

    The complete planned-indicator path is rotated, never freely shuffled.
    Every admissible shift is evaluated by the same ``condition_report``
    instrument. The reported tail area belongs only to the declared restricted
    reference set; it is not an exact unrestricted permutation p-value.
    """

    design.validate()
    timeline = pd.DatetimeIndex(index)
    plan = np.asarray(planned, dtype=np.bool_)
    m = np.asarray(margin, dtype=np.float64)
    clear = np.asarray(observability_clear, dtype=np.bool_)
    n = len(timeline)
    if (
        n == 0
        or plan.ndim != 1
        or m.ndim != 1
        or clear.ndim != 1
        or not (plan.size == m.size == clear.size == n)
    ):
        raise ConditionNullContractError(
            "index, planned, margin, and observability must be aligned "
            "nonempty vectors"
        )
    if (
        timeline.tz is None
        or timeline.has_duplicates
        or not timeline.is_monotonic_increasing
    ):
        raise ConditionNullContractError(
            "index must be timezone-aware, unique, and increasing"
        )
    if not np.isfinite(m).all():
        raise ConditionNullContractError("margin must be finite")
    if n > 1:
        expected_step = pd.Timedelta(hours=float(design.cadence_hours))
        observed_steps = timeline[1:] - timeline[:-1]
        if not bool(np.all(observed_steps == expected_step)):
            raise ConditionNullContractError(
                "index does not satisfy the pre-registered regular cadence"
            )

    original_episodes = _episodes(plan)
    original_durations = sorted(stop - start for start, stop in original_episodes)
    planned_sha = _hash_array(plan.astype(np.uint8))
    timeline_sha = _index_hash(timeline)
    margin_sha = _hash_array(m.astype("<f8", copy=False))
    clear_sha = _hash_array(clear.astype(np.uint8))
    observed = condition_report(
        timeline,
        plan,
        m,
        clear,
        pre_window=design.pre_window,
        post_window=design.post_window,
    )
    observed_eligible = [
        episode for episode in observed["episodes"] if bool(episode["eligible"])
    ]
    base = {
        "design": design,
        "rows": n,
        "planned_rows": int(plan.sum()),
        "episode_count": len(original_episodes),
        "eligible_episode_count": len(observed_eligible),
        "timeline_sha256": timeline_sha,
        "planned_sha256": planned_sha,
        "margin_sha256": margin_sha,
        "clear_sha256": clear_sha,
    }
    if not original_episodes:
        return _indeterminate(reason="no_planned_episodes", **base)
    if not observed_eligible:
        return _indeterminate(reason="no_eligible_observed_episodes", **base)

    observed_regenerative = sum(
        episode["status"] == "regenerative" for episode in observed_eligible
    )
    observed_fraction = observed_regenerative / len(observed_eligible)
    minimum_eligible = max(
        1,
        math.ceil(
            len(observed_eligible) * float(design.minimum_eligibility_fraction)
        ),
    )
    rejected: dict[str, int] = {
        "memory_exclusion": 0,
        "episode_geometry_changed": 0,
        "insufficient_eligible_episodes": 0,
    }
    accepted_shifts: list[int] = []
    reference_fractions: list[float] = []
    reference_eligible_counts: list[int] = []

    for shift in range(1, n):
        circular_distance = min(shift, n - shift)
        if circular_distance <= design.memory_exclusion_rows:
            rejected["memory_exclusion"] += 1
            continue
        shifted = np.roll(plan, shift)
        shifted_episodes = _episodes(shifted)
        shifted_durations = sorted(
            stop - start for start, stop in shifted_episodes
        )
        if (
            len(shifted_episodes) != len(original_episodes)
            or shifted_durations != original_durations
            or int(shifted.sum()) != int(plan.sum())
        ):
            rejected["episode_geometry_changed"] += 1
            continue
        result = condition_report(
            timeline,
            shifted,
            m,
            clear,
            pre_window=design.pre_window,
            post_window=design.post_window,
        )
        eligible = [
            episode for episode in result["episodes"] if bool(episode["eligible"])
        ]
        if len(eligible) < minimum_eligible:
            rejected["insufficient_eligible_episodes"] += 1
            continue
        regenerative = sum(
            episode["status"] == "regenerative" for episode in eligible
        )
        accepted_shifts.append(shift)
        reference_eligible_counts.append(len(eligible))
        reference_fractions.append(regenerative / len(eligible))

    if not accepted_shifts:
        return _indeterminate(
            reason="no_admissible_reference_shifts",
            rejected_shift_counts=rejected,
            **base,
        )
    if len(accepted_shifts) < design.minimum_reference_shifts:
        record = _indeterminate(
            reason="insufficient_admissible_reference_shifts",
            rejected_shift_counts=rejected,
            **base,
        )
        record["reference"]["admissible_shift_count"] = len(accepted_shifts)
        record["reference"]["admissible_shifts_sha256"] = _hash_array(
            np.asarray(accepted_shifts, dtype="<i8")
        )
        return record

    reference = np.asarray(reference_fractions, dtype=np.float64)
    upper_tail = (1 + int(np.sum(reference >= observed_fraction))) / (
        1 + reference.size
    )
    quantiles = {
        key: float(np.quantile(reference, probability))
        for key, probability in (
            ("q05", 0.05),
            ("q50", 0.50),
            ("q95", 0.95),
        )
    }
    effect = observed_fraction - quantiles["q50"]
    distinguished = bool(
        upper_tail <= design.upper_tail_probability_maximum
        and effect >= design.minimum_effect
    )
    return {
        "schema_version": "ergonektim.condition-null.v1",
        "status": "measured",
        "decision": (
            "regenerative_fraction_distinguished"
            if distinguished
            else "regenerative_fraction_not_distinguished"
        ),
        "design": asdict(design),
        "design_sha256": _design_hash(design),
        "custody": {
            "rows": n,
            "planned_rows": int(plan.sum()),
            "planned_episode_count": len(original_episodes),
            "eligible_observed_episode_count": len(observed_eligible),
            "timeline_sha256": timeline_sha,
            "planned_sha256": planned_sha,
            "margin_sha256": margin_sha,
            "observability_clear_sha256": clear_sha,
        },
        "observed": {
            "regenerative_episode_count": int(observed_regenerative),
            "eligible_episode_count": len(observed_eligible),
            "regenerative_fraction": float(observed_fraction),
        },
        "reference": {
            "kind": "restricted_exhaustive_circular_shift",
            "admissible_shift_count": len(accepted_shifts),
            "admissible_shifts_sha256": _hash_array(
                np.asarray(accepted_shifts, dtype="<i8")
            ),
            "reference_fractions_sha256": _hash_array(
                reference.astype("<f8", copy=False)
            ),
            "eligible_episode_count_minimum": int(
                min(reference_eligible_counts)
            ),
            "eligible_episode_count_maximum": int(
                max(reference_eligible_counts)
            ),
            "rejected_shift_counts": dict(sorted(rejected.items())),
            "quantiles": quantiles,
            "restricted_shift_tail_probability": float(upper_tail),
            "exact_unrestricted_permutation_p_value_claimed": False,
        },
        "null_effect": float(effect),
        "kernel_modified": False,
        "outcomes_accessed": False,
        "invariants": {
            "complete_indicator_shifted": True,
            "free_shuffle_absent": True,
            "episode_count_and_durations_preserved": True,
            "same_condition_instrument_reused": True,
            "identity_shift_excluded": True,
            "memory_exclusion_respected": bool(
                all(
                    min(shift, n - shift) > design.memory_exclusion_rows
                    for shift in accepted_shifts
                )
            ),
            "decision_thresholds_predeclared": True,
            "unrestricted_permutation_claim_absent": True,
        },
    }
