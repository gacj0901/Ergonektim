"""Canonical bilingual diagnostic-signal contract.

Scientific codes and evidence are locale invariant. Presentation strings are
resolved for both supported locales when a signal is built, so exported
artifacts remain self-describing without recomputing a diagnosis.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
from importlib.resources import files
import json
import math
from typing import Any, Mapping


SCHEMA_VERSION = "ergonektim.diagnostic-signal.v1"
SUPPORTED_LOCALES = ("en", "es")
SCIENTIFIC_FIELDS = (
    "schema_version",
    "observer",
    "code",
    "severity",
    "signal",
    "icon",
    "eligible",
    "timestamp_utc",
    "evidence",
)


class SignalContractError(ValueError):
    """Raised when a diagnostic signal violates the product contract."""


def _resource_json(*parts: str) -> dict[str, Any]:
    resource = files("ergonektim").joinpath("resources", *parts)
    return json.loads(resource.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _registry() -> dict[str, Any]:
    return _resource_json("status_registry.json")


@lru_cache(maxsize=len(SUPPORTED_LOCALES))
def _catalog(locale: str) -> dict[str, Any]:
    if locale not in SUPPORTED_LOCALES:
        raise SignalContractError(f"unsupported locale: {locale}")
    return _resource_json("locales", f"{locale}.json")


def _status_map(payload: Mapping[str, Any]) -> dict[tuple[str, str], Mapping[str, Any]]:
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for observer, observer_payload in payload["observers"].items():
        for code, status in observer_payload["statuses"].items():
            result[(observer, code)] = status
    return result


def validate_resource_parity() -> bool:
    """Fail if registry and bilingual catalogs do not cover identical states."""

    registry = _registry()
    registry_keys = set(_status_map(registry))
    if not registry_keys:
        raise SignalContractError("empty status registry")
    for locale in SUPPORTED_LOCALES:
        catalog = _catalog(locale)
        if catalog.get("locale") != locale:
            raise SignalContractError(f"catalog locale mismatch: {locale}")
        catalog_keys = set(_status_map(catalog))
        if catalog_keys != registry_keys:
            missing = sorted(registry_keys - catalog_keys)
            extra = sorted(catalog_keys - registry_keys)
            raise SignalContractError(
                f"catalog coverage mismatch for {locale}: missing={missing}, extra={extra}"
            )
        for observer, observer_payload in catalog["observers"].items():
            if not str(observer_payload.get("name", "")).strip():
                raise SignalContractError(f"missing observer name: {locale}/{observer}")
            if not str(observer_payload.get("claim_boundary", "")).strip():
                raise SignalContractError(
                    f"missing claim boundary: {locale}/{observer}"
                )
            for code, status in observer_payload["statuses"].items():
                for field in ("label", "explanation", "review_action"):
                    if not str(status.get(field, "")).strip():
                        raise SignalContractError(
                            f"missing {field}: {locale}/{observer}/{code}"
                        )
    return True


def status_codes() -> dict[str, tuple[str, ...]]:
    """Return the frozen observer-to-status inventory."""

    return {
        observer: tuple(sorted(payload["statuses"]))
        for observer, payload in sorted(_registry()["observers"].items())
    }


def _canonical_utc(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SignalContractError("timestamp_utc must be a nonempty string")
    candidate = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise SignalContractError("timestamp_utc is not ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise SignalContractError("timestamp_utc must carry a UTC offset")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_json_value(value: Any, path: str = "evidence") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SignalContractError(f"non-finite value at {path}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise SignalContractError(f"non-string evidence key at {path}")
            _validate_json_value(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _validate_json_value(child, f"{path}[{index}]")
        return
    raise SignalContractError(f"unsupported JSON value at {path}: {type(value).__name__}")


def build_diagnostic_signal(
    observer: str,
    code: str,
    *,
    eligible: bool,
    timestamp_utc: str,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one self-describing bilingual signal from frozen status metadata."""

    validate_resource_parity()
    registry = _registry()["observers"]
    if observer not in registry:
        raise SignalContractError(f"unknown observer: {observer}")
    statuses = registry[observer]["statuses"]
    if code not in statuses:
        raise SignalContractError(f"unknown status: {observer}/{code}")
    if not isinstance(eligible, bool):
        raise SignalContractError("eligible must be boolean")
    if not isinstance(evidence, Mapping):
        raise SignalContractError("evidence must be a mapping")
    _validate_json_value(evidence)

    status = statuses[code]
    is_indeterminate = status["severity"] == "indeterminate"
    if is_indeterminate == eligible:
        raise SignalContractError(
            "indeterminate statuses must be ineligible; substantive statuses must be eligible"
        )

    presentations: dict[str, dict[str, str]] = {}
    for locale in SUPPORTED_LOCALES:
        observer_text = _catalog(locale)["observers"][observer]
        status_text = observer_text["statuses"][code]
        presentations[locale] = {
            "observer_name": observer_text["name"],
            "label": status_text["label"],
            "explanation": status_text["explanation"],
            "review_action": status_text["review_action"],
            "claim_boundary": observer_text["claim_boundary"],
        }

    signal = {
        "schema_version": SCHEMA_VERSION,
        "observer": observer,
        "code": code,
        "severity": status["severity"],
        "signal": status["signal"],
        "icon": status["icon"],
        "eligible": eligible,
        "timestamp_utc": _canonical_utc(timestamp_utc),
        "evidence": deepcopy(dict(evidence)),
        "presentations": presentations,
    }
    validate_signal(signal)
    return signal


