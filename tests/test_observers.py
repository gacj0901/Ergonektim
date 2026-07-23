from __future__ import annotations

import unittest

import numpy as np

from ergonektim.contracts import CausalRegisterContract
from ergonektim.observers import (
    causal_link_status,
    performance_status,
    stability_status,
)
from ergonektim.synthetic import synthetic_assessment_fixture


class ObserverSemanticTests(unittest.TestCase):
    def test_causal_link_fails_closed_without_conformant_phi(self) -> None:
        inputs, _ = synthetic_assessment_fixture()
        result = causal_link_status(
            inputs.phi_register,
            inputs.displacement,
            np.ones(len(inputs.index), dtype=np.bool_),
            None,
            causal_register_contract=inputs.causal_register_contract,
            external_cause_labels_independent=None,
        )
        self.assertFalse(result["summary"]["observer_emits"])
        self.assertFalse(result["eligible"].any())
        self.assertEqual(
            set(result["status_path"].ravel()), {"instrument_indeterminate"}
        )
        self.assertTrue(
            result["invariants"][
                "observer_fail_closed_without_conformant_phi"
            ]
        )

    def test_causal_link_emits_only_with_conformant_phi(self) -> None:
        inputs, _ = synthetic_assessment_fixture()
        contract = CausalRegisterContract(
            source_system="contract_test_register",
            source_owner="contract_test_owner",
            register_role="internal_mismatch_phi",
            construction_id="contract_test_phi_v1",
            normalization_id="unit_interval_v1",
            construction_spec_sha256="a" * 64,
            input_roles=("internal_register_state",),
            prefix_causality_certified=True,
            operational_conformance_certificate_sha256="b" * 64,
            experimental_only=False,
        )
        result = causal_link_status(
            inputs.phi_register,
            inputs.displacement,
            np.ones(len(inputs.index), dtype=np.bool_),
            None,
            causal_register_contract=contract,
            external_cause_labels_independent=None,
        )
        self.assertTrue(result["summary"]["observer_emits"])
        self.assertTrue(result["eligible"].any())

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
