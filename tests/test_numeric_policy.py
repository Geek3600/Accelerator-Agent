from unittest import TestCase

from accagent.framework.numeric_policy import (
    LOOSE_NUMERIC_COMPARISON_DEFAULTS,
    numeric_comparison,
    resolve_numeric_policy,
)


class NumericPolicyTest(TestCase):
    def test_missing_quantitative_values_use_loose_defaults(self) -> None:
        policy = {
            "tolerance": {
                "stage": "functional_or_shape",
                "system": "valid_output_required",
            },
            "notes": [],
        }

        resolved = resolve_numeric_policy(policy)

        self.assertEqual(
            {name: resolved["tolerance"]["comparison"][name] for name in LOOSE_NUMERIC_COMPARISON_DEFAULTS},
            LOOSE_NUMERIC_COMPARISON_DEFAULTS,
        )
        self.assertEqual(
            resolved["_numeric_comparison_resolution"]["defaulted_fields"],
            ["atol", "rtol", "max_mismatch_fraction"],
        )
        self.assertFalse(
            resolved["_numeric_comparison_resolution"]["dut_outputs_used_for_resolution"]
        )

    def test_provided_values_take_precedence(self) -> None:
        policy = {
            "tolerance": {
                "stage": "functional",
                "system": "functional",
                "comparison": {
                    "atol": 0.01,
                    "rtol": 0.02,
                    "max_mismatch_fraction": 0.0,
                },
            }
        }

        comparison, resolution = numeric_comparison(policy)

        self.assertEqual(
            comparison,
            {"atol": 0.01, "rtol": 0.02, "max_mismatch_fraction": 0.0},
        )
        self.assertEqual(resolution["defaulted_fields"], [])
        self.assertEqual(set(resolution["field_sources"].values()), {"provided_policy"})

    def test_invalid_or_partial_values_fall_back_per_field(self) -> None:
        policy = {
            "tolerance": {
                "stage": {
                    "atol": 0.25,
                    "rtol": -1,
                    "max_mismatch_fraction": 2,
                },
                "system": "valid_output_required",
            }
        }

        comparison, resolution = numeric_comparison(policy)

        self.assertEqual(comparison["atol"], 0.25)
        self.assertEqual(comparison["rtol"], LOOSE_NUMERIC_COMPARISON_DEFAULTS["rtol"])
        self.assertEqual(
            comparison["max_mismatch_fraction"],
            LOOSE_NUMERIC_COMPARISON_DEFAULTS["max_mismatch_fraction"],
        )
        self.assertEqual(
            resolution["defaulted_fields"], ["rtol", "max_mismatch_fraction"]
        )

    def test_resolution_is_idempotent(self) -> None:
        once = resolve_numeric_policy({"tolerance": {"stage": "functional", "system": "valid"}})
        twice = resolve_numeric_policy(once)

        self.assertEqual(once, twice)
