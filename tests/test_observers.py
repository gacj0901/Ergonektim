from __future__ import annotations

import unittest

import numpy as np

from ergonektim.observers import performance_status, stability_status


class ObserverSemanticTests(unittest.TestCase):
    def test_negative_gradient_is_not_named_as_collapse(self) -> None:
        result = stability_status(
            sigma_op=np.array([True, True]),
            margin=np.array([1.0, 1.0]),
            gradient=np.array([-1e-12, 0.0]),
            observability_clear=np.array([True, True]),
        )
        self.assertEqual(
            result["status_path"].tolist(),
            ["viable_with_negative_gradient", "viable"],
        )
        self.assertTrue(
            result["invariants"]["negative_gradient_definition_exact"]
        )

    def test_zero_ledger_is_distinct_from_positive_balance(self) -> None:
        result = performance_status(
            accumulated_debt=np.array([0.0, 1.0, 1.0, 2.0]),
            regeneration_input=np.array([0.0, 1.0, 2.0, 1.0]),
            margin=np.ones(4),
            effective_flow=np.ones(4),
            observability_clear=np.ones(4, dtype=np.bool_),
            kappa=1.0,
            h=1.0,
        )
        self.assertEqual(
            result["status_path"].tolist(),
            [
                "structural_ledger_inactive",
                "balanced",
                "solvent",
                "insolvent",
            ],
        )
        self.assertTrue(
            result["invariants"]["inactive_ledger_definition_exact"]
        )


if __name__ == "__main__":
    unittest.main()
