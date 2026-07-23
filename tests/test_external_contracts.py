from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ergonektim.contracts import (
    CausalRegisterContract,
    ExternalContractError,
    ExternalDisplacementChannel,
    OperatorRepresentationContract,
    realize_external_displacement,
    validate_causal_register,
)


class ExternalDisplacementContractTests(unittest.TestCase):
    def test_absolute_reference_relative_preserves_unsigned_surprise(self) -> None:
        index = pd.date_range("2026-01-01T00:00:00Z", periods=3, freq="h")
        channel = ExternalDisplacementChannel(
            name="forecast_error",
            observation_role="observed_value",
            reference_role="operator_forecast",
            normalization="absolute_reference_relative",
            normalization_id="absolute_forecast_relative_v1",
            source_system="external_test_feed",
            source_owner="independent_test_owner",
            stress_sign=1,
            reference_floor=1.0,
        )
        result = realize_external_displacement(
            index,
            (channel,),
            {"forecast_error": np.array([90.0, 100.0, 120.0])},
            {"forecast_error": np.array([100.0, 100.0, 100.0])},
            {"forecast_error": np.ones(3, dtype=np.bool_)},
            {"forecast_error": index - pd.Timedelta(hours=1)},
        )
        np.testing.assert_array_equal(
            result.values[:, 0], np.array([0.1, 0.0, 0.2])
        )
        self.assertEqual(
            result.contract["contract_id"],
            "ergonektim.external-displacement.w.v1.1",
        )

    def test_absolute_normalization_rejects_directional_stress_sign(self) -> None:
        channel = ExternalDisplacementChannel(
            name="forecast_error",
            observation_role="observed_value",
            reference_role="operator_forecast",
            normalization="absolute_reference_relative",
            normalization_id="absolute_forecast_relative_v1",
            source_system="external_test_feed",
            source_owner="independent_test_owner",
            stress_sign=-1,
            reference_floor=1.0,
        )
        with self.assertRaisesRegex(ExternalContractError, "stress_sign"):
            channel.validate()


class CausalRegisterContractTests(unittest.TestCase):
    def _contract(self, **overrides: object) -> CausalRegisterContract:
        values = {
            "source_system": "independent_internal_register",
            "source_owner": "independent_owner",
            "register_role": "internal_organization",
            "construction_id": "internal_register_v1",
            "normalization_id": "unit_interval_v1",
            "construction_spec_sha256": "a" * 64,
            "input_roles": ("internal_equipment_state",),
        }
        values.update(overrides)
        return CausalRegisterContract(**values)

    def test_future_and_out_of_range_phi_rows_are_quarantined(self) -> None:
        index = pd.date_range("2026-01-01T00:00:00Z", periods=3, freq="h")
        result = validate_causal_register(
            index,
            np.array([0.2, 0.4, 1.2]),
            np.ones(3, dtype=np.bool_),
            pd.DatetimeIndex([index[0], index[2], index[2]]),
            self._contract(),
        )
        np.testing.assert_array_equal(
            result.valid, np.array([True, False, False])
        )
        self.assertEqual(result.contract["valid_rows"], 1)
        self.assertFalse(result.contract["observer_emission_authorized"])
        self.assertTrue(result.contract["instrument_complete"])

    def test_phi_lineage_rejects_outcomes_and_kernel_coordinates(self) -> None:
        for role in ("evaluation_outcome", "Xi", "external_displacement_w"):
            with self.subTest(role=role), self.assertRaises(ExternalContractError):
                self._contract(input_roles=(role,)).validate()


class OperatorRepresentationContractTests(unittest.TestCase):
    def test_reused_source_role_requires_explicit_dual_use(self) -> None:
        contract = OperatorRepresentationContract(
            source_system="operator_source",
            source_owner="operator",
            channel_role="operator_control_state",
            normalization_id="operator_policy_axis_v1",
            construction_spec_sha256="c" * 64,
            units="kernel_structural_excess_units",
            coupled_operational_parameter="operator_alarm_tier",
            source_roles_also_used=("external_reference",),
            dual_use_declared=False,
        )
        with self.assertRaisesRegex(ExternalContractError, "dual source use"):
            contract.validate()


if __name__ == "__main__":
    unittest.main()
