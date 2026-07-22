"""Non-circular external contracts used by ERGONEKTIM observers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


W_CONTRACT_ID = "ergonektim.external-displacement.w.v1"
R_CONTRACT_ID = "ergonektim.operator-representation.R.v1"
R_TARGET = "structural_excess_xi_minus_theta"
NORMALIZATIONS = {"reference_relative", "fixed_scale"}


class ExternalContractError(ValueError):
    """Raised when an external input is acausal, circular, or incomplete."""


@dataclass(frozen=True)
class ExternalDisplacementChannel:
    """Frozen metadata for one signed external displacement component."""

    name: str
    observation_role: str
    reference_role: str
    normalization: str
    normalization_id: str
    source_system: str
    source_owner: str
    stress_sign: int = 1
    fixed_scale: float | None = None
    reference_floor: float = 0.0
    reference_available_by_t: bool = True
    independent_of_internal_register: bool = True
    independent_of_kernel: bool = True

    def validate(self) -> None:
        text_fields = (
            self.name,
            self.observation_role,
            self.reference_role,
            self.normalization_id,
            self.source_system,
            self.source_owner,
        )
        if any(not value.strip() for value in text_fields):
            raise ExternalContractError("external displacement metadata must be nonempty")
        if self.normalization not in NORMALIZATIONS:
            raise ExternalContractError("unsupported external displacement normalization")
        if self.stress_sign not in {-1, 1}:
            raise ExternalContractError("stress_sign must be -1 or +1")
        if self.normalization == "fixed_scale":
            if (
                self.fixed_scale is None
                or not math.isfinite(self.fixed_scale)
                or self.fixed_scale <= 0.0
            ):
                raise ExternalContractError(
                    "fixed_scale normalization needs a positive finite scale"
                )
        elif self.fixed_scale is not None:
            raise ExternalContractError(
                "reference_relative normalization must not declare fixed_scale"
            )
        if not math.isfinite(self.reference_floor) or self.reference_floor < 0.0:
            raise ExternalContractError("reference_floor must be finite and nonnegative")
        if not self.reference_available_by_t:
            raise ExternalContractError("external reference must be available by t")
        if not self.independent_of_internal_register or not self.independent_of_kernel:
            raise ExternalContractError("external displacement provenance is not autonomous")


@dataclass(frozen=True)
class ExternalDisplacement:
    component_names: tuple[str, ...]
    values: np.ndarray
    valid: np.ndarray
    pressure: np.ndarray
    support: np.ndarray
    quarantined: np.ndarray
    contract: dict[str, Any]

    @property
    def complete(self) -> bool:
        return bool(self.contract["complete"])


@dataclass(frozen=True)
class OperatorRepresentationContract:
    source_system: str
    source_owner: str
    channel_role: str
    normalization_id: str
    units: str
    coupled_operational_parameter: str
    representation_target: str = R_TARGET
    available_by_t: bool = True
    generated_independently_from_prama: bool = True
    prama_variables_used: tuple[str, ...] = ()

    def validate(self) -> None:
        text_fields = (
            self.source_system,
            self.source_owner,
            self.channel_role,
            self.normalization_id,
            self.units,
            self.coupled_operational_parameter,
        )
        if any(not value.strip() for value in text_fields):
            raise ExternalContractError("operator representation metadata must be nonempty")
        if self.representation_target != R_TARGET:
            raise ExternalContractError("operator representation must target Xi minus Theta")
        if not self.available_by_t:
            raise ExternalContractError("operator representation must be available by t")
        if not self.generated_independently_from_prama or self.prama_variables_used:
            raise ExternalContractError(
                "operator representation cannot be reconstructed from PRAMA variables"
            )


@dataclass(frozen=True)
class OperatorRepresentation:
    values: np.ndarray
    valid: np.ndarray
    contract: dict[str, Any]


def _index(index: object, name: str) -> pd.DatetimeIndex:
    stamps = pd.DatetimeIndex(index)
    if len(stamps) == 0 or stamps.tz is None:
        raise ExternalContractError(f"{name} requires timezone-aware timestamps")
    if not stamps.is_monotonic_increasing or stamps.has_duplicates:
        raise ExternalContractError(f"{name} timestamps must be unique and increasing")
    return stamps


def _float_vector(name: str, values: object, length: int) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size != length:
        raise ExternalContractError(f"{name} must align with timestamps")
    return array


def _bool_vector(name: str, values: object, length: int) -> np.ndarray:
    array = np.asarray(values, dtype=np.bool_)
    if array.ndim != 1 or array.size != length:
        raise ExternalContractError(f"{name} must align with timestamps")
    return array


def _issue_vector(name: str, values: object, length: int) -> pd.DatetimeIndex:
    stamps = pd.DatetimeIndex(values)
    if len(stamps) != length or stamps.tz is None:
        raise ExternalContractError(
            f"{name} issue times must align and be timezone-aware"
        )
    return stamps


def realize_external_displacement(
    index: object,
    channels: Sequence[ExternalDisplacementChannel],
    observations: Mapping[str, object],
    references: Mapping[str, object],
    source_valid: Mapping[str, object],
    reference_issue_times: Mapping[str, object],
) -> ExternalDisplacement:
    """Realize distributive signed components without scalar fusion."""

    stamps = _index(index, "external displacement")
    if not channels:
        raise ExternalContractError("at least one displacement component is required")
    names = tuple(channel.name for channel in channels)
    if len(set(names)) != len(names):
        raise ExternalContractError("displacement component names must be unique")

    n = len(stamps)
    values = np.full((n, len(channels)), np.nan, dtype=np.float64)
    valid = np.zeros((n, len(channels)), dtype=np.bool_)
    causal = np.zeros((n, len(channels)), dtype=np.bool_)
    records: list[dict[str, Any]] = []

    for column, channel in enumerate(channels):
        channel.validate()
        for mapping, role in (
            (observations, "observation"),
            (references, "reference"),
            (source_valid, "source_valid"),
            (reference_issue_times, "reference_issue_times"),
        ):
            if channel.name not in mapping:
                raise ExternalContractError(f"missing {role} for {channel.name}")

        observed = _float_vector(
            channel.name + ".observation", observations[channel.name], n
        )
        reference = _float_vector(
            channel.name + ".reference", references[channel.name], n
        )
        declared_valid = _bool_vector(
            channel.name + ".source_valid", source_valid[channel.name], n
        )
        issue_time = _issue_vector(
            channel.name + ".reference_issue_times",
            reference_issue_times[channel.name],
            n,
        )
        causal[:, column] = issue_time <= stamps

        finite = np.isfinite(observed) & np.isfinite(reference)
        if channel.normalization == "reference_relative":
            denominator = np.abs(reference)
            denominator_valid = denominator > channel.reference_floor
        else:
            denominator = np.full(n, float(channel.fixed_scale), dtype=np.float64)
            denominator_valid = np.ones(n, dtype=np.bool_)

        raw = np.full(n, np.nan, dtype=np.float64)
        computable = finite & denominator_valid
        raw[computable] = (
            channel.stress_sign
            * (observed[computable] - reference[computable])
            / denominator[computable]
        )
        in_range = np.isfinite(raw) & (np.abs(raw) <= 1.0)
        component_valid = declared_valid & causal[:, column] & computable & in_range
        values[component_valid, column] = raw[component_valid]
        valid[:, column] = component_valid
        records.append(
            {
                **asdict(channel),
                "valid_rows": int(component_valid.sum()),
                "quarantined_rows": int((~component_valid).sum()),
                "future_reference_rows": int((~causal[:, column]).sum()),
                "out_of_range_rows": int(
                    (declared_valid & computable & ~in_range).sum()
                ),
            }
        )

    pressure = np.where(valid, np.maximum(values, 0.0), np.nan)
    support = np.where(valid, np.maximum(-values, 0.0), np.nan)
    checks = {
        "component_metadata_complete": True,
        "each_component_has_observed_support": bool(np.all(np.any(valid, axis=0))),
        "references_causal_on_all_emitted_rows": bool(np.all(causal[valid])),
        "internal_register_inputs_used": False,
        "kernel_inputs_used": False,
        "outcome_inputs_used": False,
        "global_scalar_fusion_used": False,
        "invalid_values_imputed_or_clipped": False,
        "pressure_support_identity": bool(
            np.allclose(values[valid], pressure[valid] - support[valid], rtol=0.0, atol=0.0)
        ),
    }
    complete = bool(
        checks["each_component_has_observed_support"]
        and checks["references_causal_on_all_emitted_rows"]
        and checks["pressure_support_identity"]
    )
    return ExternalDisplacement(
        component_names=names,
        values=values,
        valid=valid,
        pressure=pressure,
        support=support,
        quarantined=~valid,
        contract={
            "contract_id": W_CONTRACT_ID,
            "complete": complete,
            "completeness_semantics": (
                "every declared component has observation, causal reference, frozen "
                "normalization, validity, and autonomous provenance; not exhaustive coverage"
            ),
            "components": records,
            "checks": checks,
        },
    )


def validate_operator_representation(
    index: object,
    values: object,
    source_valid: object,
    issued_at: object,
    contract: OperatorRepresentationContract,
) -> OperatorRepresentation:
    """Validate an external, causal, non-circular operator representation."""

    contract.validate()
    stamps = _index(index, "operator representation")
    issue = _issue_vector("operator representation", issued_at, len(stamps))
    representation = _float_vector("operator representation", values, len(stamps))
    declared_valid = _bool_vector(
        "operator representation validity", source_valid, len(stamps)
    )
    causal = issue <= stamps
    finite = np.isfinite(representation)
    valid = declared_valid & causal & finite
    emitted = np.full(representation.size, np.nan, dtype=np.float64)
    emitted[valid] = representation[valid]
    checks = {
        "external_source_declared": True,
        "at_least_one_valid_row": bool(valid.any()),
        "representation_target_exact": contract.representation_target == R_TARGET,
        "operational_coupling_declared": bool(contract.coupled_operational_parameter),
        "prama_variables_used": False,
        "future_values_used": False,
        "all_emitted_rows_causal": bool(np.all(causal[valid])),
        "invalid_values_imputed": False,
    }
    complete = bool(
        checks["at_least_one_valid_row"]
        and checks["representation_target_exact"]
        and checks["operational_coupling_declared"]
        and checks["all_emitted_rows_causal"]
    )
    return OperatorRepresentation(
        values=emitted,
        valid=valid,
        contract={
            "contract_id": R_CONTRACT_ID,
            "complete": complete,
            "metadata": asdict(contract),
            "checks": checks,
            "valid_rows": int(valid.sum()),
            "quarantined_rows": int((~valid).sum()),
            "future_rows_rejected": int((declared_valid & ~causal).sum()),
        },
    )
