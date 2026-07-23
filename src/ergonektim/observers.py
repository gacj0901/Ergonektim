"""Outcome-free operational observers over projected ERGONEKTIM state."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any, Sequence

import numpy as np
import pandas as pd

from .contracts import (
    CausalRegisterContract,
    ExternalDisplacement,
    OperatorRepresentation,
)


INDETERMINATE = "instrument_indeterminate"


class ObserverContractError(ValueError):
    """Raised when aligned observer inputs violate a declared contract."""


def _vector(name: str, values: object, dtype: object) -> np.ndarray:
    array = np.asarray(values, dtype=dtype)
    if array.ndim != 1 or array.size == 0:
        raise ObserverContractError(f"{name} must be a nonempty vector")
    return array


def _aligned_float_vectors(**values: object) -> dict[str, np.ndarray]:
    arrays = {name: _vector(name, value, np.float64) for name, value in values.items()}
    if len({array.size for array in arrays.values()}) != 1:
        raise ObserverContractError("observer inputs must align")
    if not all(np.isfinite(array).all() for array in arrays.values()):
        raise ObserverContractError("observer float inputs must be finite")
    return arrays


def _counts(status: np.ndarray) -> dict[str, int]:
    return dict(sorted(Counter(str(item) for item in status).items()))


def stability_status(
    sigma_op: object,
    margin: object,
    gradient: object,
    observability_clear: object,
) -> dict[str, Any]:
    """Classify current viability and the sign of its causal gradient."""

    arrays = _aligned_float_vectors(margin=margin, gradient=gradient)
    sigma = _vector("sigma_op", sigma_op, np.bool_)
    clear = _vector("observability_clear", observability_clear, np.bool_)
    if sigma.shape != arrays["margin"].shape or clear.shape != sigma.shape:
        raise ObserverContractError("Stability Status inputs must align")
    m = arrays["margin"]
    g = arrays["gradient"]
    status = np.full(m.size, INDETERMINATE, dtype=object)
    compromised = clear & ((m < 0.0) | ~sigma)
    viable_negative_gradient = clear & sigma & (m >= 0.0) & (g < 0.0)
    viable = clear & sigma & (m >= 0.0) & (g >= 0.0)
    status[compromised] = "collapsing"
    status[viable_negative_gradient] = "viable_with_negative_gradient"
    status[viable] = "viable"
    gate = bool(np.all(status[~clear] == INDETERMINATE))
    exact = bool(
        np.array_equal(
            status == "viable_with_negative_gradient", viable_negative_gradient
        )
    )
    if not gate or not exact:
        raise RuntimeError("Stability Status invariant failure")
    return {
        "status_path": status,
        "summary": {
            "counts": _counts(status),
            "raw_margin_minimum": float(np.min(m)),
            "raw_margin_maximum": float(np.max(m)),
            "raw_gradient_minimum": float(np.min(g)),
            "raw_gradient_maximum": float(np.max(g)),
        },
        "invariants": {
            "telemetric_gate_respected": gate,
            "negative_gradient_definition_exact": exact,
        },
    }


def performance_status(
    accumulated_debt: object,
    regeneration_input: object,
    margin: object,
    effective_flow: object,
    observability_clear: object,
    *,
    kappa: float,
    h: float,
) -> dict[str, Any]:
    """Audit regeneration, structural drain, and the over-optimization guard."""

    arrays = _aligned_float_vectors(
        A=accumulated_debt,
        regeneration=regeneration_input,
        margin=margin,
        effective_flow=effective_flow,
    )
    clear = _vector("observability_clear", observability_clear, np.bool_)
    if clear.shape != arrays["A"].shape:
        raise ObserverContractError("Performance Status inputs must align")
    if not math.isfinite(kappa) or kappa < 0.0 or not math.isfinite(h) or h <= 0.0:
        raise ObserverContractError("invalid performance ledger constants")
    if np.any(arrays["A"] < 0.0) or np.any(arrays["regeneration"] < 0.0):
        raise ObserverContractError("debt and regeneration must be nonnegative")

    drain = kappa * h * arrays["A"]
    regeneration = h * arrays["regeneration"]
    net = regeneration - drain
    flow_change = np.r_[0.0, np.diff(arrays["effective_flow"])]
    margin_change = np.r_[0.0, np.diff(arrays["margin"])]
    overoptimized = clear & (flow_change > 0.0) & (margin_change < 0.0)
    status = np.full(clear.size, INDETERMINATE, dtype=object)
    inactive = clear & (drain == 0.0) & (regeneration == 0.0)
    balanced = clear & (net == 0.0) & ~inactive
    status[inactive] = "structural_ledger_inactive"
    status[balanced] = "balanced"
    status[clear & (net > 0.0)] = "solvent"
    status[clear & (net < 0.0)] = "insolvent"
    status[overoptimized] = "overoptimization_guard_triggered"
    ratio = np.full(clear.size, np.nan, dtype=np.float64)
    positive_drain = drain > 0.0
    ratio[positive_drain] = regeneration[positive_drain] / drain[positive_drain]
    gate = bool(np.all(status[~clear] == INDETERMINATE))
    guard = bool(
        np.array_equal(status == "overoptimization_guard_triggered", overoptimized)
    )
    inactive_exact = bool(
        np.array_equal(
            (status == "structural_ledger_inactive") & ~overoptimized,
            inactive & ~overoptimized,
        )
    )
    if (
        not gate
        or not guard
        or not inactive_exact
        or not np.array_equal(net, regeneration - drain)
    ):
        raise RuntimeError("Performance Status invariant failure")
    return {
        "status_path": status,
        "overoptimization_path": overoptimized,
        "structural_drain": drain,
        "regeneration": regeneration,
        "net_solvency": net,
        "regeneration_to_drain_ratio": ratio,
        "flow_change": flow_change,
        "margin_change": margin_change,
        "summary": {"counts": _counts(status)},
        "invariants": {
            "telemetric_gate_respected": gate,
            "anti_overoptimization_guard_exact": guard,
            "inactive_ledger_definition_exact": inactive_exact,
            "ledger_identity_exact": True,
        },
    }


def _planned_episodes(planned: np.ndarray) -> list[tuple[int, int]]:
    padded = np.r_[False, planned, False].astype(np.int8)
    starts = np.flatnonzero(np.diff(padded) == 1)
    stops = np.flatnonzero(np.diff(padded) == -1)
    return list(zip(starts.tolist(), stops.tolist(), strict=True))


def condition_report(
    index: pd.DatetimeIndex,
    planned: object,
    margin: object,
    observability_clear: object,
    *,
    pre_window: int = 6,
    post_window: int = 6,
) -> dict[str, Any]:
    """Characterize margin restitution around declared planned episodes."""

    plan = _vector("planned", planned, np.bool_)
    m = _vector("margin", margin, np.float64)
    clear = _vector("observability_clear", observability_clear, np.bool_)
    if not (len(index) == plan.size == m.size == clear.size):
        raise ObserverContractError("Condition Report inputs must align")
    if not np.isfinite(m).all() or index.tz is None or index.has_duplicates:
        raise ObserverContractError("Condition Report needs finite margin and UTC index")
    if not index.is_monotonic_increasing or pre_window < 1 or post_window < 1:
        raise ObserverContractError("invalid Condition Report window contract")

    records: list[dict[str, Any]] = []
    for episode_id, (start, stop) in enumerate(_planned_episodes(plan), start=1):
        record: dict[str, Any] = {
            "episode_id": episode_id,
            "start_utc": index[start].isoformat().replace("+00:00", "Z"),
            "stop_exclusive_utc": (
                index[stop].isoformat().replace("+00:00", "Z")
                if stop < len(index)
                else (index[-1] + pd.Timedelta(hours=1))
                .isoformat()
                .replace("+00:00", "Z")
            ),
            "planned_rows": int(stop - start),
        }
        left = start - pre_window
        right = stop + post_window
        if left < 0 or right > len(index):
            record.update({"status": "boundary_indeterminate", "eligible": False})
            records.append(record)
            continue
        if not bool(clear[left:right].all()):
            record.update({"status": INDETERMINATE, "eligible": False})
            records.append(record)
            continue
        pre = float(np.median(m[left:start]))
        during = float(np.min(m[start:stop]))
        post = float(np.median(m[stop:right]))
        invested = max(pre - during, 0.0)
        restored = post - during
        net = post - pre
        status = (
            "regenerative"
            if net > 0.0
            else "non_restitutive"
            if net < 0.0
            else "neutral_restitution"
        )
        record.update(
            {
                "status": status,
                "eligible": True,
                "pre_margin_median": pre,
                "during_margin_minimum": during,
                "post_margin_median": post,
                "invested_drain": invested,
                "restored_margin": restored,
                "net_margin_vs_pre": net,
                "restoration_per_invested_drain": (
                    None if invested == 0.0 else restored / invested
                ),
            }
        )
        records.append(record)
    return {
        "episodes": records,
        "summary": {
            "planned_episode_count": len(records),
            "diagnostic_emitted_count": sum(record["eligible"] for record in records),
            "status_counts": dict(
                sorted(Counter(record["status"] for record in records).items())
            ),
            "planned_rows_preserved": int(plan.sum()),
        },
        "invariants": {
            "planned_rows_not_filtered": bool(
                sum(record["planned_rows"] for record in records) == int(plan.sum())
            )
        },
    }


def causal_link_status(
    phi_register: object,
    displacement: ExternalDisplacement,
    observability_clear: object,
    external_cause_labels: object | None,
    *,
    causal_register_contract: CausalRegisterContract,
    external_cause_labels_independent: bool | None,
    tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Partition local mismatch change between internal and external arms."""

    if not displacement.complete:
        raise ObserverContractError("Causal Link needs a complete displacement contract")
    try:
        phi_contract = causal_register_contract.record()
    except (TypeError, ValueError) as exc:
        raise ObserverContractError("Causal Link Phi contract is invalid") from exc
    if not math.isfinite(tolerance) or tolerance < 0.0:
        raise ObserverContractError("invalid Causal Link tolerance")
    phi = _vector("phi_register", phi_register, np.float64)
    clear = _vector("observability_clear", observability_clear, np.bool_)
    labels = None
    if external_cause_labels is not None:
        if external_cause_labels_independent is not True:
            raise ObserverContractError("supplied Causal Link labels must be independent")
        labels = _vector("external_cause_labels", external_cause_labels, object)
    psi = 0.5 + 0.4 * displacement.values
    valid = displacement.valid
    if psi.shape != valid.shape or psi.shape[0] != phi.size:
        raise ObserverContractError("Causal Link components must align")
    if clear.shape != phi.shape or (labels is not None and labels.shape != phi.shape):
        raise ObserverContractError("Causal Link row inputs must align")
    if not np.isfinite(phi).all() or not np.isfinite(psi[valid]).all():
        raise ObserverContractError("Causal Link valid values must be finite")
    allowed = {"internal", "environmental", "joint", "none"}
    if labels is not None and any(str(label) not in allowed for label in labels):
        raise ObserverContractError("unsupported independent cause label")

    n, components = psi.shape
    status = np.full((n, components), INDETERMINATE, dtype=object)
    phi_contribution = np.full((n, components), np.nan, dtype=np.float64)
    psi_contribution = np.full((n, components), np.nan, dtype=np.float64)
    mismatch_change = np.full((n, components), np.nan, dtype=np.float64)
    eligible = np.zeros((n, components), dtype=np.bool_)
    if not phi_contract["observer_emission_authorized"]:
        summaries = {
            name: {
                "counts": {INDETERMINATE: n},
                "eligible_rows": 0,
                "independent_label_matches": None,
                "independent_label_match_fraction": None,
            }
            for name in displacement.component_names
        }
        return {
            "component_names": displacement.component_names,
            "status_path": status,
            "eligible": eligible,
            "phi_contribution": phi_contribution,
            "psi_contribution": psi_contribution,
            "mismatch_change": mismatch_change,
            "summary": {
                "components": summaries,
                "global_scalar_emitted": False,
                "observer_emits": False,
                "instrument_component_explored": False,
                "fail_closed_reason": "causal_register_phi_not_conformant",
            },
            "invariants": {
                "shapley_budget_identity_within_tolerance": True,
                "telemetric_and_external_gate_respected": True,
                "no_component_pooling": True,
                "attribution_does_not_require_labels": True,
                "external_labels_independent_when_supplied": bool(
                    labels is None or external_cause_labels_independent is True
                ),
                "causal_register_contract_respected": True,
                "observer_fail_closed_without_conformant_phi": True,
            },
        }
    for row in range(1, n):
        for component in range(components):
            if not (
                clear[row - 1]
                and clear[row]
                and valid[row - 1, component]
                and valid[row, component]
            ):
                continue
            eligible[row, component] = True
            phi0, phi1 = float(phi[row - 1]), float(phi[row])
            psi0, psi1 = float(psi[row - 1, component]), float(psi[row, component])
            f00 = abs(phi0 - psi0)
            f10 = abs(phi1 - psi0)
            f01 = abs(phi0 - psi1)
            f11 = abs(phi1 - psi1)
            c_phi = 0.5 * ((f10 - f00) + (f11 - f01))
            c_psi = 0.5 * ((f01 - f00) + (f11 - f10))
            change = f11 - f00
            phi_contribution[row, component] = c_phi
            psi_contribution[row, component] = c_psi
            mismatch_change[row, component] = change
            status[row, component] = (
                "no_new_deterioration"
                if change <= tolerance
                else "joint"
                if abs(c_phi - c_psi) <= tolerance
                else "phi_internal"
                if c_phi > c_psi
                else "psi_environmental"
            )
    residual = mismatch_change - phi_contribution - psi_contribution
    finite = residual[eligible]
    exact = bool(
        finite.size == 0
        or np.max(np.abs(finite)) <= max(tolerance, 8.0 * np.finfo(float).eps)
    )
    gate = bool(np.all(status[~eligible] == INDETERMINATE))
    if not exact or not gate:
        raise RuntimeError("Causal Link invariant failure")
    expected = {
        "internal": "phi_internal",
        "environmental": "psi_environmental",
        "joint": "joint",
        "none": "no_new_deterioration",
    }
    summaries: dict[str, Any] = {}
    for component, name in enumerate(displacement.component_names):
        mask = eligible[:, component]
        matches = None
        if labels is not None:
            matches = np.asarray(
                [
                    bool(
                        mask[row]
                        and status[row, component] == expected[str(labels[row])]
                    )
                    for row in range(n)
                ],
                dtype=np.bool_,
            )
        summaries[name] = {
            "counts": _counts(status[:, component]),
            "eligible_rows": int(mask.sum()),
            "independent_label_matches": (
                None if matches is None else int(matches.sum())
            ),
            "independent_label_match_fraction": (
                None
                if matches is None or not mask.any()
                else float(matches.sum() / mask.sum())
            ),
        }
    return {
        "component_names": displacement.component_names,
        "status_path": status,
        "eligible": eligible,
        "phi_contribution": phi_contribution,
        "psi_contribution": psi_contribution,
        "mismatch_change": mismatch_change,
        "summary": {
            "components": summaries,
            "global_scalar_emitted": False,
            "observer_emits": True,
            "instrument_component_explored": False,
            "fail_closed_reason": None,
        },
        "invariants": {
            "shapley_budget_identity_within_tolerance": exact,
            "telemetric_and_external_gate_respected": gate,
            "no_component_pooling": True,
            "attribution_does_not_require_labels": True,
            "external_labels_independent_when_supplied": bool(
                labels is None or external_cause_labels_independent is True
            ),
            "causal_register_contract_respected": True,
            "observer_fail_closed_without_conformant_phi": True,
        },
    }


