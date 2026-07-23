"""Installed command-line interface for canonical ERGONEKTIM assessments."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from .artifact import ArtifactVerificationError, verify_assessment_artifact
from .contracts import ExternalContractError
from .input_bundle import InputBundleError, load_assessment_bundle
from .kernel_binding import KernelBindingError, verify_prama_binding
from .observers import ObserverContractError
from .panel import AssessmentContractError, evaluate_assessment, write_assessment
from .telemetry import TelemetricStatusError


MESSAGES = {
    "en": {
        "assessed": "Assessment completed; one deterministic artifact was written.",
        "verified": "Input bundle and certified kernel binding are valid.",
        "artifact_verified": "Assessment artifact matches an exact custody replay.",
        "error": "Assessment stopped fail-closed.",
        "exists": "Output already exists; use --overwrite to replace it.",
        "inside": "Output must be written outside the immutable input bundle.",
    },
    "es": {
        "assessed": "Evaluación completada; se escribió un único artefacto determinista.",
        "verified": "El paquete de entrada y la vinculación certificada son válidos.",
        "artifact_verified": (
            "El artefacto de evaluación coincide con una réplica exacta de custodia."
        ),
        "error": "La evaluación se detuvo en modo fail-closed.",
        "exists": "La salida ya existe; use --overwrite para sustituirla.",
        "inside": "La salida debe escribirse fuera del paquete de entrada inmutable.",
    },
}


class CliContractError(ValueError):
    """Raised when command-side custody or overwrite rules are violated."""


def _emit(payload: dict[str, Any], *, stream: Any = None) -> None:
    print(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False),
        file=sys.stdout if stream is None else stream,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ergonektim",
        description=(
            "Outcome-free aptadynamic viability assessment for electric power systems."
        ),
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "assess"):
        command = subcommands.add_parser(name)
        command.add_argument("--bundle", required=True, type=Path)
        command.add_argument("--recertification", required=True, type=Path)
        command.add_argument("--language", choices=("en", "es"), default="en")
        if name == "assess":
            command.add_argument("--output", required=True, type=Path)
            command.add_argument("--overwrite", action="store_true")
    artifact = subcommands.add_parser("verify-artifact")
    artifact.add_argument("--artifact", required=True, type=Path)
    artifact.add_argument("--bundle", required=True, type=Path)
    artifact.add_argument("--recertification", required=True, type=Path)
    artifact.add_argument("--expected-sha256")
    artifact.add_argument("--language", choices=("en", "es"), default="en")
    return parser


def _output_guard(bundle: Path, output: Path, overwrite: bool, language: str) -> None:
    bundle_resolved = bundle.resolve()
    output_resolved = output.resolve()
    if output_resolved.is_relative_to(bundle_resolved):
        raise CliContractError(MESSAGES[language]["inside"])
    if output.exists() and not overwrite:
        raise CliContractError(MESSAGES[language]["exists"])
    if output.exists() and not output.is_file():
        raise CliContractError(MESSAGES[language]["exists"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    language = str(args.language)
    try:
        if args.command == "verify-artifact":
            result = verify_assessment_artifact(
                args.artifact,
                args.bundle,
                args.recertification,
                expected_sha256=args.expected_sha256,
            )
            _emit(
                {
                    **result,
                    "message": MESSAGES[language]["artifact_verified"],
                    "language": language,
                }
            )
            return 0

        loaded = load_assessment_bundle(args.bundle)
        kernel_binding = verify_prama_binding(args.recertification)
        if args.command == "verify":
            _emit(
                {
                    "status": "verified",
                    "message": MESSAGES[language]["verified"],
                    "language": language,
                    "assessment_id": loaded.input_binding["assessment_id"],
                    "rows": loaded.input_binding["rows"],
                    "bundle_sha256": loaded.input_binding["bundle_sha256"],
                    "prama_version": kernel_binding["prama_version"],
                    "recertification_sha256": kernel_binding["recertification"][
                        "sha256"
                    ],
                }
            )
            return 0

        _output_guard(args.bundle, args.output, args.overwrite, language)
        payload = evaluate_assessment(
            loaded.inputs,
            telemetric_contract=loaded.telemetric_contract,
            recertification_path=args.recertification,
            kernel_config=loaded.kernel_config,
            input_binding=loaded.input_binding,
        )
        output = write_assessment(args.output, payload)
        _emit(
            {
                "status": "completed",
                "message": MESSAGES[language]["assessed"],
                "language": language,
                "output": str(output),
                "artifact_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "bundle_sha256": loaded.input_binding["bundle_sha256"],
                "rows": payload["summary"]["rows"],
                "observer_count": payload["summary"]["observer_count"],
                "global_scalar_emitted": payload["summary"][
                    "global_scalar_emitted"
                ],
            }
        )
        return 0
    except (
        AssessmentContractError,
        ArtifactVerificationError,
        CliContractError,
        ExternalContractError,
        InputBundleError,
        KernelBindingError,
        ObserverContractError,
        TelemetricStatusError,
        OSError,
    ) as exc:
        _emit(
            {
                "status": "failed_closed",
                "message": MESSAGES[language]["error"],
                "language": language,
                "error": str(exc),
            },
            stream=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
