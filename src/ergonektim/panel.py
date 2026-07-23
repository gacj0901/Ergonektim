"""Single-run integration of the six ERGONEKTIM observer contracts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ._strict import StrictTypeError, strict_boolean_vector
from .contracts import (
    CausalRegisterContract,
    ExternalDisplacement,
    OperatorRepresentation,
    validate_causal_register,
)
from .kernel_binding import verify_prama_binding
from .observers import (
    causal_link_status,
    condition_report,
    estimation_fidelity_status,
    performance_status,
    stability_status,
)
from .reachability import audit_lambda_reachability
from .signals import build_diagnostic_signal
from .telemetry import TelemetricContract, audit_telemetry_frame


class AssessmentContractError(ValueError):
    """Raised when a complete assessment cannot be aligned causally."""


@dataclass(frozen=True)
class AssessmentInputs:
    index: pd.DatetimeIndex
    omega: np.ndarray
    expected: np.ndarray
    sigma_op: np.ndarray
    u_lambda: np.ndarray
    effective_flow: np.ndarray
    planned: np.ndarray
    telemetry: pd.DataFrame
    telemetry_timestamp_column: str
    telemetry_q_column: str
    telemetry_valid_columns: tuple[str, ...]
    displacement: ExternalDisplacement
    phi_register: np.ndarray
    phi_valid: np.ndarray
    phi_issued_at: pd.DatetimeIndex
    causal_register_contract: CausalRegisterContract
    external_cause_labels: np.ndarray | None
    external_cause_labels_independent: bool | None
    operator_representation: OperatorRepresentation


def _vector(name: str, values: object, length: int, dtype: object) -> np.ndarray:
    if np.dtype(dtype).kind == "b":
        try:
            return strict_boolean_vector(
                values,
                name=name,
                expected_length=length,
            )
        except StrictTypeError as exc:
            raise AssessmentContractError(str(exc)) from exc
    array = np.asarray(values, dtype=dtype)
    if array.ndim != 1 or array.size != length:
        raise AssessmentContractError(f"{name} must align with assessment index")
    return array


def _timestamp(value: pd.Timestamp) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _float_or_none(value: float) -> float | None:
    return None if not np.isfinite(value) else float(value)


def _validated_inputs(inputs: AssessmentInputs) -> dict[str, np.ndarray]:
    index = pd.DatetimeIndex(inputs.index)
    if len(index) == 0 or index.tz is None:
        raise AssessmentContractError("assessment index must be timezone-aware")
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise AssessmentContractError("assessment index must be unique and increasing")
    n = len(index)
    arrays = {
        "omega": _vector("omega", inputs.omega, n, np.float64),
        "expected": _vector("expected", inputs.expected, n, np.float64),
        "sigma_op": _vector("sigma_op", inputs.sigma_op, n, np.bool_),
        "u_lambda": _vector("u_lambda", inputs.u_lambda, n, np.float64),
        "effective_flow": _vector(
            "effective_flow", inputs.effective_flow, n, np.float64
        ),
        "planned": _vector("planned", inputs.planned, n, np.bool_),
        "phi_register": _vector("phi_register", inputs.phi_register, n, np.float64),
        "phi_valid": _vector("phi_valid", inputs.phi_valid, n, np.bool_),
    }
    if inputs.external_cause_labels is not None:
        arrays["external_cause_labels"] = _vector(
            "external_cause_labels", inputs.external_cause_labels, n, object
        )
    for name in ("omega", "expected", "u_lambda", "effective_flow"):
        if not np.isfinite(arrays[name]).all():
            raise AssessmentContractError(f"{name} must be finite")
    if len(pd.DatetimeIndex(inputs.phi_issued_at)) != n:
        raise AssessmentContractError("phi_issued_at must align")
    if inputs.displacement.values.shape[0] != n:
        raise AssessmentContractError("external displacement must align")
    if inputs.operator_representation.values.shape != (n,):
        raise AssessmentContractError("operator representation must align")
    return arrays


def evaluate_assessment(
    inputs: AssessmentInputs,
    *,
    telemetric_contract: TelemetricContract,
    recertification_path: str | Path,
    kernel_config: Any | None = None,
    input_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the frozen kernel and all six observers in one process."""

    binding = verify_prama_binding(recertification_path)
    if not binding["verified"]:
        raise RuntimeError("PRAMA binding is not canonical")
    from prama_protokol import KernelConfigV3, project_v3

    arrays = _validated_inputs(inputs)
    index = pd.DatetimeIndex(inputs.index)
    if kernel_config is None:
        cfg = KernelConfigV3()
    elif isinstance(kernel_config, Mapping):
        try:
            cfg = KernelConfigV3(**dict(kernel_config))
        except (TypeError, ValueError) as exc:
            raise AssessmentContractError("invalid kernel_config mapping") from exc
    else:
        cfg = kernel_config
    if not isinstance(cfg, KernelConfigV3):
        raise AssessmentContractError(
            "kernel_config must be KernelConfigV3 or a complete mapping"
        )
    if input_binding is None:
        binding_record: dict[str, Any] = {
            "kind": "programmatic",
            "verified": False,
            "file_custody_available": False,
        }
    else:
        try:
            encoded_binding = json.dumps(
                input_binding, sort_keys=True, allow_nan=False
            )
        except (TypeError, ValueError) as exc:
            raise AssessmentContractError("input_binding must be finite JSON") from exc
        binding_record = deepcopy(json.loads(encoded_binding))
    gamma = project_v3(
        arrays["omega"],
        arrays["expected"],
        cfg,
        arrays["u_lambda"],
        arrays["sigma_op"],
    )
    if len(gamma) != len(index):
        raise AssessmentContractError(
            "assessment inputs must already exclude leading kernel warm-up"
        )

    telemetric = audit_telemetry_frame(
        inputs.telemetry,
        timestamp_column=inputs.telemetry_timestamp_column,
        q_column=inputs.telemetry_q_column,
        source_valid_columns=list(inputs.telemetry_valid_columns),
        contract=telemetric_contract,
    )
    telemetric_index = pd.DatetimeIndex(
        pd.to_datetime(telemetric.timeline["timestamp_utc"], utc=True)
    )
    if not telemetric_index.equals(index):
        raise AssessmentContractError("telemetric grid differs from assessment index")
    clear = telemetric.timeline["observability_clear"].to_numpy(dtype=np.bool_)
    phi = validate_causal_register(
        index,
        arrays["phi_register"],
        arrays["phi_valid"],
        inputs.phi_issued_at,
        inputs.causal_register_contract,
    )

    stability = stability_status(gamma.sigma_op, gamma.M, gamma.G, clear)
    performance = performance_status(
        gamma.A,
        gamma.u_lambda,
        gamma.M,
        arrays["effective_flow"],
        clear,
        kappa=cfg.kappa_v3,
        h=cfg.h,
    )
    condition = condition_report(index, arrays["planned"], gamma.M, clear)
    causal = causal_link_status(
        phi.values,
        inputs.displacement,
        clear,
        arrays.get("external_cause_labels"),
        causal_register_contract=inputs.causal_register_contract,
        causal_register_valid=phi.valid,
        causal_register_record=phi.contract,
        external_cause_labels_independent=inputs.external_cause_labels_independent,
    )
    fidelity = estimation_fidelity_status(
        inputs.operator_representation, gamma.xi, gamma.theta, clear
    )
    exceedance_active = gamma.xi > gamma.theta
    accumulated_debt_active = gamma.A > 0.0
    regulatory_drain_active = cfg.kappa_v3 * cfg.h * gamma.A > 0.0
    lambda_changed = gamma.lambda_ != cfg.lambda_0
    regulatory_branch_exercised = bool(accumulated_debt_active.any())
    reachability = audit_lambda_reachability(
        gamma.delta_tilde,
        gamma.xi,
        gamma.theta,
        h=cfg.h,
        tau=cfg.tau,
        xi_initial=0.0,
    )
    kernel_branch_coverage = {
        "regulatory_A_lambda": {
            "xi_maximum": float(np.max(gamma.xi)),
            "theta_minimum": float(np.min(gamma.theta)),
            "theta_maximum": float(np.max(gamma.theta)),
            "accumulated_debt_maximum": float(np.max(gamma.A)),
            "lambda_minimum": float(np.min(gamma.lambda_)),
            "lambda_maximum": float(np.max(gamma.lambda_)),
            "exceedance_active_rows": int(exceedance_active.sum()),
            "accumulated_debt_active_rows": int(accumulated_debt_active.sum()),
            "regulatory_drain_active_rows": int(regulatory_drain_active.sum()),
            "lambda_changed_from_initial_rows": int(lambda_changed.sum()),
            "rows": len(index),
            "exercised": regulatory_branch_exercised,
            "interpretation": (
                "regulatory_branch_exercised"
                if regulatory_branch_exercised
                else "regulatory_branch_not_exercised"
            ),
            "analytic_reachability": reachability,
        }
    }

    timeline: list[dict[str, Any]] = []
    for row, timestamp in enumerate(index):
        timestamp_utc = _timestamp(timestamp)
        telemetric_code = str(telemetric.timeline.iloc[row]["telemetric_status"])
        telemetric_signal = build_diagnostic_signal(
            "telemetric_status",
            telemetric_code,
            eligible=bool(clear[row]),
            timestamp_utc=timestamp_utc,
            evidence={
                "interval_width": float(telemetric.timeline.iloc[row]["interval_width"]),
                "quarantine_reasons": str(
                    telemetric.timeline.iloc[row]["quarantine_reasons"]
                ),
            },
        )
        stability_code = str(stability["status_path"][row])
        stability_signal = build_diagnostic_signal(
            "stability_status",
            stability_code,
            eligible=stability_code != "instrument_indeterminate",
            timestamp_utc=timestamp_utc,
            evidence={
                "sigma_op": bool(gamma.sigma_op[row]),
                "M": float(gamma.M[row]),
                "G": float(gamma.G[row]),
            },
        )
        performance_code = str(performance["status_path"][row])
        performance_signal = build_diagnostic_signal(
            "performance_status",
            performance_code,
            eligible=performance_code != "instrument_indeterminate",
            timestamp_utc=timestamp_utc,
            evidence={
                "structural_drain": float(performance["structural_drain"][row]),
                "regeneration": float(performance["regeneration"][row]),
                "net_solvency": float(performance["net_solvency"][row]),
                "effective_flow": float(arrays["effective_flow"][row]),
            },
        )
        fidelity_code = str(fidelity["status_path"][row])
        fidelity_signal = build_diagnostic_signal(
            "estimation_fidelity",
            fidelity_code,
            eligible=fidelity_code != "instrument_indeterminate",
            timestamp_utc=timestamp_utc,
            evidence={
                "operator_R": _float_or_none(fidelity["operator_R"][row]),
                "structural_excess": float(fidelity["structural_excess"][row]),
                "representation_error": _float_or_none(
                    fidelity["representation_error"][row]
                ),
                "fidelity": _float_or_none(fidelity["fidelity"][row]),
            },
        )
        causal_signals = []
        for component, name in enumerate(causal["component_names"]):
            causal_code = str(causal["status_path"][row, component])
            causal_signals.append(
                {
                    "component": name,
                    "diagnostic": build_diagnostic_signal(
                        "causal_link",
                        causal_code,
                        eligible=bool(causal["eligible"][row, component]),
                        timestamp_utc=timestamp_utc,
                        evidence={
                            "component": name,
                            "phi_contribution": _float_or_none(
                                causal["phi_contribution"][row, component]
                            ),
                            "psi_contribution": _float_or_none(
                                causal["psi_contribution"][row, component]
                            ),
                            "mismatch_change": _float_or_none(
                                causal["mismatch_change"][row, component]
                            ),
                        },
                    ),
                }
            )
        timeline.append(
            {
                "timestamp_utc": timestamp_utc,
                "state": {
                    "delta": float(gamma.delta[row]),
                    "delta_tilde": float(gamma.delta_tilde[row]),
                    "xi": float(gamma.xi[row]),
                    "A": float(gamma.A[row]),
                    "lambda": float(gamma.lambda_[row]),
                    "theta": float(gamma.theta[row]),
                    "M": float(gamma.M[row]),
                    "G": float(gamma.G[row]),
                    "u_lambda": float(gamma.u_lambda[row]),
                    "sigma_op": bool(gamma.sigma_op[row]),
                },
                "signals": {
                    "telemetric_status": telemetric_signal,
                    "stability_status": stability_signal,
                    "performance_status": performance_signal,
                    "causal_link": causal_signals,
                    "estimation_fidelity": fidelity_signal,
                },
            }
        )

    condition_signals = []
    for episode in condition["episodes"]:
        evidence = {
            key: value
            for key, value in episode.items()
            if key not in {"status", "eligible"}
        }
        condition_signals.append(
            build_diagnostic_signal(
                "condition_report",
                str(episode["status"]),
                eligible=bool(episode["eligible"]),
                timestamp_utc=str(episode["stop_exclusive_utc"]),
                evidence=evidence,
            )
        )

    return {
        "schema_version": "ergonektim.assessment.v1.3",
        "access": {
            "outcomes_accessed": False,
            "future_values_accessed": False,
            "global_scalar_emitted": False,
        },
        "kernel_binding": binding,
        "input_binding": binding_record,
        "kernel_config": asdict(cfg),
        "source_contracts": {
            "causal_register_phi": phi.contract,
            "external_displacement": inputs.displacement.contract,
            "operator_representation": inputs.operator_representation.contract,
            "telemetric": telemetric.report["contract"],
        },
        "dynamics_boundary": {
            "external_displacement_w": {
                "observed": True,
                "contract_complete": bool(inputs.displacement.complete),
                "coupled_to_kernel_dynamics": False,
                "observer_consumers": ["causal_link"],
                "claim_boundary": (
                    "w is observed and contracted for component-wise attribution; "
                    "it is not an input to Omega, Xi, A, lambda, Theta, M, or G."
                ),
            },
            "causal_register_phi": {
                "observed": True,
                "instrument_complete": bool(phi.contract["instrument_complete"]),
                "contract_complete": bool(phi.contract["complete"]),
                "observer_emission_authorized": bool(
                    phi.contract["observer_emission_authorized"]
                ),
                "representation_theorem_claimed": bool(
                    phi.contract["metadata"]["representation_theorem_claimed"]
                ),
                "coupled_to_kernel_dynamics": False,
                "observer_consumers": ["causal_link"],
                "claim_boundary": (
                    "Phi is an observer input, not a kernel input. Causal Link "
                    "emits only when its hash-bound level-1 operational "
                    "conformance contract authorizes emission. A separate "
                    "representation-theorem claim is recorded independently "
                    "and is not an emission prerequisite."
                ),
            },
        },
        "kernel_branch_coverage": kernel_branch_coverage,
        "observer_invariants": {
            "telemetric_status": telemetric.report["invariants"],
            "stability_status": stability["invariants"],
            "performance_status": performance["invariants"],
            "condition_report": condition["invariants"],
            "causal_link": causal["invariants"],
            "estimation_fidelity": fidelity["invariants"],
        },
        "observer_summaries": {
            "telemetric_status": {
                "status": telemetric.report["status"],
                "coverage": telemetric.report["coverage"],
                "claim_boundary": telemetric.report["claim_boundary"],
            },
            "stability_status": stability["summary"],
            "performance_status": performance["summary"],
            "condition_report": condition["summary"],
            "causal_link": causal["summary"],
            "estimation_fidelity": fidelity["summary"],
        },
        "condition_report": condition_signals,
        "timeline": timeline,
        "summary": {
            "rows": len(timeline),
            "observer_count": 6,
            "single_process_run": True,
            "global_scalar_emitted": False,
            "regulatory_branch_exercised": regulatory_branch_exercised,
        },
    }


def write_assessment(path: str | Path, payload: dict[str, Any]) -> Path:
    """Write deterministic JSON; the caller chooses the authorized path."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_assessment_bytes(payload))
    return target


def canonical_assessment_bytes(payload: Mapping[str, Any]) -> bytes:
    """Encode an assessment in the only accepted artifact representation."""

    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8") + b"\n"
