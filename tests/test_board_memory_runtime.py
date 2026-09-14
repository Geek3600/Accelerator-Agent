from __future__ import annotations

import copy
import hashlib
from unittest import TestCase

from accagent.framework.board_acceptance_contract import canonical_contract_sha256
from accagent.framework.board_memory_runtime import (
    BOARD_MEMORY_RUNTIME_PLAN_SCHEMA,
    PLAN_AGENT_ID,
    PLAN_SCHEMA_VERSION,
    board_runtime_identity_projection,
    bind_materialized_runtime_constants,
    bind_materialized_workload,
    validate_and_normalize_plan,
)
from accagent.framework.board_runtime_image import (
    IMAGE_FORMAT as RUNTIME_IMAGE_FORMAT,
    MANIFEST_SCHEMA_VERSION as RUNTIME_MANIFEST_SCHEMA_VERSION,
)
from accagent.framework.board_weight_image import (
    IMAGE_FORMAT,
    PLAN_SCHEMA_VERSION as IMAGE_PLAN_SCHEMA_VERSION,
)


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def artifact_ref(artifact: str, path: str, value: int) -> dict:
    return {
        "resolved_value": value,
        "source": {"kind": "artifact_ref", "artifact": artifact, "path": path},
    }


def expression(value: int, text: str, *refs: tuple[str, str, str]) -> dict:
    return {
        "resolved_value": value,
        "source": {
            "kind": "derived_expression",
            "expression": text,
            "refs": [
                {"symbol": symbol, "artifact": artifact, "path": path}
                for symbol, artifact, path in refs
            ],
        },
    }


