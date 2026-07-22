from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from ergonektim import evaluate_assessment, write_assessment
from ergonektim.kernel_binding import binding_manifest, verify_prama_binding
from ergonektim.synthetic import synthetic_assessment_fixture


RECERTIFICATION = os.environ.get("ERGONEKTIM_PRAMA_RECERTIFICATION")


@unittest.skipUnless(RECERTIFICATION, "canonical PRAMA recertification not supplied")
class IntegratedPanelTests(unittest.TestCase):
    def test_final_prama_binding(self) -> None:
        binding = verify_prama_binding(Path(RECERTIFICATION))
        self.assertTrue(binding["verified"])
        self.assertEqual(binding["prama_version"], "0.3.0")
        self.assertTrue(binding["recertification"]["verified"])
        self.assertEqual(
            binding["recertification"]["sha256"],
            binding_manifest()["recertification"]["sha256"],
        )
        self.assertFalse(binding["outcomes_accessed"])

    def test_all_six_observers_run_once_and_write_one_file(self) -> None:
        inputs, telemetric_contract = synthetic_assessment_fixture()
        payload = evaluate_assessment(
            inputs,
            telemetric_contract=telemetric_contract,
            recertification_path=Path(RECERTIFICATION),
        )
        self.assertEqual(payload["summary"]["observer_count"], 6)
        self.assertEqual(payload["summary"]["rows"], 240)
        self.assertTrue(payload["summary"]["single_process_run"])
        self.assertTrue(payload["summary"]["bilingual_presentations_embedded"])
        self.assertFalse(payload["summary"]["global_scalar_emitted"])
        self.assertEqual(len(payload["condition_report"]), 2)
        self.assertEqual(
            set(payload["observer_summaries"]),
            {
                "telemetric_status",
                "stability_status",
                "performance_status",
                "condition_report",
                "causal_link",
                "estimation_fidelity",
            },
        )
        self.assertFalse(
            payload["observer_summaries"]["causal_link"]["global_scalar_emitted"]
        )
        first = payload["timeline"][0]["signals"]
        self.assertEqual(
            set(first),
            {
                "telemetric_status",
                "stability_status",
                "performance_status",
                "causal_link",
                "estimation_fidelity",
            },
        )
        for observer, checks in payload["observer_invariants"].items():
            self.assertTrue(all(checks.values()), observer)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "assessment.json"
            second_output = Path(temporary) / "assessment-second.json"
            write_assessment(output, payload)
            write_assessment(second_output, payload)
            loaded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(loaded["summary"], payload["summary"])
            self.assertEqual(output.read_bytes(), second_output.read_bytes())
            self.assertNotIn("NaN", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
