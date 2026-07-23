from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ergonektim.artifact import (
    ArtifactVerificationError,
    load_canonical_assessment,
)
from ergonektim.panel import canonical_assessment_bytes


class ArtifactContractTests(unittest.TestCase):
    def test_canonical_artifact_loads(self) -> None:
        payload = {
            "schema_version": "ergonektim.assessment.v1.2",
            "summary": {"rows": 1},
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "assessment.json"
            path.write_bytes(canonical_assessment_bytes(payload))
            loaded, raw = load_canonical_assessment(path)
        self.assertEqual(loaded, payload)
        self.assertEqual(raw, canonical_assessment_bytes(payload))

    def test_pretty_printed_or_nonfinite_artifact_is_rejected(self) -> None:
        payload = {
            "schema_version": "ergonektim.assessment.v1.2",
            "summary": {"rows": 1},
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "assessment.json"
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(
                ArtifactVerificationError, "canonical byte"
            ):
                load_canonical_assessment(path)
            path.write_text(
                '{"schema_version":"ergonektim.assessment.v1.2","x":NaN}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ArtifactVerificationError, "non-finite"):
                load_canonical_assessment(path)


if __name__ == "__main__":
    unittest.main()
