from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from ergonektim.cli import main
from ergonektim.input_bundle import InputBundleError, load_assessment_bundle
from ergonektim.synthetic import write_synthetic_bundle


RECERTIFICATION = os.environ.get("ERGONEKTIM_PRAMA_RECERTIFICATION")


class InputBundleTests(unittest.TestCase):
    def test_bundle_is_closed_hashed_and_outcome_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle = write_synthetic_bundle(Path(temporary) / "bundle")
            loaded = load_assessment_bundle(bundle)
            binding = loaded.input_binding
            self.assertTrue(binding["verified"])
            self.assertEqual(binding["schema_version"], "ergonektim.input-bundle.v1")
            self.assertEqual(binding["rows"], 240)
            self.assertEqual(len(binding["manifest_sha256"]), 64)
            self.assertEqual(len(binding["data_sha256"]), 64)
            self.assertEqual(len(binding["bundle_sha256"]), 64)
            self.assertFalse(binding["undeclared_columns_accessed"])
            self.assertFalse(binding["outcome_roles_declared"])
            self.assertFalse(binding["outcome_columns_accessed"])
            self.assertIsNone(loaded.inputs.external_cause_labels)

    def test_undeclared_column_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle = write_synthetic_bundle(Path(temporary) / "bundle")
            data_path = bundle / "timeseries.csv"
            frame = pd.read_csv(data_path)
            frame["undeclared_outcome"] = 0
            frame.to_csv(data_path, index=False)
            with self.assertRaisesRegex(InputBundleError, "undeclared"):
                load_assessment_bundle(bundle)

    def test_extra_bundle_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle = write_synthetic_bundle(Path(temporary) / "bundle")
            (bundle / "notes.txt").write_text("not part of custody", encoding="utf-8")
            with self.assertRaisesRegex(InputBundleError, "two-file"):
                load_assessment_bundle(bundle)

    def test_negative_regeneration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle = write_synthetic_bundle(Path(temporary) / "bundle")
            data_path = bundle / "timeseries.csv"
            frame = pd.read_csv(data_path)
            frame.loc[10, "u_lambda"] = -0.1
            frame.to_csv(data_path, index=False)
            with self.assertRaisesRegex(InputBundleError, "nonnegative"):
                load_assessment_bundle(bundle)

    def test_timezone_naive_timestamp_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle = write_synthetic_bundle(Path(temporary) / "bundle")
            data_path = bundle / "timeseries.csv"
            frame = pd.read_csv(data_path, dtype=str, keep_default_na=False)
            frame.loc[0, "timestamp_utc"] = "2020-01-01T00:00:00"
            frame.to_csv(data_path, index=False)
            with self.assertRaisesRegex(InputBundleError, "explicit UTC offset"):
                load_assessment_bundle(bundle)

    def test_manifest_schema_is_packaged_and_closed(self) -> None:
        import importlib.resources

        path = importlib.resources.files("ergonektim").joinpath(
            "resources", "schemas", "input-bundle-manifest.schema.json"
        )
        schema = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "ergonektim.input-bundle.v1",
        )


@unittest.skipUnless(RECERTIFICATION, "canonical PRAMA recertification not supplied")
class CliTests(unittest.TestCase):
    def test_verify_and_assess_are_bilingual_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = write_synthetic_bundle(root / "bundle")
            verification_stdout = io.StringIO()
            with redirect_stdout(verification_stdout):
                code = main(
                    [
                        "verify",
                        "--bundle",
                        str(bundle),
                        "--recertification",
                        str(RECERTIFICATION),
                        "--language",
                        "es",
                    ]
                )
            self.assertEqual(code, 0)
            verification = json.loads(verification_stdout.getvalue())
            self.assertEqual(verification["language"], "es")
            self.assertEqual(verification["status"], "verified")

            artifacts: list[bytes] = []
            for language in ("es", "en"):
                output = root / f"assessment-{language}.json"
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = main(
                        [
                            "assess",
                            "--bundle",
                            str(bundle),
                            "--recertification",
                            str(RECERTIFICATION),
                            "--output",
                            str(output),
                            "--language",
                            language,
                        ]
                    )
                self.assertEqual(code, 0)
                terminal = json.loads(stdout.getvalue())
                self.assertEqual(terminal["language"], language)
                self.assertEqual(terminal["observer_count"], 6)
                artifacts.append(output.read_bytes())
            self.assertEqual(artifacts[0], artifacts[1])

            payload = json.loads(artifacts[0])
            self.assertTrue(payload["input_binding"]["verified"])
            self.assertEqual(
                payload["input_binding"]["bundle_sha256"],
                verification["bundle_sha256"],
            )
            self.assertTrue(
                payload["observer_invariants"]["causal_link"][
                    "attribution_does_not_require_labels"
                ]
            )
            self.assertFalse(payload["access"]["outcomes_accessed"])
            expected_digest = hashlib.sha256(artifacts[0]).hexdigest()
            self._assert_assess_existing(bundle, root / "assessment-es.json")
            self.assertEqual(
                hashlib.sha256((root / "assessment-es.json").read_bytes()).hexdigest(),
                expected_digest,
            )

    def _assert_assess_existing(self, bundle: Path, output: Path) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        original = output.read_bytes()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(
                [
                    "assess",
                    "--bundle",
                    str(bundle),
                    "--recertification",
                    str(RECERTIFICATION),
                    "--output",
                    str(output),
                    "--language",
                    "es",
                ]
            )
        self.assertEqual(code, 2)
        self.assertEqual(output.read_bytes(), original)
        failure = json.loads(stderr.getvalue())
        self.assertEqual(failure["status"], "failed_closed")


if __name__ == "__main__":
    unittest.main()
