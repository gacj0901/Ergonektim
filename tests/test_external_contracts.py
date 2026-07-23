from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ergonektim.contracts import (
    ExternalContractError,
    ExternalDisplacementChannel,
    realize_external_displacement,
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


if __name__ == "__main__":
    unittest.main()
