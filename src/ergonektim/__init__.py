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

__all__ = [
    "SignalContractError",
    "build_diagnostic_signal",
    "presentation_for",
    "scientific_payload",
    "status_codes",
    "validate_resource_parity",
    "validate_signal",
]

__version__ = "0.1.0.dev0"
