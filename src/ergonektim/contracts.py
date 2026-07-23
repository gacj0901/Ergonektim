"""Non-circular external contracts used by ERGONEKTIM observers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


W_CONTRACT_ID = "ergonektim.external-displacement.w.v1.1"
PHI_CONTRACT_ID = "ergonektim.causal-register.Phi.v2"
R_CONTRACT_ID = "ergonektim.operator-representation.R.v1"
R_TARGET = "structural_excess_xi_minus_theta"
PHI_ORIENTATION = "higher_is_more_coherent"
PROHIBITED_PHI_INPUT_ROLES = {
    "A",
    "G",
    "M",
    "Theta",
    "Xi",
    "cause_label",
    "delta",
    "delta_tilde",
    "evaluation_outcome",
    "external_displacement_w",
    "lambda",
    "outcome",
    "w",
}
NORMALIZATIONS = {
    "reference_relative",
    "absolute_reference_relative",
    "fixed_scale",
}


class ExternalContractError(ValueError):
    """Raised when an external input is acausal, circular, or incomplete."""


def _is_sha256(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


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
        if self.normalization == "absolute_reference_relative" and self.stress_sign != 1:
            raise ExternalContractError(
                "absolute_reference_relative requires stress_sign=+1"
            )
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
                "reference-relative normalizations must not declare fixed_scale"
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
class CausalRegisterContract:
    """Hash-bound custody and level-1 conformance contract for ``Phi``."""

    source_system: str
    source_owner: str
    register_role: str
    construction_id: str
    normalization_id: str
    construction_spec_sha256: str
    input_roles: tuple[str, ...]
    orientation: str = PHI_ORIENTATION
    value_min: float = 0.0
    value_max: float = 1.0
    available_by_t: bool = True
    source_validity_gated: bool = True
    independent_of_external_displacement: bool = True
    independent_of_kernel: bool = True
    outcome_inputs_used: bool = False
    prefix_causality_certified: bool = False
    operational_conformance_certificate_sha256: str | None = None
    representation_theorem_claimed: bool = False
    experimental_only: bool = True

    def validate(self) -> None:
        text_fields = (
            self.source_system,
            self.source_owner,
            self.register_role,
            self.construction_id,
            self.normalization_id,
        )
        if any(not value.strip() for value in text_fields):
            raise ExternalContractError("causal register metadata must be nonempty")
        if not _is_sha256(self.construction_spec_sha256):
            raise ExternalContractError(
                "causal register construction_spec_sha256 is invalid"
            )
        if (
            not self.input_roles
            or any(not isinstance(role, str) or not role.strip() for role in self.input_roles)
            or len(set(self.input_roles)) != len(self.input_roles)
        ):
            raise ExternalContractError(
                "causal register input_roles must be nonempty and unique"
            )
        forbidden = sorted(set(self.input_roles) & PROHIBITED_PHI_INPUT_ROLES)
        if forbidden:
            raise ExternalContractError(
                f"causal register input_roles contain prohibited roles: {forbidden}"
            )
        if self.orientation != PHI_ORIENTATION:
            raise ExternalContractError(
                f"causal register orientation must be {PHI_ORIENTATION}"
            )
        if (
            not math.isfinite(self.value_min)
            or not math.isfinite(self.value_max)
            or self.value_min >= self.value_max
        ):
            raise ExternalContractError("causal register value bounds are invalid")
        if not self.available_by_t:
            raise ExternalContractError("causal register must be available by t")
        if not self.source_validity_gated:
            raise ExternalContractError("causal register must inherit source validity")
        if (
            not self.independent_of_external_displacement
            or not self.independent_of_kernel
        ):
            raise ExternalContractError(
                "causal register cannot be constructed from w or PRAMA variables"
            )
        if self.outcome_inputs_used:
            raise ExternalContractError(
                "causal register construction cannot use evaluation outcomes"
            )
        certificate_present = self.operational_conformance_certificate_sha256 is not None
        if certificate_present and not _is_sha256(
            self.operational_conformance_certificate_sha256
        ):
            raise ExternalContractError(
                "causal register conformance certificate hash is invalid"
            )
        if certificate_present and not self.prefix_causality_certified:
            raise ExternalContractError(
                "operational conformance requires a prefix-causality certificate"
            )
        if certificate_present and self.experimental_only:
            raise ExternalContractError(
                "certified causal register cannot remain experimental_only"
            )
        if not certificate_present and not self.experimental_only:
            raise ExternalContractError(
                "uncertified causal register must remain experimental_only"
            )
        if self.representation_theorem_claimed and not certificate_present:
            raise ExternalContractError(
                "a representation-theorem claim requires operational conformance"
            )

    @property
    def conformant(self) -> bool:
        return bool(
            self.operational_conformance_certificate_sha256 is not None
            and self.prefix_causality_certified
            and not self.experimental_only
        )

    def record(self) -> dict[str, Any]:
        self.validate()
        return {
            "contract_id": PHI_CONTRACT_ID,
            "complete": self.conformant,
            "observer_emission_authorized": self.conformant,
            "metadata": asdict(self),
            "checks": {
                "available_by_t": self.available_by_t,
                "source_validity_gated": self.source_validity_gated,
                "independent_of_external_displacement": (
                    self.independent_of_external_displacement
                ),
                "independent_of_kernel": self.independent_of_kernel,
                "outcome_inputs_absent": not self.outcome_inputs_used,
                "construction_spec_hash_bound": _is_sha256(
                    self.construction_spec_sha256
                ),
                "input_lineage_closed": bool(self.input_roles),
                "prohibited_input_roles_absent": not bool(
                    set(self.input_roles) & PROHIBITED_PHI_INPUT_ROLES
                ),
                "orientation_declared": self.orientation == PHI_ORIENTATION,
                "prefix_causality_certified": self.prefix_causality_certified,
                "operational_conformance_certificate_present": (
                    self.operational_conformance_certificate_sha256 is not None
                ),
                "representation_theorem_claimed": (
                    self.representation_theorem_claimed
                ),
                "operational_not_experimental": not self.experimental_only,
            },
        }


@dataclass(frozen=True)
class CausalRegister:
    values: np.ndarray
    valid: np.ndarray
    contract: dict[str, Any]


@dataclass(frozen=True)
class OperatorRepresentationContract:
    source_system: str
    source_owner: str
    channel_role: str
    normalization_id: str
    construction_spec_sha256: str
    units: str
    coupled_operational_parameter: str
    source_roles_also_used: tuple[str, ...] = ()
    dual_use_declared: bool = False
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
        if not _is_sha256(self.construction_spec_sha256):
            raise ExternalContractError(
                "operator representation construction_spec_sha256 is invalid"
            )
        if (
            len(set(self.source_roles_also_used))
            != len(self.source_roles_also_used)
            or any(
                not isinstance(role, str) or not role.strip()
                for role in self.source_roles_also_used
            )
        ):
            raise ExternalContractError(
                "operator representation reused source roles are invalid"
            )
        if bool(self.source_roles_also_used) != self.dual_use_declared:
            raise ExternalContractError(
                "operator representation dual source use must be declared exactly"
            )
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


def validate_causal_register(
    index: object,
    values: object,
    source_valid: object,
    issued_at: object,
    contract: CausalRegisterContract,
) -> CausalRegister:
    """Validate row-level Phi custody without promoting a theorem claim."""

    contract.validate()
    stamps = _index(index, "causal register")
    raw = _float_vector("causal register", values, len(stamps))
    declared_valid = _bool_vector(
        "causal register source validity", source_valid, len(stamps)
    )
    issue = _issue_vector("causal register", issued_at, len(stamps))
    causal = issue <= stamps
    finite = np.isfinite(raw)
    in_range = finite & (raw >= contract.value_min) & (raw <= contract.value_max)
    valid = declared_valid & causal & in_range
    emitted = np.full(raw.size, np.nan, dtype=np.float64)
    emitted[valid] = raw[valid]
    runtime_checks = {
        "at_least_one_valid_row": bool(valid.any()),
        "all_emitted_rows_causal": bool(np.all(causal[valid])),
        "all_emitted_rows_finite": bool(np.all(finite[valid])),
        "all_emitted_rows_within_declared_bounds": bool(np.all(in_range[valid])),
        "source_validity_gate_applied": bool(np.all(valid <= declared_valid)),
        "invalid_rows_imputed_or_clipped": False,
        "future_rows_rejected": int((declared_valid & ~causal).sum()),
        "out_of_range_rows_rejected": int((declared_valid & causal & ~in_range).sum()),
    }
    instrument_complete = bool(
        runtime_checks["at_least_one_valid_row"]
        and runtime_checks["all_emitted_rows_causal"]
        and runtime_checks["all_emitted_rows_finite"]
        and runtime_checks["all_emitted_rows_within_declared_bounds"]
        and runtime_checks["source_validity_gate_applied"]
    )
    record = contract.record()
    record["instrument_complete"] = instrument_complete
    record["runtime_checks"] = runtime_checks
    record["valid_rows"] = int(valid.sum())
    record["quarantined_rows"] = int((~valid).sum())
    record["complete"] = bool(record["complete"] and instrument_complete)
    record["observer_emission_authorized"] = bool(
        record["observer_emission_authorized"] and instrument_complete
    )
    return CausalRegister(values=emitted, valid=valid, contract=record)


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
        if channel.normalization in {
            "reference_relative",
            "absolute_reference_relative",
        }:
            denominator = np.abs(reference)
            denominator_valid = denominator > channel.reference_floor
        else:
            denominator = np.full(n, float(channel.fixed_scale), dtype=np.float64)
            denominator_valid = np.ones(n, dtype=np.bool_)

        raw = np.full(n, np.nan, dtype=np.float64)
        computable = finite & denominator_valid
        if channel.normalization == "absolute_reference_relative":
            raw[computable] = (
                np.abs(observed[computable] - reference[computable])
                / denominator[computable]
            )
        else:
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
        "construction_spec_hash_bound": _is_sha256(
            contract.construction_spec_sha256
        ),
        "dual_source_use_declared_exactly": bool(
            bool(contract.source_roles_also_used) == contract.dual_use_declared
        ),
        "prama_variables_used": False,
        "future_values_used": False,
        "all_emitted_rows_causal": bool(np.all(causal[valid])),
        "invalid_values_imputed": False,
    }
    complete = bool(
        checks["at_least_one_valid_row"]
        and checks["representation_target_exact"]
        and checks["operational_coupling_declared"]
        and checks["construction_spec_hash_bound"]
        and checks["dual_source_use_declared_exactly"]
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