def validate_signal(signal: Mapping[str, Any]) -> bool:
    """Validate a materialized signal against the executable core contract."""

    expected_fields = set(SCIENTIFIC_FIELDS) | {"presentations"}
    if set(signal) != expected_fields:
        raise SignalContractError("signal fields do not match the canonical contract")
    if signal["schema_version"] != SCHEMA_VERSION:
        raise SignalContractError("unsupported signal schema")
    observer = signal["observer"]
    code = signal["code"]
    registry = _registry()["observers"]
    if observer not in registry or code not in registry[observer]["statuses"]:
        raise SignalContractError("signal observer/status is not registered")
    status = registry[observer]["statuses"][code]
    for field in ("severity", "signal", "icon"):
        if signal[field] != status[field]:
            raise SignalContractError(f"signal {field} differs from registry")
    if (signal["severity"] == "indeterminate") == bool(signal["eligible"]):
        raise SignalContractError("signal eligibility conflicts with severity")
    _canonical_utc(signal["timestamp_utc"])
    _validate_json_value(signal["evidence"])
    presentations = signal["presentations"]
    if set(presentations) != set(SUPPORTED_LOCALES):
        raise SignalContractError("signal is not self-describing in both locales")
    for locale in SUPPORTED_LOCALES:
        required = {
            "observer_name",
            "label",
            "explanation",
            "review_action",
            "claim_boundary",
        }
        if set(presentations[locale]) != required:
            raise SignalContractError(f"invalid presentation fields for {locale}")
        if not all(str(value).strip() for value in presentations[locale].values()):
            raise SignalContractError(f"empty presentation text for {locale}")
    return True


def scientific_payload(signal: Mapping[str, Any]) -> dict[str, Any]:
    """Return the locale-invariant portion used for custody and hashing."""

    validate_signal(signal)
    return {field: deepcopy(signal[field]) for field in SCIENTIFIC_FIELDS}


def presentation_for(signal: Mapping[str, Any], locale: str) -> dict[str, Any]:
    """Select one locale without mutating or recomputing scientific content."""

    validate_signal(signal)
    if locale not in SUPPORTED_LOCALES:
        raise SignalContractError(f"unsupported locale: {locale}")
    return {
        **scientific_payload(signal),
        "locale": locale,
        "presentation": deepcopy(signal["presentations"][locale]),
    }
