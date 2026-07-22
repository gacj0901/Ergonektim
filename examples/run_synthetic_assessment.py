#!/usr/bin/env python3
"""Run all six observers once on the deterministic synthetic fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ergonektim import evaluate_assessment, write_assessment
from ergonektim.synthetic import fixture_record, synthetic_assessment_fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recertification", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    inputs, telemetric_contract = synthetic_assessment_fixture()
    payload = evaluate_assessment(
        inputs,
        telemetric_contract=telemetric_contract,
        recertification_path=args.recertification,
    )
    payload["fixture"] = fixture_record()
    output = write_assessment(args.output, payload)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(
        json.dumps(
            {
                "output": str(output),
                "sha256": digest,
                "rows": payload["summary"]["rows"],
                "observer_count": payload["summary"]["observer_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
