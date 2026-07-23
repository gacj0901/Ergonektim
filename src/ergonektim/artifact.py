"""Adversarial, byte-exact replay verification for assessment artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .input_bundle import load_assessment_bundle
from .panel import canonical_assessment_bytes, evaluate_assessment


ASSESSMENT_SCHEMA = "ergonektim.assessment.v1.3"


class ArtifactVerificationError(ValueError):
    """Raised when a received assessment cannot be reproduced exactly."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _expected_hash(value: str | None) -> str | None:
    if value is None:
        return None
    token = value.strip().lower()
    if len(token) != 64 or any(character not in "0123456789abcdef" for character in token):
        raise ArtifactVerificationError("expected_sha256 must be 64 lowercase hex digits")
    return token


def load_canonical_assessment(path: str | Path) -> tuple[dict[str, Any], bytes]:
    """Load strict JSON and reject noncanonical or unsupported artifacts."""

    target = Path(path)
    try:
        raw = target.read_bytes()
        text = raw.decode("utf-8")

        def reject_constant(token: str) -> None:
            raise ArtifactVerificationError(
                f"non-finite JSON constant is forbidden: {token}"
            )

        payload = json.loads(text, parse_constant=reject_constant)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactVerificationError(
            "assessment artifact is not valid canonical UTF-8 JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise ArtifactVerificationError("assessment artifact root must be an object")
    if payload.get("schema_version") != ASSESSMENT_SCHEMA:
        raise ArtifactVerificationError("unsupported assessment schema_version")
    if canonical_assessment_bytes(payload) != raw:
        raise ArtifactVerificationError(
            "assessment artifact is not in canonical byte representation"
        )
    return payload, raw


def verify_assessment_artifact(
    artifact_path: str | Path,
    bundle_path: str | Path,
    recertification_path: str | Path,
    *,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Recompute an assessment from custody inputs and compare every byte."""

    _, received = load_canonical_assessment(artifact_path)
    received_sha256 = _sha256(received)
    expected = _expected_hash(expected_sha256)
    if expected is not None and received_sha256 != expected:
        raise ArtifactVerificationError(
            "assessment artifact SHA-256 differs from the expected digest"
        )

    loaded = load_assessment_bundle(bundle_path)
    recomputed = evaluate_assessment(
        loaded.inputs,
        telemetric_contract=loaded.telemetric_contract,
        recertification_path=recertification_path,
        kernel_config=loaded.kernel_config,
        input_binding=loaded.input_binding,
    )
    replay = canonical_assessment_bytes(recomputed)
    if replay != received:
        raise ArtifactVerificationError(
            "assessment artifact differs from deterministic custody replay"
        )
    return {
        "status": "verified",
        "verification_mode": "byte_exact_deterministic_replay",
        "artifact_sha256": received_sha256,
        "bundle_sha256": loaded.input_binding["bundle_sha256"],
        "assessment_schema": ASSESSMENT_SCHEMA,
        "rows": recomputed["summary"]["rows"],
        "observer_count": recomputed["summary"]["observer_count"],
        "global_scalar_emitted": recomputed["summary"]["global_scalar_emitted"],
        "all_observer_invariants_recomputed": True,
        "received_bytes_equal_replay_bytes": True,
    }
