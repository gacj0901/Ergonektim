from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ergonektim.validation import (
    ConditionNullContractError,
    ConditionNullDesign,
    circular_shift_condition_reference,
)


class ConditionNullTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = pd.date_range(
            "2020-01-01", periods=72, freq="h", tz="UTC"
        )
        self.clear = np.ones(72, dtype=np.bool_)
        self.design = ConditionNullDesign(
            pre_window=2,
            post_window=2,
            memory_exclusion_rows=2,
            minimum_eligibility_fraction=0.5,
            minimum_reference_shifts=5,
            upper_tail_probability_maximum=0.05,
            minimum_effect=0.05,
            cadence_hours=1.0,
        )

    def test_reference_is_deterministic_and_restricted(self) -> None:
        planned = np.zeros(72, dtype=np.bool_)
        planned[12:14] = True
        planned[36:38] = True
        margin = np.sin(np.arange(72) / 5.0)
        first = circular_shift_condition_reference(
            self.index, planned, margin, self.clear, design=self.design
        )
        second = circular_shift_condition_reference(
            self.index, planned, margin, self.clear, design=self.design
        )
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "measured")
        self.assertFalse(
            first["reference"]["exact_unrestricted_permutation_p_value_claimed"]
        )
        self.assertTrue(all(first["invariants"].values()))
        self.assertGreaterEqual(
            first["reference"]["admissible_shift_count"],
            self.design.minimum_reference_shifts,
        )

    def test_zero_episode_and_zero_eligible_fail_closed(self) -> None:
        margin = np.linspace(0.0, 1.0, 72)
        empty = circular_shift_condition_reference(
            self.index,
            np.zeros(72, dtype=np.bool_),
            margin,
            self.clear,
            design=self.design,
        )
        self.assertEqual(empty["status"], "instrument_indeterminate")
        self.assertEqual(empty["reason"], "no_planned_episodes")

        planned = np.zeros(72, dtype=np.bool_)
        planned[12:14] = True
        blocked = circular_shift_condition_reference(
            self.index,
            planned,
            margin,
            np.zeros(72, dtype=np.bool_),
            design=self.design,
        )
        self.assertEqual(blocked["status"], "instrument_indeterminate")
        self.assertEqual(blocked["reason"], "no_eligible_observed_episodes")

    def test_irregular_cadence_is_rejected(self) -> None:
        index = self.index.delete(10)
        with self.assertRaises(ConditionNullContractError):
            circular_shift_condition_reference(
                index,
                np.zeros(len(index), dtype=np.bool_),
                np.zeros(len(index)),
                np.ones(len(index), dtype=np.bool_),
                design=self.design,
            )

    def test_insufficient_reference_geometry_fails_closed(self) -> None:
        planned = np.zeros(72, dtype=np.bool_)
        planned[12:14] = True
        design = ConditionNullDesign(
            pre_window=2,
            post_window=2,
            memory_exclusion_rows=30,
            minimum_eligibility_fraction=1.0,
            minimum_reference_shifts=100,
        )
        result = circular_shift_condition_reference(
            self.index,
            planned,
            np.linspace(0.0, 1.0, 72),
            self.clear,
            design=design,
        )
        self.assertEqual(result["status"], "instrument_indeterminate")
        self.assertIn(
            result["reason"],
            {
                "no_admissible_reference_shifts",
                "insufficient_admissible_reference_shifts",
            },
        )


if __name__ == "__main__":
    unittest.main()
