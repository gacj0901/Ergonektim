from __future__ import annotations

from dataclasses import replace
import unittest

import numpy as np
import pandas as pd

from ergonektim.contracts import (
    CausalRegisterContract,
    ExternalContractError,
    ExternalDisplacementChannel,
    validate_causal_register,
)
from ergonektim.panel import AssessmentContractError, _validated_inputs
from ergonektim.synthetic import synthetic_assessment_fixture
from ergonektim.telemetry import (
    TelemetricContract,
    TelemetricStatusError,
    propagate_causal_interval,
)
from ergonektim.validation import (
    ConditionNullContractError,
    ConditionNullDesign,
    circular_shift_condition_reference,
)


class StrictBooleanBoundaryTests(unittest.TestCase):
    def test_programmatic_sigma_op_rejects_truthy_nonbooleans(self) -> None:
        inputs, _ = synthetic_assessment_fixture()
        invalid_vectors = (
            np.full(len(inputs.index), "false"),
            np.full(len(inputs.index), "invalid"),
            np.full(len(inputs.index), np.nan),
            np.full(len(inputs.index), 2),
        )
        for invalid in invalid_vectors:
            with self.subTest(dtype=invalid.dtype, sample=invalid[0]):
                with self.assertRaises(AssessmentContractError):
                    _validated_inputs(replace(inputs, sigma_op=invalid))

    def test_programmatic_boolean_vectors_accept_only_boolean_dtype(self) -> None:
        inputs, _ = synthetic_assessment_fixture()
        arrays = _validated_inputs(
            replace(
                inputs,
                sigma_op=np.ones(len(inputs.index), dtype=np.bool_),
                planned=np.zeros(len(inputs.index), dtype=np.bool_),
            )
        )
        self.assertEqual(arrays["sigma_op"].dtype.kind, "b")
        self.assertEqual(arrays["planned"].dtype.kind, "b")

    def test_causal_register_validity_rejects_string_false(self) -> None:
        index = pd.date_range("2020-01-01", periods=2, freq="h", tz="UTC")
        contract = CausalRegisterContract(
            source_system="test",
            source_owner="test",
            register_role="internal_state",
            construction_id="test_v1",
            normalization_id="unit_interval",
            construction_spec_sha256="a" * 64,
            input_roles=("internal_register_state",),
        )
        with self.assertRaises(ExternalContractError):
            validate_causal_register(
                index,
                np.array([0.2, 0.3]),
                np.array(["false", "false"]),
                index,
                contract,
            )

    def test_contract_boolean_metadata_is_exact(self) -> None:
        channel = ExternalDisplacementChannel(
            name="w",
            observation_role="observation",
            reference_role="reference",
            normalization="reference_relative",
            normalization_id="relative_v1",
            source_system="test",
            source_owner="test",
            reference_available_by_t="false",  # type: ignore[arg-type]
        )
        with self.assertRaises(ExternalContractError):
            channel.validate()

    def test_telemetry_rejects_numeric_validity_mask(self) -> None:
        contract = TelemetricContract(q_normalization_id="unit_test")
        with self.assertRaises(TelemetricStatusError):
            propagate_causal_interval([0.1, 0.2], [1, 0], contract)

    def test_condition_null_rejects_string_masks(self) -> None:
        index = pd.date_range("2020-01-01", periods=8, freq="h", tz="UTC")
        design = ConditionNullDesign(
            pre_window=1,
            post_window=1,
            memory_exclusion_rows=1,
            minimum_eligibility_fraction=0.5,
            minimum_reference_shifts=1,
        )
        with self.assertRaises(ConditionNullContractError):
            circular_shift_condition_reference(
                index,
                np.full(8, "false"),
                np.linspace(0.0, 1.0, 8),
                np.ones(8, dtype=np.bool_),
                design=design,
            )


if __name__ == "__main__":
    unittest.main()
