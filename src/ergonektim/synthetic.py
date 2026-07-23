"""Deterministic outcome-free fixture for product functionality verification."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .contracts import (
    ExternalDisplacementChannel,
    OperatorRepresentationContract,
    realize_external_displacement,
    validate_operator_representation,
)
from .panel import AssessmentInputs
from .telemetry import TelemetricContract
from .input_bundle import SCHEMA_VERSION, canonical_manifest, contract_dict


def synthetic_assessment_fixture() -> tuple[AssessmentInputs, TelemetricContract]:
    """Build one shared stream without reading real data or event outcomes."""

    n = 240
    row = np.arange(n, dtype=np.float64)
    index = pd.date_range("2020-01-01T00:00:00Z", periods=n, freq="h")
    omega = np.r_[
        np.zeros(24),
        np.full(80, 10.0),
        np.full(40, 1000.0),
        np.zeros(96),
    ]
    expected = np.zeros(n, dtype=np.float64)
    sigma_op = np.ones(n, dtype=np.bool_)
    u_lambda = np.zeros(n, dtype=np.float64)
    u_lambda[150:156] = 0.020
    u_lambda[190:196] = 0.015
    effective_flow = np.linspace(0.5, 1.1, n) + 0.01 * np.sin(
        2.0 * np.pi * row / 24.0
    )
    planned = np.zeros(n, dtype=np.bool_)
    planned[120:126] = True
    planned[180:186] = True

    demand_valid = np.ones(n, dtype=np.bool_)
    forecast_valid = np.ones(n, dtype=np.bool_)
    forecast_valid[30] = False
    telemetry = pd.DataFrame(
        {
            "timestamp_utc": index,
            "q": np.zeros(n, dtype=np.float64),
            "demand_valid": demand_valid,
            "forecast_valid": forecast_valid,
        }
    )

    w_demand = np.zeros(n, dtype=np.float64)
    w_interchange = np.zeros(n, dtype=np.float64)
    w_demand[120:180] = np.linspace(0.0, -0.80, 60)
    w_interchange[120:180] = np.linspace(0.0, -0.55, 60)
    w_demand[180:] = np.linspace(-0.80, 0.0, 60)
    w_interchange[180:] = np.linspace(-0.55, 0.0, 60)
    demand_reference = 1000.0 + 40.0 * np.sin(2.0 * np.pi * row / 24.0)
    demand_observed = demand_reference * (1.0 + w_demand)
    interchange_reference = 80.0 * np.sin(2.0 * np.pi * row / 24.0)
    interchange_observed = interchange_reference + 500.0 * w_interchange
    displacement_valid = {
        "demand_surprise": np.ones(n, dtype=np.bool_),
        "interchange_schedule_error": np.ones(n, dtype=np.bool_),
    }
    displacement_valid["demand_surprise"][70] = False
    displacement_valid["interchange_schedule_error"][150] = False
    channels = (
        ExternalDisplacementChannel(
            name="demand_surprise",
            observation_role="actual_demand_mw",
            reference_role="operator_demand_forecast_mw",
            normalization="reference_relative",
            normalization_id="forecast_relative_signed_v1",
            source_system="synthetic_external_market_feed",
            source_owner="synthetic_independent_BA",
            reference_floor=1.0,
        ),
        ExternalDisplacementChannel(
            name="interchange_schedule_error",
            observation_role="actual_interchange_mw",
            reference_role="operator_interchange_schedule_mw",
            normalization="fixed_scale",
            normalization_id="engineering_interchange_limit_500mw_v1",
            source_system="synthetic_external_interchange_feed",
            source_owner="synthetic_independent_RC",
            fixed_scale=500.0,
        ),
    )
    displacement = realize_external_displacement(
        index,
        channels,
        {
            "demand_surprise": demand_observed,
            "interchange_schedule_error": interchange_observed,
        },
        {
            "demand_surprise": demand_reference,
            "interchange_schedule_error": interchange_reference,
        },
        displacement_valid,
        {
            "demand_surprise": index - pd.Timedelta(hours=1),
            "interchange_schedule_error": index - pd.Timedelta(hours=1),
        },
    )

    phi = np.full(n, 0.50, dtype=np.float64)
    phi[60:120] = np.linspace(0.50, 0.90, 60)
    phi[120:180] = 0.90
    phi[180:] = np.linspace(0.90, 0.50, 60)
    labels = np.full(n, "none", dtype=object)
    labels[60:120] = "internal"
    labels[120:180] = "environmental"

    operator_r = np.zeros(n, dtype=np.float64)
    operator_r[160:200] = 15.0
    operator_r[200:] = 5.0
    operator_valid = np.ones(n, dtype=np.bool_)
    operator_valid[200] = False
    representation = validate_operator_representation(
        index,
        operator_r,
        operator_valid,
        index,
        OperatorRepresentationContract(
            source_system="synthetic_external_EMS",
            source_owner="synthetic_independent_control_room",
            channel_role="operator_estimated_structural_excess_alarm_index",
            normalization_id="kernel_excess_units_identity_v1",
            units="kernel_structural_excess_units",
            coupled_operational_parameter="synthetic_alarm_escalation_tier",
        ),
    )
    return (
        AssessmentInputs(
            index=index,
            omega=omega,
            expected=expected,
            sigma_op=sigma_op,
            u_lambda=u_lambda,
            effective_flow=effective_flow,
            planned=planned,
            telemetry=telemetry,
            telemetry_timestamp_column="timestamp_utc",
            telemetry_q_column="q",
            telemetry_valid_columns=("demand_valid", "forecast_valid"),
            displacement=displacement,
            phi_register=phi,
            external_cause_labels=labels,
            external_cause_labels_independent=True,
            operator_representation=representation,
        ),
        TelemetricContract(q_normalization_id="synthetic_zero_drain_unit_v1"),
    )


def fixture_record() -> dict[str, Any]:
    inputs, _ = synthetic_assessment_fixture()
    return {
        "kind": "deterministic_outcome_free_shared_stream",
        "rows": len(inputs.index),
        "start_utc": inputs.index[0].isoformat().replace("+00:00", "Z"),
        "stop_utc": inputs.index[-1].isoformat().replace("+00:00", "Z"),
        "real_data_accessed": False,
        "outcomes_accessed": False,
    }


def write_synthetic_bundle(path: str | Path) -> Path:
    """Write one canonical two-file bundle for CLI and packaging verification."""

    target = Path(path)
    if target.exists():
        raise FileExistsError("synthetic bundle target must not already exist")
    target.mkdir(parents=True)
    inputs, telemetric_contract = synthetic_assessment_fixture()
    from prama_protokol import KernelConfigV3

    timestamp_column = "timestamp_utc"
    frame = pd.DataFrame(
        {
            timestamp_column: inputs.index,
            "omega": inputs.omega,
            "expected": inputs.expected,
            "sigma_op": inputs.sigma_op,
            "u_lambda": inputs.u_lambda,
            "effective_flow": inputs.effective_flow,
            "planned": inputs.planned,
            "q": inputs.telemetry["q"].to_numpy(),
            "phi_register": inputs.phi_register,
            "telemetry_demand_valid": inputs.telemetry[
                "demand_valid"
            ].to_numpy(),
            "telemetry_forecast_valid": inputs.telemetry[
                "forecast_valid"
            ].to_numpy(),
        }
    )
    component_records: list[dict[str, Any]] = []
    for column, name in enumerate(inputs.displacement.component_names):
        prefix = f"w__{name}"
        observation_column = prefix + "__observation"
        reference_column = prefix + "__reference"
        valid_column = prefix + "__valid"
        issue_column = prefix + "__reference_issued_at"
        frame[observation_column] = inputs.displacement.values[:, column]
        frame[reference_column] = np.zeros(len(inputs.index), dtype=np.float64)
        frame[valid_column] = inputs.displacement.valid[:, column]
        frame[issue_column] = inputs.index - pd.Timedelta(hours=1)
        component_records.append(
            {
                "contract": contract_dict(
                    ExternalDisplacementChannel(
                        name=name,
                        observation_role="synthetic_normalized_observation",
                        reference_role="synthetic_zero_reference",
                        normalization="fixed_scale",
                        normalization_id="synthetic_identity_scale_v1",
                        source_system="synthetic_external_fixture",
                        source_owner="synthetic_independent_source",
                        fixed_scale=1.0,
                    )
                ),
                "columns": {
                    "observation": observation_column,
                    "reference": reference_column,
                    "valid": valid_column,
                    "reference_issued_at": issue_column,
                },
            }
        )

    operator_columns = {
        "value": "operator_R__value",
        "valid": "operator_R__valid",
        "issued_at": "operator_R__issued_at",
    }
    frame[operator_columns["value"]] = inputs.operator_representation.values
    frame[operator_columns["valid"]] = inputs.operator_representation.valid
    frame[operator_columns["issued_at"]] = inputs.index
    operator_metadata = dict(inputs.operator_representation.contract["metadata"])
    operator_metadata["prama_variables_used"] = tuple(
        operator_metadata["prama_variables_used"]
    )
    operator_contract = OperatorRepresentationContract(**operator_metadata)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "assessment_id": "synthetic-shared-stream-v1",
        "data_file": "timeseries.csv",
        "timestamp_column": timestamp_column,
        "core_columns": {
            "omega": "omega",
            "expected": "expected",
            "sigma_op": "sigma_op",
            "u_lambda": "u_lambda",
            "effective_flow": "effective_flow",
            "planned": "planned",
            "q": "q",
            "phi_register": "phi_register",
        },
        "telemetry": {
            "source_valid_columns": [
                "telemetry_demand_valid",
                "telemetry_forecast_valid",
            ],
            "contract": asdict(telemetric_contract),
        },
        "external_displacement": {"components": component_records},
        "operator_representation": {
            "contract": contract_dict(operator_contract),
            "columns": operator_columns,
        },
        "kernel_config": asdict(KernelConfigV3()),
    }
    (target / "manifest.json").write_bytes(canonical_manifest(manifest))
    frame.to_csv(
        target / "timeseries.csv",
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        date_format="%Y-%m-%dT%H:%M:%SZ",
        float_format="%.17g",
    )
    return target
