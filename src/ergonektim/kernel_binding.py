"""Fail-closed binding to the certified PRAMA Protokol 0.3.0 release."""

from __future__ import annotations

import hashlib
from importlib import import_module
from importlib.resources import files
import json
from pathlib import Path
from typing import Any


class KernelBindingError(RuntimeError):
    """Raised when the installed kernel cannot prove the frozen binding."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def binding_manifest() -> dict[str, Any]:
    resource = files("ergonektim").joinpath(
        "resources", "prama_v0_3_0_binding.json"
    )
    return json.loads(resource.read_text(encoding="utf-8"))


def verify_prama_binding(
    recertification_path: str | Path | None,
    *,
    require_recertification_artifact: bool = True,
) -> dict[str, Any]:
    """Verify package version, kernel bytes, and the public recertification.

    Canonical ERGONEKTIM runs require the machine-readable recertification
    artifact. Development callers may explicitly disable that requirement,
    but the returned binding records the weaker state.
    """

    manifest = binding_manifest()
    prama = import_module("prama_protokol")
    kernel = import_module("prama_protokol.kernel_v3")
    installed_version = str(getattr(prama, "__version__", ""))
    if installed_version != manifest["prama_version"]:
        raise KernelBindingError(
            f"PRAMA version mismatch: {installed_version!r} != "
            f"{manifest['prama_version']!r}"
        )
    kernel_path = Path(kernel.__file__).resolve()
    kernel_hash = _sha256(kernel_path)
    expected_kernel_hash = manifest["hashes"]["python_kernel_v3"]
    if kernel_hash != expected_kernel_hash:
        raise KernelBindingError("installed PRAMA Python kernel hash mismatch")

    artifact_record: dict[str, Any] = {
        "required": require_recertification_artifact,
        "verified": False,
        "artifact_file": None,
        "sha256": None,
    }
    if recertification_path is None:
        if require_recertification_artifact:
            raise KernelBindingError("canonical run requires recertification_path")
    else:
        artifact_path = Path(recertification_path).resolve()
        if not artifact_path.is_file():
            raise KernelBindingError("recertification artifact does not exist")
        artifact_hash = _sha256(artifact_path)
        if artifact_hash != manifest["recertification"]["sha256"]:
            raise KernelBindingError("recertification artifact hash mismatch")
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        checks = {
            "artifact": payload.get("artifact")
            == manifest["recertification"]["artifact"],
            "passed": payload.get("passed") is True,
            "outcome_free": payload.get("outcomes_accessed") is False,
            "python_version": payload.get("version", {}).get("python")
            == manifest["prama_version"],
            "rust_version": payload.get("version", {}).get("rust")
            == manifest["prama_version"],
            "python_kernel": payload.get("hashes", {}).get("python_kernel_v3")
            == manifest["hashes"]["python_kernel_v3"],
            "rust_kernel": payload.get("hashes", {}).get("rust_kernel_v3")
            == manifest["hashes"]["rust_kernel_v3"],
            "specification": payload.get("hashes", {}).get("specification")
            == manifest["hashes"]["specification"],
        }
        if not all(checks.values()):
            failed = sorted(name for name, passed in checks.items() if not passed)
            raise KernelBindingError(
                f"recertification content mismatch: {', '.join(failed)}"
            )
        artifact_record = {
            "required": require_recertification_artifact,
            "verified": True,
            "artifact_file": artifact_path.name,
            "sha256": artifact_hash,
            "checks": checks,
        }

    return {
        "schema_version": manifest["schema_version"],
        "verified": bool(
            installed_version == manifest["prama_version"]
            and kernel_hash == expected_kernel_hash
            and (
                artifact_record["verified"]
                or not require_recertification_artifact
            )
        ),
        "prama_version": installed_version,
        "python_kernel_file": kernel_path.name,
        "python_kernel_sha256": kernel_hash,
        "recertification": artifact_record,
        "outcomes_accessed": False,
    }
