from __future__ import annotations

import math
import unittest

import numpy as np

from ergonektim.reachability import (
    ReachabilityAuditError,
    audit_lambda_reachability,
    constant_input_state,
    minimum_constant_input_bins,
)


class ReachabilityAuditTests(unittest.TestCase):
    @staticmethod
    def _xi(delta: np.ndarray, *, tau: float) -> np.ndarray:
        r = math.exp(-1.0 / tau)
        state = 0.0
        values = []
        for input_value in delta:
            state = r * state + (1.0 - r) * float(input_value)
            values.append(state)
        return np.asarray(values)

    def test_exact_constant_input_recurrence(self) -> None:
        state = constant_input_state(
            3.0, xi_initial=0.0, bins=2, h=1.0, tau=2.0
        )
        r = math.exp(-0.5)
        self.assertAlmostEqual(state, 3.0 * (1.0 - r**2))

    def test_strict_crossing_bin(self) -> None:
        bins = minimum_constant_input_bins(
            3.0, xi_initial=0.0, theta=2.0, h=1.0, tau=2.0
        )
        self.assertIsNotNone(bins)
        assert bins is not None
        self.assertLessEqual(
            constant_input_state(
                3.0, xi_initial=0.0, bins=bins - 1, h=1.0, tau=2.0
            ),
            2.0,
        )
        self.assertGreater(
            constant_input_state(
                3.0, xi_initial=0.0, bins=bins, h=1.0, tau=2.0
            ),
            2.0,
        )
        self.assertIsNone(
            minimum_constant_input_bins(
                2.0, xi_initial=0.0, theta=2.0, h=1.0, tau=2.0
            )
        )

    def test_unreachable_under_observed_bound_is_not_physical_claim(self) -> None:
        delta = np.full(24, 0.5)
        result = audit_lambda_reachability(
            delta,
            self._xi(delta, tau=336.0),
            np.full(24, 2.0),
            h=1.0,
            tau=336.0,
        )
        self.assertEqual(result["status"], "unreachable_under_empirical_bound")
        self.assertEqual(
            result["bound_kind"], "empirical_observed_not_physical"
        )
        self.assertFalse(result["threshold_recalibrated"])
        self.assertTrue(all(result["invariants"].values()))

    def test_observed_crossing_has_priority(self) -> None:
        delta = np.array([3.0, 3.0])
        result = audit_lambda_reachability(
            delta,
            self._xi(delta, tau=1.0),
            np.array([2.0, 2.0]),
            h=1.0,
            tau=1.0,
        )
        self.assertEqual(result["status"], "observed_crossing")
        self.assertEqual(result["first_observed_crossing_row"], 1)

    def test_bound_must_cover_observations(self) -> None:
        delta = np.array([0.1, 0.5])
        with self.assertRaises(ReachabilityAuditError):
            audit_lambda_reachability(
                delta,
                self._xi(delta, tau=336.0),
                np.array([2.0, 2.0]),
                h=1.0,
                tau=336.0,
                empirical_input_bound=0.4,
            )

    def test_inconsistent_xi_is_rejected(self) -> None:
        with self.assertRaises(ReachabilityAuditError):
            audit_lambda_reachability(
                np.array([0.1, 0.1]),
                np.array([0.0, 2.1]),
                np.array([2.0, 2.0]),
                h=1.0,
                tau=336.0,
            )


if __name__ == "__main__":
    unittest.main()
