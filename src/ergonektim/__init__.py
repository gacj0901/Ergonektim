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
    ExternalDisplacementChannel,
    ExternalContractError,
    OperatorRepresentationContract,
    realize_external_displacement,
    validate_operator_representation,
)
from .panel import AssessmentInputs, evaluate_assessment, write_assessment
from .telemetry import TelemetricContract
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
    "ExternalDisplacementChannel",
    "ExternalContractError",
    "OperatorRepresentationContract",
    "realize_external_displacement",
    "validate_operator_representation",
    "AssessmentInputs",
    "evaluate_assessment",
    "write_assessment",
    "TelemetricContract",
    "InputBundleError",
    "LoadedAssessmentBundle",
    "load_assessment_bundle",
]

__version__ = "0.1.0.dev0"
