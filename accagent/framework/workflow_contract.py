"""Canonical public workflow for SpatialAccAgent.

Internal modules may split a public stage into small executable steps, but all
reports and routing use the consecutive Stage 0-7 contract defined here.
"""

from __future__ import annotations

from typing import Any


PUBLIC_STAGES: tuple[dict[str, Any], ...] = (
    {"id": 0, "name": "objective_and_input_preparation", "internal_steps": ("input_preparation",)},
    {"id": 1, "name": "sacg_extraction", "internal_steps": ("constraint_extraction",)},
    {"id": 2, "name": "trusted_templates_and_fpga_ip_binding", "internal_steps": ("template_selection",)},
    {"id": 3, "name": "model_derived_spatial_pipeline", "internal_steps": ("pipeline_planning",)},
    {"id": 4, "name": "dse_and_parameter_binding", "internal_steps": ("parameter_binding",)},
    {
        "id": 5,
        "name": "hardware_implementation_and_verification_preparation",
        "internal_steps": ("code_generation", "verification_artifacts"),
    },
    {"id": 6, "name": "hierarchical_real_verification_and_repair", "internal_steps": ("debug_loop",)},
    {"id": 7, "name": "vivado_implementation_and_qor", "internal_steps": ("backend_board",)},
)

INTERNAL_TO_PUBLIC = {
    internal: {"id": stage["id"], "name": stage["name"]}
    for stage in PUBLIC_STAGES
    for internal in stage["internal_steps"]
}

STAGE_TARGET_ALIASES = {
    **{f"stage{stage['id']}": stage["internal_steps"][0] for stage in PUBLIC_STAGES},
    **{f"stage{stage['id']}.{stage['name']}": stage["internal_steps"][0] for stage in PUBLIC_STAGES},
}
STAGE_TARGET_ALIASES.update(
    {
        "stage3.pipeline_planning": "pipeline_planning",
        "stage4.parameter_binding": "parameter_binding",
        "stage5.code_generation": "code_generation",
        "stage5.verification_artifacts": "verification_artifacts",
        "stage6.verification": "debug_loop",
        "stage6.debug_loop": "debug_loop",
        "stage7.backend_board": "backend_board",
        "stage7.vivado_implementation_and_qor": "backend_board",
    }
)


def public_stage(internal_step: str) -> dict[str, Any]:
    return dict(INTERNAL_TO_PUBLIC.get(internal_step, {"id": None, "name": "internal"}))


def public_workflow_manifest() -> list[dict[str, Any]]:
    return [
        {
            "id": stage["id"],
            "name": stage["name"],
            "internal_steps": list(stage["internal_steps"]),
        }
        for stage in PUBLIC_STAGES
    ]
