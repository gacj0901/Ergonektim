"""Analytic reachability audit for the PRAMA regulatory branch."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


class ReachabilityAuditError(ValueError):
    """Raised when a reachability claim lacks a finite declared basis."""


def retention_factor(*, h: float, tau: float) -> float:
    h_value = float(h)
    tau_value = float(tau)
    if (
        not math.isfinite(h_value)
        or not math.isfinite(tau_value)
        or h_value <= 0.0
        or tau_value <= 0.0
    ):
        raise ReachabilityAuditError("h and tau must be positive finite values")
    return math.exp(-h_value / tau_value)


def constant_input_state(
    input_level: float,
    *,
    xi_initial: float,
    bins: int,
    h: float,
    tau: float,
) -> float:
    """Exact EWMA state after ``bins`` constant-input updates."""

    level = float(input_level)
    initial = float(xi_initial)
    if not math.isfinite(level) or not math.isfinite(initial):
        raise ReachabilityAuditError("constant-input values must be finite")
    if isinstance(bins, bool) or not isinstance(bins, int) or bins < 0:
        raise ReachabilityAuditError("bins must be a nonnegative integer")
    r = retention_factor(h=h, tau=tau)
    return level + (initial - level) * (r**bins)


def minimum_constant_input_bins(
    input_level: float,
    *,
    xi_initial: float,
    theta: float,
    h: float,
    tau: float,
) -> int | None:
    """Return the first bin with strict ``Xi > theta``, or ``None``."""

    level = float(input_level)
    initial = float(xi_initial)
    threshold = float(theta)
    if not all(math.isfinite(value) for value in (level, initial, threshold)):
        raise ReachabilityAuditError("crossing inputs must be finite")
    if initial > threshold:
        return 0
    if level <= threshold:
        return None
    scale = float(tau) / float(h)
    continuous = scale * math.log((level - initial) / (level - threshold))
    candidate = max(0, math.floor(continuous) + 1)
    while constant_input_state(
        level, xi_initial=initial, bins=candidate, h=h, tau=tau
    ) <= threshold:
        candidate += 1
    while candidate > 0 and constant_input_state(
        level, xi_initial=initial, bins=candidate - 1, h=h, tau=tau
    ) > threshold:
        candidate -= 1
    return candidate


def audit_lambda_reachability(
    delta_tilde: object,
    xi: object,
    theta: object,
    *,
    h: float,
    tau: float,
    xi_initial: float = 0.0,
    empirical_input_bound: float | None = None,
    recurrence_tolerance: float | None = None,
) -> dict[str, Any]:
    """Classify branch reachability without recalibrating any threshold."""

    delta = np.asarray(delta_tilde, dtype=np.float64)
    xi_values = np.asarray(xi, dtype=np.float64)
    theta_values = np.asarray(theta, dtype=np.float64)
    if (
        delta.ndim != 1
        or delta.size == 0
        or xi_values.shape != delta.shape
        or theta_values.shape != delta.shape
    ):
        raise ReachabilityAuditError(
            "delta_tilde, xi, and theta must be aligned nonempty vectors"
        )
    if (
        not np.isfinite(delta).all()
        or not np.isfinite(xi_values).all()
        or not np.isfinite(theta_values).all()
        or np.any(delta < 0.0)
        or np.any(theta_values <= 0.0)
    ):
        raise ReachabilityAuditError(
            "reachability vectors must be finite with nonnegative input and positive theta"
        )
    initial = float(xi_initial)
    if not math.isfinite(initial) or initial < 0.0:
        raise ReachabilityAuditError("xi_initial must be finite and nonnegative")
    r = retention_factor(h=h, tau=tau)
    replica = np.empty_like(delta)
    previous = initial
    for row, input_value in enumerate(delta):
        previous = r * previous + (1.0 - r) * float(input_value)
        replica[row] = previous
    scale = max(
        1.0,
        float(np.max(np.abs(delta))),
        float(np.max(np.abs(xi_values))),
    )
    if recurrence_tolerance is None:
        tolerance = float(
            64.0
            * np.finfo(np.float64).eps
            * scale
            * max(1, int(delta.size))
        )
    else:
        tolerance = float(recurrence_tolerance)
        if not math.isfinite(tolerance) or tolerance < 0.0:
            raise ReachabilityAuditError(
                "recurrence_tolerance must be finite and nonnegative"
            )
    recurrence_residual = float(np.max(np.abs(replica - xi_values)))
    if recurrence_residual > tolerance:
        raise ReachabilityAuditError(
            "xi does not satisfy the declared exact-input recurrence"
        )
    if empirical_input_bound is None:
        bound = float(np.max(delta))
        bound_source = "maximum_observed_delta_tilde"
    else:
        bound = float(empirical_input_bound)
        if not math.isfinite(bound) or bound < float(np.max(delta)):
            raise ReachabilityAuditError(
                "empirical_input_bound must be finite and cover observed delta_tilde"
            )
        bound_source = "externally_declared_empirical_bound"

    crossing = xi_values > theta_values
    crossing_rows = np.flatnonzero(crossing)
    minimum_theta = float(np.min(theta_values))
    envelope = constant_input_state(
        bound,
        xi_initial=initial,
        bins=int(delta.size),
        h=h,
        tau=tau,
    )
    if crossing_rows.size:
        status = "observed_crossing"
    elif envelope <= minimum_theta:
        status = "unreachable_under_empirical_bound"
    else:
        status = "reachable_not_observed"
    crossing_bins = minimum_constant_input_bins(
        bound,
        xi_initial=initial,
        theta=minimum_theta,
        h=h,
        tau=tau,
    )
    return {
        "status": status,
        "bound_kind": "empirical_observed_not_physical",
        "bound_source": bound_source,
        "rows": int(delta.size),
        "h": float(h),
        "tau": float(tau),
        "retention_factor": r,
        "xi_initial": initial,
        "theta_initial": float(theta_values[0]),
        "theta_minimum": minimum_theta,
        "empirical_delta_tilde_maximum": float(np.max(delta)),
        "empirical_input_bound": bound,
        "finite_window_envelope": envelope,
        "constant_input_crossing_bins_at_bound": crossing_bins,
        "observed_xi_maximum": float(np.max(xi_values)),
        "recurrence_maximum_absolute_residual": recurrence_residual,
        "recurrence_tolerance": tolerance,
        "observed_crossing_rows": int(crossing_rows.size),
        "first_observed_crossing_row": (
            None if crossing_rows.size == 0 else int(crossing_rows[0])
        ),
        "recurrence": "Xi_next=r*Xi+(1-r)*delta_tilde",
        "activation_timing": (
            "e at row k uses Xi_k and Theta_k; a first Xi crossing affects A "
            "on the following kernel update"
        ),
        "threshold_recalibrated": False,
        "claim_boundary": (
            "An empirical bound characterizes only the declared window and is "
            "not a physical limit of the system."
        ),
        "invariants": {
            "observed_crossing_definition_exact": bool(
                crossing_rows.size == int(np.sum(xi_values > theta_values))
            ),
            "finite_window_envelope_uses_exact_recurrence": True,
            "observed_xi_recurrence_verified": bool(
                recurrence_residual <= tolerance
            ),
            "threshold_unchanged": True,
            "empirical_bound_not_reported_as_physical": True,
        },
    }
