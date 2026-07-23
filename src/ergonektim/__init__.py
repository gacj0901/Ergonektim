"""ERGONEKTIM product contracts."""

from .signals import (
    SignalContractError,
    build_diagnostic_signal,
    presentation_for,
    scientific_payload,
    status_codes,
    validate_resource_parity,
    validate_signal,
)
from .contracts import (
    CausalRegister,
    CausalRegisterContract,
    ExternalDisplacementChannel,
    ExternalContractError,
    OperatorRepresentationContract,
    realize_external_displacement,
    validate_causal_register,
    validate_operator_representation,
)
from .artifact import ArtifactVerificationError, verify_assessment_artifact
from .panel import AssessmentInputs, evaluate_assessment, write_assessment
from .reachability import (
    ReachabilityAuditError,
    audit_lambda_reachability,
    constant_input_state,
    minimum_constant_input_bins,
    retention_factor,
)
from .telemetry import TelemetricContract
from .validation import (
    ConditionNullContractError,
    ConditionNullDesign,
    circular_shift_condition_reference,
)
from .input_bundle import (
    InputBundleError,
    LoadedAssessmentBundle,
    load_assessment_bundle,
)

__all__ = [
    "SignalContractError",
    "build_diagnostic_signal",
    "presentation_for",
    "scientific_payload",
    "status_codes",
    "validate_resource_parity",
    "validate_signal",
    "CausalRegisterContract",
    "CausalRegister",
    "ExternalDisplacementChannel",
    "ExternalContractError",
    "OperatorRepresentationContract",
    "realize_external_displacement",
    "validate_causal_register",
    "validate_operator_representation",
    "ArtifactVerificationError",
    "verify_assessment_artifact",
    "AssessmentInputs",
    "evaluate_assessment",
    "write_assessment",
    "ReachabilityAuditError",
    "audit_lambda_reachability",
    "constant_input_state",
    "minimum_constant_input_bins",
    "retention_factor",
    "ConditionNullContractError",
    "ConditionNullDesign",
    "circular_shift_condition_reference",
    "TelemetricContract",
    "InputBundleError",
    "LoadedAssessmentBundle",
    "load_assessment_bundle",
]

__version__ = "0.1.0.dev4"
