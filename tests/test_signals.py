from __future__ import annotations

from importlib.resources import files
import json
import math
import unittest

from ergonektim import (
    SignalContractError,
    build_diagnostic_signal,
    presentation_for,
    scientific_payload,
    status_codes,
    validate_resource_parity,
    validate_signal,
)


INDETERMINATE_CODES = {"instrument_indeterminate", "boundary_indeterminate"}


class DiagnosticSignalTests(unittest.TestCase):
    def test_registry_and_catalogs_have_identical_coverage(self) -> None:
        self.assertTrue(validate_resource_parity())
        inventory = status_codes()
        self.assertEqual(
            set(inventory),
            {
                "telemetric_status",
                "stability_status",
                "performance_status",
                "condition_report",
                "causal_link",
                "estimation_fidelity",
            },
        )

    def test_every_registered_status_builds_a_valid_signal(self) -> None:
        for observer, codes in status_codes().items():
            for code in codes:
                eligible = code not in INDETERMINATE_CODES
                signal = build_diagnostic_signal(
                    observer,
                    code,
                    eligible=eligible,
                    timestamp_utc="2026-07-21T12:00:00Z",
                    evidence={"contract_test": True},
                )
                self.assertTrue(validate_signal(signal))
                self.assertEqual(set(signal["presentations"]), {"en", "es"})
                self.assertNotIn("overall_score", signal)
                self.assertNotIn("global_status", signal)

    def test_language_switch_does_not_change_scientific_payload(self) -> None:
        signal = build_diagnostic_signal(
            "stability_status",
            "latent_collapse",
            eligible=True,
            timestamp_utc="2026-07-21T12:00:00Z",
            evidence={"M": 0.18, "G": -0.03},
        )
        english = presentation_for(signal, "en")
        spanish = presentation_for(signal, "es")
        self.assertNotEqual(
            english["presentation"]["label"], spanish["presentation"]["label"]
        )
        self.assertEqual(scientific_payload(signal), {
            key: english[key] for key in scientific_payload(signal)
        })
        self.assertEqual(
            {key: english[key] for key in scientific_payload(signal)},
            {key: spanish[key] for key in scientific_payload(signal)},
        )

    def test_indeterminate_status_must_be_ineligible(self) -> None:
        with self.assertRaises(SignalContractError):
            build_diagnostic_signal(
                "telemetric_status",
                "instrument_indeterminate",
                eligible=True,
                timestamp_utc="2026-07-21T12:00:00Z",
                evidence={},
            )

    def test_substantive_status_must_be_eligible(self) -> None:
        with self.assertRaises(SignalContractError):
            build_diagnostic_signal(
                "stability_status",
                "viable",
                eligible=False,
                timestamp_utc="2026-07-21T12:00:00Z",
                evidence={},
            )

    def test_nonfinite_evidence_is_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(SignalContractError):
                build_diagnostic_signal(
                    "stability_status",
                    "viable",
                    eligible=True,
                    timestamp_utc="2026-07-21T12:00:00Z",
                    evidence={"M": value},
                )

    def test_timestamp_must_be_utc(self) -> None:
        with self.assertRaises(SignalContractError):
            build_diagnostic_signal(
                "stability_status",
                "viable",
                eligible=True,
                timestamp_utc="2026-07-21T12:00:00-06:00",
                evidence={"M": 1.0, "G": 0.0},
            )

    def test_json_schema_is_packaged_and_closed(self) -> None:
        schema_path = files("ergonektim").joinpath(
            "resources", "schemas", "diagnostic-signal.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["presentations"]["required"], ["en", "es"]
        )


if __name__ == "__main__":
    unittest.main()