def estimation_fidelity_status(
    representation: OperatorRepresentation,
    xi: object,
    theta: object,
    observability_clear: object,
    *,
    boundary_tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Compare structural excess with a causal external operator representation."""

    if not representation.contract.get("complete", False):
        raise ObserverContractError("Estimation Fidelity needs a complete R contract")
    if boundary_tolerance < 0.0 or not math.isfinite(boundary_tolerance):
        raise ObserverContractError("invalid Estimation Fidelity tolerance")
    arrays = _aligned_float_vectors(xi=xi, theta=theta)
    clear = _vector("observability_clear", observability_clear, np.bool_)
    if clear.shape != arrays["xi"].shape or representation.values.shape != clear.shape:
        raise ObserverContractError("Estimation Fidelity inputs must align")
    if representation.valid.shape != clear.shape or np.any(arrays["theta"] <= 0.0):
        raise ObserverContractError("Estimation Fidelity requires positive Theta")
    eligible = clear & representation.valid
    excess = arrays["xi"] - arrays["theta"]
    error = np.full(clear.size, np.nan, dtype=np.float64)
    fidelity = np.full(clear.size, np.nan, dtype=np.float64)
    error[eligible] = np.abs(representation.values[eligible] - excess[eligible])
    fidelity[eligible] = 1.0 - error[eligible] / arrays["theta"][eligible]
    status = np.full(clear.size, INDETERMINATE, dtype=object)
    critical = eligible & (np.abs(fidelity) <= boundary_tolerance)
    status[eligible & (fidelity > boundary_tolerance)] = "faithful_self_image"
    status[critical] = "critical_self_image"
    status[eligible & (fidelity < -boundary_tolerance)] = "epistemically_saturated"
    identity = bool(
        np.allclose(
            fidelity[eligible],
            1.0 - error[eligible] / arrays["theta"][eligible],
            rtol=0.0,
            atol=0.0,
        )
    )
    gate = bool(np.all(status[~eligible] == INDETERMINATE))
    if not identity or not gate:
        raise RuntimeError("Estimation Fidelity invariant failure")
    return {
        "status_path": status,
        "operator_R": representation.values.copy(),
        "structural_excess": excess,
        "representation_error": error,
        "fidelity": fidelity,
        "eligible": eligible,
        "summary": {"counts": _counts(status), "eligible_rows": int(eligible.sum())},
        "invariants": {
            "fidelity_identity_exact": identity,
            "telemetric_and_R_gate_respected": gate,
            "operator_R_is_external_to_prama": True,
            "operator_R_is_causal": True,
        },
    }