class BoardMemoryRuntimePlanTest(TestCase):
    def setUp(self) -> None:
        self.model = {
            "model_type": "synthetic_transformer",
            "num_hidden_layers": 3,
            "sequence_length": 4,
            "hidden_size": 8,
            "activation_bytes_per_element": 4,
        }
        tensors = []
        for layer_index in range(3):
            for suffix in ("arbitrary.alpha", "arbitrary.beta"):
                tensors.append(
                    {
                        "name": f"blocks.{layer_index}.{suffix}",
                        "layer_index": layer_index,
                        "parameter_suffix": suffix,
                        "source_slice_sha256": digest(f"{layer_index}:{suffix}"),
                    }
                )
        self.catalog = {
            "schema_version": "test.transformer_catalog.v1",
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "source_checkpoint_sha256": digest("checkpoint"),
            "target_layer_count": 3,
            "layer_ids": [0, 1, 2],
            "tensor_count": len(tensors),
            "tensors": tensors,
        }
        connected_payload = {
            "schema_version": "spatialaccagent.composite_weight_stream.v1",
            "status": "pass",
            "word_bits": 32,
            "word_count": 16,
            "stage_order": ["stage_with_no_model_keyword"],
            "stage_segments": [],
        }
        connected = {
            **connected_payload,
            "contract_sha256": canonical_contract_sha256(connected_payload),
        }
        runtime_payload = {
            "schema_version": "spatialaccagent.composite_runtime_stream.v1",
            "status": "pass",
            "path": "/current/run/connected_runtime.u32.memh",
            "sha256": digest("connected-runtime-bytes"),
            "word_bits": 32,
            "word_count": 4,
            "stage_order": ["stage_with_no_model_keyword"],
            "stage_segments": [
                {
                    "stage_index": 0,
                    "stage_id": "stage_with_no_model_keyword",
                    "op": "user_defined_op",
                    "runtime_contract_sha256": digest("runtime-stage-contract"),
                    "local_stream_sha256": digest("connected-runtime-bytes"),
                    "global_stream_range": {
                        "word_offset": 0,
                        "word_count": 4,
                        "word_end_exclusive": 4,
                    },
                    "targets": [],
                }
            ],
        }
        self.connected_runtime = {
            **runtime_payload,
            "contract_sha256": canonical_contract_sha256(
                {key: value for key, value in runtime_payload.items() if key != "path"}
            ),
        }
        layout_hashes = [digest("layout:no-keyword")]
        self.requirements = {
            "schema_version": "test.weight_requirements.v1",
            "accelerator_scope": "transformer_blocks_only",
            "accelerator_weight_catalog_sha256": canonical_contract_sha256(self.catalog),
            "source_checkpoint_sha256": self.catalog["source_checkpoint_sha256"],
            "board_required_layer_count": 3,
            "board_required_tensor_count": len(tensors),
            "board_required_tensors": copy.deepcopy(tensors),
            "connected_weight_stream_contract": connected,
            "connected_runtime_stream_contract": copy.deepcopy(
                self.connected_runtime
            ),
            "stage_requirements": [
                {
                    "stage_id": "stage_with_no_model_keyword",
                    "op": "user_defined_op",
                    "weight_layout_contract_sha256": layout_hashes[0],
                }
            ],
        }
        self.stage_memory_layout = {
            "schema_version": "test.stage_memory.v1",
            "regions": [
                {"label": "zone_a", "base": "0x1000", "size_bytes": 384, "alignment_bytes": 128},
                {"label": "zone_b", "base": "0x2000", "size_bytes": 128, "alignment_bytes": 128},
                {"label": "zone_c", "base": "0x2100", "size_bytes": 128, "alignment_bytes": 128},
                {"label": "zone_d", "base": "0x3000", "size_bytes": 128, "alignment_bytes": 128},
                {"label": "zone_e", "base": "0x4000", "size_bytes": 128, "alignment_bytes": 128},
                {"label": "zone_f", "base": "0x4100", "size_bytes": 128, "alignment_bytes": 128},
                {"label": "zone_g", "base": "0x5000", "size_bytes": 128, "alignment_bytes": 128},
                {"label": "zone_h", "base": "0x6000", "size_bytes": 128, "alignment_bytes": 128},
            ],
        }
        control = {
            "clock_domain": "clock_domain_17",
            "configuration_fields": [
                {
                    "field_id": "zeta_91",
                    "fact_port_id": "fact:violet_bus",
                    "register": "opaque_register_q",
                    "bit_offset": 0,
                    "width_bits": 20,
                    "access": "rw",
                    "reset_value": 0,
                },
                {
                    "field_id": "theta_04",
                    "fact_port_id": "fact:violet_bus",
                    "register": "opaque_register_q",
                    "bit_offset": 20,
                    "width_bits": 16,
                    "access": "rw",
                    "reset_value": 7,
                },
            ],
            "control_sequence_enforcement": "sample_exact_mixed",
            "control_sequence": [
                {"order": 11, "event": "cfg_evt_x", "fact_port_ids": ["fact:cfg_3"]},
                {"order": 23, "event": "launch_evt_y", "fact_port_ids": ["fact:kick_8"]},
                {"order": 41, "event": "observe_evt_z", "fact_port_ids": ["fact:watch_2"]},
                {"order": 57, "event": "clear_evt_w", "fact_port_ids": ["fact:drop_6"]},
            ],
        }
        abi = {"status": "pass", "control_abi": control}
        timing = {"clock_domains": [{"name": "clock_domain_17", "period_ps": 5000}]}
        axi = [
            {
                "name": "fabric_omega_73",
                "address_width_bits": 20,
                "data_width_bits": 64,
                "byte_order": "little",
            }
        ]
        self.identity = {
            "schema_version": "test.exact_board.v1",
            "status": "pass",
            "exact_user_sample_wrapper": True,
            "top_module": "sample_wrapper_top",
            "wrapper_top_module": "sample_wrapper_top",
            "simulation_fileset_top_module": "sample_wrapper_top",
            "selected_simulation_source_closure_sha256": digest("source-closure"),
            "compute_slot_abi": abi,
            "timing_contract": timing,
            "axi_interfaces": axi,
            "compute_slot_abi_sha256": canonical_contract_sha256(abi),
            "control_abi_sha256": canonical_contract_sha256(control),
            "timing_contract_sha256": canonical_contract_sha256(timing),
            "axi_interfaces_sha256": canonical_contract_sha256(axi),
        }
        self.certified_single_layer_binding = {
            "connected_runtime_stream_contract_sha256": self.connected_runtime[
                "contract_sha256"
            ],
            "interface": {
                "runtime_loader": {
                    "valid_port": "runtime_valid_opaque",
                    "ready_port": "runtime_ready_opaque",
                    "data_port": "runtime_data_opaque",
                    "data_width_bits": 32,
                    "addr_port": "runtime_addr_opaque",
                    "addr_width_bits": 3,
                    "last_port": "runtime_last_opaque",
                }
            },
            "loader_route_contract": {
                "runtime_routes": [
                    {
                        "stage_id": "stage_with_no_model_keyword",
                        "global_stream_range": {
                            "word_offset": 0,
                            "word_count": 4,
                            "word_end_exclusive": 4,
                        },
                    }
                ]
            },
        }
        self.runtime_manifest = self.make_runtime_manifest()
        self.runtime_authority = {
            "full_runtime_image_manifest": copy.deepcopy(self.runtime_manifest),
            "certified_single_layer_binding": copy.deepcopy(
                self.certified_single_layer_binding
            ),
        }
        self.plan = self.make_plan()

    def make_image_plan(self) -> dict:
        connected = self.requirements["connected_weight_stream_contract"]
        layout_hashes = [
            row["weight_layout_contract_sha256"]
            for row in self.requirements["stage_requirements"]
        ]
        return {
            "schema_version": IMAGE_PLAN_SCHEMA_VERSION,
            "status": "pass",
            "target_layer_count": 3,
            "input_identity": {
                "transformer_block_weight_catalog_sha256": self.requirements[
                    "accelerator_weight_catalog_sha256"
                ],
                "source_checkpoint_sha256": self.catalog["source_checkpoint_sha256"],
                "connected_weight_stream_contract_sha256": connected["contract_sha256"],
                "stage_weight_layout_contract_sha256s": layout_hashes,
                "canonical_weight_layout_set_sha256": canonical_contract_sha256(
                    {"stage_weight_layout_contract_sha256s": layout_hashes}
                ),
            },
            "image": {
                "format": IMAGE_FORMAT,
                "word_bits": 32,
                "byte_order": "little",
                "layer_order": [0, 1, 2],
                "layer_alignment_bytes": 128,
            },
            "memory": {
                "weight_bank_count": 2,
                "weight_bank_capacity_bytes": 128,
            },
            "additional_runtime_fields": {"semantic_owner": PLAN_AGENT_ID},
        }

    def make_manifest(self, image_plan: dict) -> dict:
        layer_segments = []
        hashes_by_layer = {
            layer_index: [
                row["source_slice_sha256"]
                for row in self.catalog["tensors"]
                if row["layer_index"] == layer_index
            ]
            for layer_index in range(3)
        }
        for layer_index in range(3):
            byte_offset = layer_index * 128
            layer_segments.append(
                {
                    "layer_index": layer_index,
                    "byte_offset": byte_offset,
                    "byte_count": 128,
                    "byte_end_exclusive": byte_offset + 128,
                    "word_offset": byte_offset // 4,
                    "word_count": 32,
                    "word_end_exclusive": byte_offset // 4 + 32,
                    "payload_byte_count": 64,
                    "payload_word_count": 16,
                    "padding_byte_count": 64,
                    "payload_sha256": digest(f"payload:{layer_index}"),
                    "sha256": digest(f"segment:{layer_index}"),
                    "tensor_hashes": hashes_by_layer[layer_index],
                    "stage_segments": [],
                }
            )
        layout_hashes = image_plan["input_identity"]["stage_weight_layout_contract_sha256s"]
        manifest = {
            "schema_version": "spatialaccagent.full_weight_image_manifest.v1",
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "all_target_layers": True,
            "target_layer_count": 3,
            "bound_layer_count": 3,
            "layer_order": [0, 1, 2],
            "source_checkpoint_sha256": self.catalog["source_checkpoint_sha256"],
            "accelerator_weight_catalog_sha256": self.requirements[
                "accelerator_weight_catalog_sha256"
            ],
            "dut_weight_binding_requirements_sha256": canonical_contract_sha256(
                self.requirements
            ),
            "board_workload_image_plan_sha256": canonical_contract_sha256(image_plan),
            "connected_weight_stream_contract_sha256": self.requirements[
                "connected_weight_stream_contract"
            ]["contract_sha256"],
            "stage_weight_layout_contract_sha256s": layout_hashes,
            "canonical_weight_layout_set_sha256": canonical_contract_sha256(
                {"stage_weight_layout_contract_sha256s": layout_hashes}
            ),
            "canonical_stage_layouts": [],
            "canonical_layer_word_count": 16,
            "canonical_layer_byte_count": 64,
            "word_bits": 32,
            "byte_order": "little",
            "image_format": IMAGE_FORMAT,
            "layer_alignment_bytes": 128,
            "weight_bank_count": 2,
            "weight_bank_capacity_bytes": 128,
            "path": "/current/run/weights.u32le.bin",
            "sha256": digest("image"),
            "image_sha256": digest("image"),
            "byte_count": 384,
            "total_bytes": 384,
            "word_count": 96,
            "packed_tensor_count": 6,
            "packed_tensor_hashes": [
                row["source_slice_sha256"] for row in self.catalog["tensors"]
            ],
            "source_checkpoint_files": [],
            "layer_segments": layer_segments,
            "padding_policy": {
                "placement": "zero bytes after each canonical layer payload",
                "alignment_bytes": 128,
                "padding_value": 0,
                "padding_is_not_sent_to_canonical_weight_loader": True,
            },
            "image": {
                "path": "/current/run/weights.u32le.bin",
                "sha256": digest("image"),
                "format": IMAGE_FORMAT,
                "word_bits": 32,
                "byte_order": "little",
                "byte_count": 384,
                "total_bytes": 384,
                "word_count": 96,
            },
            "manifest_path": "/current/run/full_weight_image_manifest.json",
        }
        manifest["manifest_contract_sha256"] = canonical_contract_sha256(manifest)
        return manifest

    def make_runtime_manifest(self) -> dict:
        segment_a = {
            "segment_id": "runtime-segment::A",
            "byte_offset": 0,
            "byte_count": 16,
            "byte_end_exclusive": 16,
            "word_offset": 0,
            "word_count": 4,
            "word_end_exclusive": 4,
            "sha256": digest("runtime-segment:A"),
            "layer_indices": [0, 2],
        }
        segment_b = {
            "segment_id": "runtime-segment::B",
            "byte_offset": 16,
            "byte_count": 16,
            "byte_end_exclusive": 32,
            "word_offset": 4,
            "word_count": 4,
            "word_end_exclusive": 8,
            "sha256": digest("runtime-segment:B"),
            "layer_indices": [1],
        }
        segments = {row["segment_id"]: row for row in (segment_a, segment_b)}
        layer_segment_ids = [
            "runtime-segment::A",
            "runtime-segment::B",
            "runtime-segment::A",
        ]
        layer_bindings = []
        for layer_index, segment_id in enumerate(layer_segment_ids):
            segment = segments[segment_id]
            layer_bindings.append(
                {
                    "layer_index": layer_index,
                    "segment_id": segment_id,
                    "byte_offset": segment["byte_offset"],
                    "byte_count": segment["byte_count"],
                    "word_offset": segment["word_offset"],
                    "word_count": segment["word_count"],
                    "sha256": segment["sha256"],
                    "stage_bindings": [
                        {
                            "stage_id": "stage_with_no_model_keyword",
                            "consumer_op": "user_defined_op",
                            "runtime_contract_sha256": digest(
                                "runtime-stage-contract"
                            ),
                            "word_offset": 0,
                            "word_count": 4,
                        }
                    ],
                }
            )
        manifest = {
            "schema_version": RUNTIME_MANIFEST_SCHEMA_VERSION,
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "capture_contract_sha256": digest("runtime-capture"),
            "capture_contract_identity_sha256": digest("runtime-capture-identity"),
            "source_reference_manifest_sha256": digest("runtime-reference"),
            "semantic_adapter_sha256": digest("runtime-adapter"),
            "semantic_runtime_contract_sha256": digest("semantic-runtime"),
            "semantic_runtime_contract_identity_sha256": digest(
                "semantic-runtime-identity"
            ),
            "connected_runtime_stream_contract_sha256": self.connected_runtime[
                "contract_sha256"
            ],
            "connected_runtime_stream_contract_identity_sha256": digest(
                "connected-runtime-identity"
            ),
            "target_layer_count": 3,
            "canonical_layer_word_count": 4,
            "word_bits": 32,
            "byte_order": "little",
            "image_format": RUNTIME_IMAGE_FORMAT,
            "path": "/current/run/runtime_constants.u32le.bin",
            "sha256": digest("runtime-image"),
            "image_sha256": digest("runtime-image"),
            "byte_count": 32,
            "total_bytes": 32,
            "word_count": 8,
            "unique_stream_count": 2,
            "unique_segments": [segment_a, segment_b],
            "layer_bindings": layer_bindings,
            "source_tensor_files": [],
            "deduplication_policy": {
                "kind": "exact_u32le_bytes_sha256_and_length",
                "cross_layer_sharing_is_never_assumed": True,
                "shared_segment_requires_equal_recomputed_bytes": True,
                "different_streams_remain_distinct": True,
            },
            "image": {
                "path": "/current/run/runtime_constants.u32le.bin",
                "sha256": digest("runtime-image"),
                "format": RUNTIME_IMAGE_FORMAT,
                "word_bits": 32,
                "byte_order": "little",
                "byte_count": 32,
                "word_count": 8,
            },
            "manifest_path": "/current/run/board_runtime_image_manifest.json",
        }
        manifest["manifest_contract_sha256"] = canonical_contract_sha256(manifest)
        return manifest

    def memory_region(self, region_id: str, index: int, purpose: str) -> dict:
        row = self.stage_memory_layout["regions"][index]
        return {
            "region_id": region_id,
            "purpose": purpose,
            "axi_interface_ref": "fabric_omega_73",
            "address_width_bits": 20,
            "data_width_bits": 64,
            "base_address": artifact_ref(
                "stage_memory_layout", f"/regions/{index}/base", int(row["base"], 0)
            ),
            "size_bytes": artifact_ref(
                "stage_memory_layout", f"/regions/{index}/size_bytes", row["size_bytes"]
            ),
            "alignment_bytes": artifact_ref(
                "stage_memory_layout",
                f"/regions/{index}/alignment_bytes",
                row["alignment_bytes"],
            ),
        }

    def make_plan(self) -> dict:
        image_plan = self.make_image_plan()
        manifest = self.make_manifest(image_plan)
        trace_roles = [
            "weight_prefetch_start",
            "weight_prefetch_complete",
            "weight_bank_switch",
            "activation_bank_switch",
            "final_writeback_start",
            "final_writeback_complete",
            "runtime_load_start",
            "runtime_load_complete",
        ]
        trace_ids = {role: f"trace::{index}" for index, role in enumerate(trace_roles)}
        plan = {
            "schema_version": PLAN_SCHEMA_VERSION,
            "agent": PLAN_AGENT_ID,
            "status": "ready",
            "summary": "Evidence-bound runtime plan with arbitrary physical names.",
            "blocked_reasons": [],
            "input_bindings": {
                "exact_board_identity_sha256": canonical_contract_sha256(
                    board_runtime_identity_projection(self.identity)
                ),
                "target_model_sha256": canonical_contract_sha256(self.model),
                "transformer_block_catalog_sha256": canonical_contract_sha256(self.catalog),
                "dut_weight_requirements_sha256": canonical_contract_sha256(self.requirements),
                "stage_memory_layout_sha256": canonical_contract_sha256(
                    self.stage_memory_layout
                ),
                "compute_slot_abi_sha256": self.identity["compute_slot_abi_sha256"],
                "control_abi_sha256": canonical_contract_sha256(
                    self.identity["compute_slot_abi"]["control_abi"]
                ),
                "timing_contract_sha256": self.identity["timing_contract_sha256"],
                "axi_interfaces_sha256": self.identity["axi_interfaces_sha256"],
            },
            "workload_image": {
                "image_plan": image_plan,
                "region_id": "image::x",
                "semantic_refs": {
                    "layer_alignment_bytes": artifact_ref(
                        "stage_memory_layout", "/regions/0/alignment_bytes", 128
                    ),
                    "weight_bank_capacity_bytes": expression(
                        128,
                        "((words * bits // 8 + align - 1) // align) * align",
                        (
                            "words",
                            "requirements",
                            "/connected_weight_stream_contract/word_count",
                        ),
                        (
                            "bits",
                            "requirements",
                            "/connected_weight_stream_contract/word_bits",
                        ),
                        ("align", "stage_memory_layout", "/regions/0/alignment_bytes"),
                    ),
                },
            },
            "memory_regions": [
                self.memory_region("image::x", 0, "packed_workload"),
                self.memory_region("weight::red", 1, "weight_bank"),
                self.memory_region("weight::blue", 2, "weight_bank"),
                self.memory_region("input::raw", 3, "input_activation"),
                self.memory_region("activation::left", 4, "activation_bank"),
                self.memory_region("activation::right", 5, "activation_bank"),
                self.memory_region("output::only", 6, "final_output"),
                self.memory_region("runtime::values", 7, "runtime_constants"),
            ],
            "physical_cfg_bindings": [
                {
                    "binding_id": "cfg-binding-A",
                    "runtime_role": "external image location chosen by the planner",
                    "binding_mode": "program",
                    "field_id": "zeta_91",
                    "fact_port_id": "fact:violet_bus",
                    "register": "opaque_register_q",
                    "bit_offset": 0,
                    "width_bits": 20,
                    "access": "rw",
                    "reset_value": 0,
                    "value": artifact_ref("stage_memory_layout", "/regions/0/base", 0x1000),
                },
                {
                    "binding_id": "cfg-binding-B",
                    "runtime_role": "planner-selected descriptor extent",
                    "binding_mode": "program",
                    "field_id": "theta_04",
                    "fact_port_id": "fact:violet_bus",
                    "register": "opaque_register_q",
                    "bit_offset": 20,
                    "width_bits": 16,
                    "access": "rw",
                    "reset_value": 7,
                    "value": expression(
                        192,
                        "layers * layer_bytes",
                        ("layers", "model", "/num_hidden_layers"),
                        ("layer_bytes", "workload_image", "/canonical_layer_bytes"),
                    ),
                },
            ],
            "programming_sequence": {
                "clock_domain": "clock_domain_17",
                "enforcement": "sample_exact_mixed",
                "steps": copy.deepcopy(
                    self.identity["compute_slot_abi"]["control_abi"]["control_sequence"]
                ),
            },
            "runtime_constants": {
                "enabled": True,
                "region_id": "runtime::values",
                "connected_runtime_stream_contract_sha256": self.connected_runtime[
                    "contract_sha256"
                ],
                "loader_abi": copy.deepcopy(
                    self.certified_single_layer_binding["interface"]["runtime_loader"]
                ),
                "loader_protocol": {
                    "ready_valid_acceptance": True,
                    "address_start": 0,
                    "address_increment": 1,
                    "data_word_bits": 32,
                    "last_on_final_accepted_word": True,
                    "complete_before_kernel_start": True,
                },
                "load_schedule": [
                    {
                        key: row[key]
                        for key in (
                            "layer_index",
                            "segment_id",
                            "byte_offset",
                            "byte_count",
                            "word_offset",
                            "word_count",
                            "sha256",
                        )
                    }
                    | {
                        "loader_address_start": 0,
                        "loader_address_count": row["word_count"],
                        "last_word_address": row["word_count"] - 1,
                        "complete_before_kernel_start": True,
                    }
                    for row in self.runtime_manifest["layer_bindings"]
                ],
                "trace_point_ids": [
                    trace_ids["runtime_load_start"],
                    trace_ids["runtime_load_complete"],
                ],
            },
            "weight_double_buffer": {
                "bank_count": 2,
                "initial_layer_index": 0,
                "initial_bank_id": "bank::A",
                "banks": [
                    {
                        "bank_id": "bank::A",
                        "region_id": "weight::red",
                        "capacity_bytes": artifact_ref(
                            "stage_memory_layout", "/regions/1/size_bytes", 128
                        ),
                    },
                    {
                        "bank_id": "bank::B",
                        "region_id": "weight::blue",
                        "capacity_bytes": artifact_ref(
                            "stage_memory_layout", "/regions/2/size_bytes", 128
                        ),
                    },
                ],
                "ownership_protocol": {
                    "single_compute_owner": True,
                    "inactive_bank_prefetch_only": True,
                    "prefetch_completion_before_switch": True,
                    "atomic_switch": True,
                },
                "layer_schedule": [
                    {
                        "layer_index": 0,
                        "compute_bank_id": "bank::A",
                        "prefetch_layer_index": 1,
                        "prefetch_bank_id": "bank::B",
                        "prefetch_overlaps_compute": True,
                        "switch_is_atomic": True,
                    },
                    {
                        "layer_index": 1,
                        "compute_bank_id": "bank::B",
                        "prefetch_layer_index": 2,
                        "prefetch_bank_id": "bank::A",
                        "prefetch_overlaps_compute": True,
                        "switch_is_atomic": True,
                    },
                    {
                        "layer_index": 2,
                        "compute_bank_id": "bank::A",
                        "prefetch_layer_index": None,
                        "prefetch_bank_id": None,
                        "prefetch_overlaps_compute": False,
                        "switch_is_atomic": False,
                    },
                ],
                "trace_point_ids": [
                    trace_ids["weight_prefetch_start"],
                    trace_ids["weight_prefetch_complete"],
                    trace_ids["weight_bank_switch"],
                ],
            },
            "activation_ping_pong": {
                "bank_count": 2,
                "required_activation_bytes": expression(
                    128,
                    "sequence * hidden * element_bytes",
                    ("sequence", "model", "/sequence_length"),
                    ("hidden", "model", "/hidden_size"),
                    ("element_bytes", "model", "/activation_bytes_per_element"),
                ),
                "banks": [
                    {
                        "bank_id": "activation::A",
                        "region_id": "activation::left",
                        "capacity_bytes": artifact_ref(
                            "stage_memory_layout", "/regions/4/size_bytes", 128
                        ),
                    },
                    {
                        "bank_id": "activation::B",
                        "region_id": "activation::right",
                        "capacity_bytes": artifact_ref(
                            "stage_memory_layout", "/regions/5/size_bytes", 128
                        ),
                    },
                ],
                "input_load": {
                    "source_region_id": "input::raw",
                    "destination_bank_id": "activation::A",
                    "complete_before_start": True,
                },
                "layer_schedule": [
                    {
                        "layer_index": 0,
                        "read_bank_id": "activation::A",
                        "write_bank_id": "activation::B",
                        "external_writeback": False,
                    },
                    {
                        "layer_index": 1,
                        "read_bank_id": "activation::B",
                        "write_bank_id": "activation::A",
                        "external_writeback": False,
                    },
                    {
                        "layer_index": 2,
                        "read_bank_id": "activation::A",
                        "write_bank_id": "activation::B",
                        "external_writeback": True,
                    },
                ],
                "trace_point_ids": [trace_ids["activation_bank_switch"]],
            },
            "final_writeback": {
                "enabled": True,
                "only_final_layer": True,
                "layer_index": 2,
                "source_activation_bank_id": "activation::B",
                "destination_region_id": "output::only",
                "starts_after_final_layer_completion": True,
                "trace_point_ids": [
                    trace_ids["final_writeback_start"],
                    trace_ids["final_writeback_complete"],
                ],
            },
            "trace_points": [
                {
                    "trace_id": trace_ids[role],
                    "role": role,
                    "clock_domain": "clock_domain_17",
                    "condition": f"event::{index}",
                    "observed_fields": [f"state::{index}"],
                }
                for index, role in enumerate(trace_roles)
            ],
        }
        plan = bind_materialized_workload(plan, manifest)
        return bind_materialized_runtime_constants(plan, self.runtime_manifest)

    def validate(self, plan: dict) -> tuple[dict, list[str]]:
        return validate_and_normalize_plan(
            plan,
            self.identity,
            self.model,
            self.catalog,
            self.requirements,
            self.stage_memory_layout,
            self.runtime_authority,
        )

    def test_llm_schema_keeps_real_manifest_post_materialization_optional(self) -> None:
        workload_schema = BOARD_MEMORY_RUNTIME_PLAN_SCHEMA["properties"]["workload_image"]
        runtime_schema = BOARD_MEMORY_RUNTIME_PLAN_SCHEMA["properties"][
            "runtime_constants"
        ]
        self.assertEqual(
            BOARD_MEMORY_RUNTIME_PLAN_SCHEMA["properties"]["agent"]["enum"],
            [PLAN_AGENT_ID],
        )
        self.assertNotIn("full_weight_image_manifest", workload_schema["required"])
        self.assertNotIn("full_runtime_image_manifest", runtime_schema["required"])
        unbound = copy.deepcopy(self.plan)
        del unbound["workload_image"]["full_weight_image_manifest"]
        del unbound["workload_image"]["materialized_projection"]

        _, errors = self.validate(unbound)

        self.assertIn(
            "workload_image.full_weight_image_manifest is missing after materialization",
            errors,
        )

        runtime_unbound = copy.deepcopy(self.plan)
        del runtime_unbound["runtime_constants"]["full_runtime_image_manifest"]
        del runtime_unbound["runtime_constants"]["materialized_projection"]
        normalized, runtime_errors = self.validate(runtime_unbound)

        self.assertEqual(runtime_errors, [])
        self.assertEqual(
            normalized["runtime_constants"]["full_runtime_image_manifest"],
            self.runtime_manifest,
        )

    def test_arbitrary_physical_names_pass_without_keyword_matching(self) -> None:
        normalized, errors = self.validate(self.plan)

        self.assertEqual(errors, [])
        self.assertEqual(normalized["validation"]["status"], "pass")
        self.assertEqual(
            [row["field_id"] for row in normalized["physical_cfg_bindings"]],
            ["zeta_91", "theta_04"],
        )
        self.assertEqual(
            normalized["workload_image"]["materialized_projection"][
                "canonical_layer_bytes"
            ],
            64,
        )
        self.assertEqual(
            normalized["workload_image"]["materialized_projection"]["total_bytes"],
            384,
        )
        self.assertEqual(
            [row["segment_id"] for row in normalized["runtime_constants"]["load_schedule"]],
            ["runtime-segment::A", "runtime-segment::B", "runtime-segment::A"],
        )
        self.assertEqual(
            normalized["runtime_constants"]["materialized_projection"][
                "unique_stream_count"
            ],
            2,
        )
        self.assertRegex(normalized["contract_sha256"], r"^[0-9a-f]{64}$")

    def test_prefix_scope_uses_scoped_weight_requirements(self) -> None:
        requirements = copy.deepcopy(self.requirements)
        scoped_rows = [
            row
            for row in requirements["board_required_tensors"]
            if row["layer_index"] == 0
        ]
        requirements.update(
            {
                "board_required_layer_count": 1,
                "board_required_tensor_count": len(scoped_rows),
                "board_required_tensors": scoped_rows,
                "board_validation_scope": {
                    "model_layer_count": 3,
                    "validation_layer_indices": [0],
                    "validation_layer_count": 1,
                    "reference_output_layer_index": 0,
                    "covers_full_model": False,
                    "requires_next_layer_prefetch": False,
                },
            }
        )
        plan = copy.deepcopy(self.plan)
        plan["input_bindings"]["dut_weight_requirements_sha256"] = (
            canonical_contract_sha256(requirements)
        )
        plan["workload_image"]["image_plan"]["target_layer_count"] = 1
        plan["workload_image"]["image_plan"]["image"]["layer_order"] = [0]

        _, errors = validate_and_normalize_plan(
            plan,
            self.identity,
            self.model,
            self.catalog,
            requirements,
            self.stage_memory_layout,
            self.runtime_authority,
        )

        self.assertFalse(
            any(
                error.startswith("weight requirements layer count")
                or error.startswith("weight requirements tensor count")
                or error.startswith("weight requirements do not exactly cover")
                for error in errors
            )
        )

    def test_prefix_scope_requires_plan_and_requirement_scope_agreement(self) -> None:
        requirements = copy.deepcopy(self.requirements)
        requirements["board_validation_scope"] = {
            "model_layer_count": 3,
            "validation_layer_indices": [0],
            "validation_layer_count": 1,
            "reference_output_layer_index": 0,
            "covers_full_model": False,
            "requires_next_layer_prefetch": False,
        }
        requirements["board_required_layer_count"] = 1
        requirements["board_required_tensors"] = [
            row
            for row in requirements["board_required_tensors"]
            if row["layer_index"] == 0
        ]
        requirements["board_required_tensor_count"] = len(
            requirements["board_required_tensors"]
        )
        plan = copy.deepcopy(self.plan)
        plan["input_bindings"]["dut_weight_requirements_sha256"] = (
            canonical_contract_sha256(requirements)
        )

        _, errors = validate_and_normalize_plan(
            plan,
            self.identity,
            self.model,
            self.catalog,
            requirements,
            self.stage_memory_layout,
            self.runtime_authority,
        )

        self.assertIn(
            "weight requirements board validation scope differs from the workload image plan",
            errors,
        )

    def test_runtime_manifest_and_layer_schedule_fail_closed(self) -> None:
        manifest = copy.deepcopy(self.runtime_manifest)
        manifest["layer_bindings"][1]["sha256"] = digest("wrong-layer-segment")
        manifest["manifest_contract_sha256"] = canonical_contract_sha256(
            {
                key: value
                for key, value in manifest.items()
                if key != "manifest_contract_sha256"
            }
        )
        plan = bind_materialized_runtime_constants(self.plan, manifest)
        authority = {
            "full_runtime_image_manifest": manifest,
            "certified_single_layer_binding": self.certified_single_layer_binding,
        }

        _, errors = validate_and_normalize_plan(
            plan,
            self.identity,
            self.model,
            self.catalog,
            self.requirements,
            self.stage_memory_layout,
            authority,
        )

        self.assertTrue(any("differs from its runtime segment" in error for error in errors))
        self.assertTrue(any("differs from the runtime manifest" in error for error in errors))

        incomplete = copy.deepcopy(self.runtime_manifest)
        incomplete["layer_bindings"].pop()
        incomplete["unique_segments"][0]["layer_indices"] = [0]
        incomplete["manifest_contract_sha256"] = canonical_contract_sha256(
            {
                key: value
                for key, value in incomplete.items()
                if key != "manifest_contract_sha256"
            }
        )
        incomplete_plan = bind_materialized_runtime_constants(self.plan, incomplete)
        incomplete_authority = {
            "full_runtime_image_manifest": incomplete,
            "certified_single_layer_binding": self.certified_single_layer_binding,
        }
        _, incomplete_errors = validate_and_normalize_plan(
            incomplete_plan,
            self.identity,
            self.model,
            self.catalog,
            self.requirements,
            self.stage_memory_layout,
            incomplete_authority,
        )
        self.assertTrue(
            any("does not bind every target layer" in error for error in incomplete_errors)
        )

    def test_runtime_region_capacity_and_non_overlap_are_enforced(self) -> None:
        overlapping = copy.deepcopy(self.plan)
        overlapping["memory_regions"][-1]["base_address"] = artifact_ref(
            "stage_memory_layout", "/regions/6/base", 0x5000
        )
        _, overlap_errors = self.validate(overlapping)
        self.assertTrue(any("overlap" in error for error in overlap_errors))

        layout = copy.deepcopy(self.stage_memory_layout)
        layout["regions"][7]["size_bytes"] = 16
        layout["regions"][7]["alignment_bytes"] = 8
        too_small = copy.deepcopy(self.plan)
        too_small["input_bindings"]["stage_memory_layout_sha256"] = (
            canonical_contract_sha256(layout)
        )
        too_small["memory_regions"][-1]["size_bytes"] = artifact_ref(
            "stage_memory_layout", "/regions/7/size_bytes", 16
        )
        too_small["memory_regions"][-1]["alignment_bytes"] = artifact_ref(
            "stage_memory_layout", "/regions/7/alignment_bytes", 8
        )
        _, capacity_errors = validate_and_normalize_plan(
            too_small,
            self.identity,
            self.model,
            self.catalog,
            self.requirements,
            layout,
            self.runtime_authority,
        )
        self.assertIn(
            "runtime constants image does not fit its physical memory region",
            capacity_errors,
        )

    def test_runtime_loader_abi_schedule_and_trace_completion_are_enforced(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["runtime_constants"]["loader_abi"]["addr_port"] = "guessed_addr"
        plan["runtime_constants"]["load_schedule"][1][
            "complete_before_kernel_start"
        ] = False
        runtime_complete_id = plan["runtime_constants"]["trace_point_ids"].pop()
        plan["trace_points"] = [
            row for row in plan["trace_points"] if row["trace_id"] != runtime_complete_id
        ]

        _, errors = self.validate(plan)

        self.assertTrue(any("loader_abi differs" in error for error in errors))
        self.assertTrue(any("before kernel start" in error for error in errors))
        self.assertTrue(any("every required runtime role" in error for error in errors))
        self.assertTrue(any("both runtime load trace roles" in error for error in errors))

    def test_runtime_loader_routes_must_match_connected_contract(self) -> None:
        authority = copy.deepcopy(self.runtime_authority)
        authority["certified_single_layer_binding"]["loader_route_contract"][
            "runtime_routes"
        ][0]["global_stream_range"]["word_count"] = 3

        _, errors = validate_and_normalize_plan(
            self.plan,
            self.identity,
            self.model,
            self.catalog,
            self.requirements,
            self.stage_memory_layout,
            authority,
        )

        self.assertTrue(any("loader routes do not exactly cover" in error for error in errors))

    def test_no_runtime_stream_accepts_explicit_disabled_with_legacy_call(self) -> None:
        requirements = copy.deepcopy(self.requirements)
        requirements.pop("connected_runtime_stream_contract")
        plan = copy.deepcopy(self.plan)
        plan["input_bindings"]["dut_weight_requirements_sha256"] = (
            canonical_contract_sha256(requirements)
        )
        weight_manifest = copy.deepcopy(
            plan["workload_image"]["full_weight_image_manifest"]
        )
        weight_manifest["dut_weight_binding_requirements_sha256"] = (
            canonical_contract_sha256(requirements)
        )
        weight_manifest["manifest_contract_sha256"] = canonical_contract_sha256(
            {
                key: value
                for key, value in weight_manifest.items()
                if key != "manifest_contract_sha256"
            }
        )
        plan = bind_materialized_workload(plan, weight_manifest)
        plan["runtime_constants"] = {
            "enabled": False,
            "region_id": None,
            "connected_runtime_stream_contract_sha256": None,
            "loader_abi": None,
            "loader_protocol": None,
            "load_schedule": [],
            "trace_point_ids": [],
        }
        plan["memory_regions"] = [
            row
            for row in plan["memory_regions"]
            if row["region_id"] != "runtime::values"
        ]
        plan["trace_points"] = [
            row
            for row in plan["trace_points"]
            if row["role"] not in {"runtime_load_start", "runtime_load_complete"}
        ]

        normalized, errors = validate_and_normalize_plan(
            plan,
            self.identity,
            self.model,
            self.catalog,
            requirements,
            self.stage_memory_layout,
        )

        self.assertEqual(errors, [])
        self.assertFalse(normalized["runtime_constants"]["enabled"])

    def test_runtime_identity_ignores_audit_packaging_but_tracks_board_semantics(self) -> None:
        expected = canonical_contract_sha256(
            board_runtime_identity_projection(self.identity)
        )
        repackaged = copy.deepcopy(self.identity)
        repackaged["discovery_provenance"] = {
            "prompt_path": "/another/run/prompt.md",
            "record_sha256": digest("new-record"),
        }
        repackaged["evidence_records"] = [{"sha256": digest("new-package")}]

        self.assertEqual(
            canonical_contract_sha256(board_runtime_identity_projection(repackaged)),
            expected,
        )
        _, repackaged_errors = validate_and_normalize_plan(
            self.plan,
            repackaged,
            self.model,
            self.catalog,
            self.requirements,
            self.stage_memory_layout,
            self.runtime_authority,
        )
        self.assertEqual(repackaged_errors, [])

        changed_timing = copy.deepcopy(self.identity)
        changed_timing["timing_contract"]["clock_domains"][0]["period_ps"] = 6000
        changed_timing["timing_contract_sha256"] = canonical_contract_sha256(
            changed_timing["timing_contract"]
        )
        self.assertNotEqual(
            canonical_contract_sha256(
                board_runtime_identity_projection(changed_timing)
            ),
            expected,
        )
        _, changed_errors = validate_and_normalize_plan(
            self.plan,
            changed_timing,
            self.model,
            self.catalog,
            self.requirements,
            self.stage_memory_layout,
            self.runtime_authority,
        )
        self.assertTrue(
            any(
                "input_bindings.exact_board_identity_sha256" in error
                for error in changed_errors
            )
        )

    def test_familiar_field_name_cannot_bypass_exact_fact_identity(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["physical_cfg_bindings"][0]["field_id"] = "param_addr"

        _, errors = self.validate(plan)

        self.assertTrue(
            any("does not reference an exact discovered physical cfg field" in error for error in errors)
        )
        self.assertTrue(any("do not exactly cover" in error for error in errors))

    def test_opaque_or_incorrect_numeric_value_fails_closed(self) -> None:
        opaque = copy.deepcopy(self.plan)
        opaque["memory_regions"][0]["base_address"] = 0x1000
        _, opaque_errors = self.validate(opaque)
        self.assertTrue(any("evidence-bound integer" in error for error in opaque_errors))

        wrong_derivation = copy.deepcopy(self.plan)
        wrong_derivation["workload_image"]["semantic_refs"][
            "weight_bank_capacity_bytes"
        ]["resolved_value"] = 256
        _, derivation_errors = self.validate(wrong_derivation)
        self.assertTrue(any("does not match derived value" in error for error in derivation_errors))

        self_referential = copy.deepcopy(self.plan)
        self_referential["workload_image"]["semantic_refs"]["layer_alignment_bytes"] = (
            artifact_ref(
                "workload_image", "/image_plan/image/layer_alignment_bytes", 128
            )
        )
        _, self_reference_errors = self.validate(self_referential)
        self.assertTrue(
            any("is not authoritative for this value" in error for error in self_reference_errors)
        )

    def test_buffering_ping_pong_and_final_writeback_are_mandatory(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["weight_double_buffer"]["layer_schedule"][0][
            "prefetch_overlaps_compute"
        ] = False
        plan["activation_ping_pong"]["layer_schedule"][1]["read_bank_id"] = (
            "activation::A"
        )
        plan["activation_ping_pong"]["layer_schedule"][0]["external_writeback"] = True
        plan["final_writeback"]["layer_index"] = 1

        _, errors = self.validate(plan)

        self.assertTrue(any("does not overlap next-layer prefetch" in error for error in errors))
        self.assertTrue(any("does not alternate activation ping-pong" in error for error in errors))
        self.assertTrue(any("final-layer-only external writeback" in error for error in errors))
        self.assertTrue(any("not the final target layer" in error for error in errors))

    def test_manifest_padding_and_tensor_coverage_are_checked_separately(self) -> None:
        plan = copy.deepcopy(self.plan)
        manifest = plan["workload_image"]["full_weight_image_manifest"]
        manifest["layer_segments"][1]["payload_byte_count"] = 128
        manifest["layer_segments"][2]["tensor_hashes"] = manifest["layer_segments"][1][
            "tensor_hashes"
        ]
        manifest["manifest_contract_sha256"] = canonical_contract_sha256(
            {key: value for key, value in manifest.items() if key != "manifest_contract_sha256"}
        )
        plan = bind_materialized_workload(plan, manifest)

        _, errors = self.validate(plan)

        self.assertTrue(any("payload differs from the certified stream" in error for error in errors))
        self.assertTrue(any("tensor hashes are incomplete" in error for error in errors))
