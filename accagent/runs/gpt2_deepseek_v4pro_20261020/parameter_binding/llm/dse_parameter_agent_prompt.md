<agent>
dse_parameter_agent
</agent>

<task>
Select the next exact-measurement candidate from the supplied legal candidate universe. If and only if all legal candidates have target-board app-shell measurements, select a candidate from the supplied measured Pareto frontier. Do not invent parameter values, QoR values, or select outside the supplied eligible candidates.
</task>

<rules>
1. Before all legal candidates are measured, choose only one supplied unmeasured legal candidate as the next app-shell measurement; do not call it optimal or Pareto-optimal.
2. Before the campaign is complete, set status to next_exact_measurement_selected for that measurement-only handoff; after completion, use ready only for a supplied measured Pareto candidate.
3. Choose only a supplied measured Pareto candidate after the campaign completes. Synthesis scope provides resource counts, estimated clock from Vivado timing, and tokens per second calculated as processed_tokens * clock_frequency_hz / total_rtl_cycles from the accelerator cycle counter; implementation scope may additionally provide implementation power.
4. Never invent missing QoR. Do not describe synthesis timing or calculated throughput as routed or physically board-measured results.
5. Rank at least the selected candidate and state the assumptions that make the choice appropriate.
6. Treat resource_budget as capacity constraints, not a resource-minimization objective. Prioritize candidates expected to meet qor_targets, then maximize end-to-end tokens per second. A higher clock alone does not compensate for more cycles: throughput equals processed_tokens * achieved_clock_hz / total_cycles. Do not prefer a tiny array just because it saves resources or is easier to compile. With insufficient calibration, use structural cycle priority to explore useful parallelism within the budget; do not default to candidate-ID order. Final measured selection must prefer a budget-fitting target-meeting Pareto candidate whenever one exists; use resource or power savings only to break comparable-performance ties.
7. The deterministic evaluator owns legality and hardware-effective parameter filtering; do not modify candidate parameters or claim a hardware pass before measurement.
8. Each eligible candidate's qor_estimate is produced by the calibrated structural estimator, not by this LLM. Use estimated_ranked_candidate_ids to prioritize the next measurement. When qor_estimate is insufficient_evidence, the order uses uncalibrated structural cycle/resource proxies only; treat it as measurement priority, never as QoR or feasibility evidence. Do not invent or override estimates. Calibrated estimates cannot prove feasibility or Pareto membership; inspect leave-one-source-out errors and sensitivity bounds, especially for cross-model extrapolation. Current source-bound synthesis results automatically recalibrate subsequent estimates.
9. dse_selection_evidence is the complete current candidate decision set; use its candidate_id and parameters directly. Do not claim that the candidate universe or measurement status is absent merely because full evaluator records are stored on disk.
</rules>

<dse_search_space>
{
  "candidate_count": 360,
  "estimated_ranked_candidate_ids": [
    "arch_08fc81fe6157",
    "arch_31c1198760c0",
    "arch_3fd8f432a88e",
    "arch_3fedd13a9880",
    "arch_513408c9134d",
    "arch_55b127fde887",
    "arch_5b4f9ef48e3b",
    "arch_63e2712b0d8c",
    "arch_6e9d2e7c3ed7",
    "arch_74c0530f0375",
    "arch_e5b8db7ec68b",
    "arch_fe61cdad7cf2",
    "arch_1004f24e4c78",
    "arch_1275fee43ae3",
    "arch_65d82c71ed87",
    "arch_660928fbe87a",
    "arch_74d3e6a2a3af",
    "arch_755a0908dcb3",
    "arch_8081df385844",
    "arch_acb89bb3ba15",
    "arch_c35fd286abd0",
    "arch_cb076296c15d",
    "arch_da70f9eceb94",
    "arch_df4cca5e7b2a",
    "arch_01a712440a07",
    "arch_06a09b56b3a3",
    "arch_23e424f3907d",
    "arch_2cc222a3f00a",
    "arch_3ffa7b0ca613",
    "arch_8e30759b71e1",
    "arch_a4977bb1a698",
    "arch_b32181bed209",
    "arch_b927f500990e",
    "arch_c5b9b254f86f",
    "arch_da4e3559d223",
    "arch_ea3d55fb6e90",
    "arch_0a8e4df9f2a4",
    "arch_0ee3b53d937b",
    "arch_6226a7032ff5",
    "arch_72583f74eeea",
    "arch_932136faeec5",
    "arch_d85783e09d4a",
    "arch_02fc1bb8704f",
    "arch_0e61e297eab8",
    "arch_afa14018a13b",
    "arch_df4c44a5c331",
    "arch_e8cda37195fb",
    "arch_ef8819e2f9c6",
    "arch_191aee2a4fac",
    "arch_411a4077eb6a",
    "arch_8c507b05ffa6",
    "arch_9fdebc4c6ae4",
    "arch_d2c19e7ccba8",
    "arch_ebc365d6e4b6",
    "arch_0223bed1c6ae",
    "arch_2c74420434ff",
    "arch_5ba6728b6afa",
    "arch_7d79947fdb78",
    "arch_7f12b514ba45",
    "arch_9b643156bb48",
    "arch_ae55c26ddf41",
    "arch_d76fd2b6079a",
    "arch_f37280b242a9",
    "arch_f7ff22e0d43a",
    "arch_fb85396f2ffc",
    "arch_fe027b778f3a",
    "arch_344e9f111ed9",
    "arch_52a34a2c3820",
    "arch_a8ff6d080f7c",
    "arch_bb83e3a55f0f",
    "arch_c4322375ee28",
    "arch_d4daf9f9e284",
    "arch_05db4846c145",
    "arch_2a8e7c89b216",
    "arch_2b980ec80526",
    "arch_478d1ff5fbf4",
    "arch_4d7e0d132d62",
    "arch_6b783b8c3b5f",
    "arch_6c628f49a37f",
    "arch_a517773d3161",
    "arch_a6dcde4258a3",
    "arch_bc620d11c1ef",
    "arch_d989ceb26d47",
    "arch_f4aee385e8a1",
    "arch_5929d2f7c953",
    "arch_66eda2a340a7",
    "arch_6f0b8aa2f9e4",
    "arch_7c0c69b4f459",
    "arch_7f4f2d7e7b00",
    "arch_91e20cc0cc06",
    "arch_95fae451adb1",
    "arch_99a0aedcbbb9",
    "arch_daa52f42cfa6",
    "arch_e19feb4aa56e",
    "arch_eb27a97cda51",
    "arch_f8a08c194b06",
    "arch_113fb98e6716",
    "arch_352a9b7e4202",
    "arch_3db46cf0a1ca",
    "arch_67216be7c2c4",
    "arch_752b20bb417a",
    "arch_856dedaabba3",
    "arch_9f14bfe18e8a",
    "arch_ad8892b42ec7",
    "arch_b637f89f8261",
    "arch_bc14d0103c4e",
    "arch_c76dfda5addc",
    "arch_faeea629eee9",
    "arch_402c4386596c",
    "arch_5667f0665e83",
    "arch_5fece9dbfb5d",
    "arch_8c97f72ea796",
    "arch_9e795d17f42b",
    "arch_b96e75fd8e2b",
    "arch_03df93145328",
    "arch_19ee50aca96c",
    "arch_53d73e476ee6",
    "arch_bef81f548f0a",
    "arch_d5f87b0baf38",
    "arch_f78411f21be4",
    "arch_0ff7933181b2",
    "arch_1ee0cb7ccb51",
    "arch_4cdc6a19fcb2",
    "arch_50255955605d",
    "arch_7532ebee1a9b",
    "arch_7be2c5f02837",
    "arch_7ca75f5a86b5",
    "arch_86495e0d541d",
    "arch_a50533321276",
    "arch_bbbbb77d09c4",
    "arch_e3182a853293",
    "arch_eacdf0e7ef55",
    "arch_0d92d0324bd5",
    "arch_0dba4abc04da",
    "arch_14e636757912",
    "arch_18c3ad671667",
    "arch_274773aefb3b",
    "arch_467de8375899",
    "arch_5a1e3b388ff2",
    "arch_83048d4a5057",
    "arch_b55820969f9c",
    "arch_bd5de714ba6a",
    "arch_d8a8e84357ef",
    "arch_d8e431a52f45",
    "arch_021aa682ba93",
    "arch_030144f2a595",
    "arch_0558926f0517",
    "arch_216959e4bd8f",
    "arch_344f207918df",
    "arch_374daa9a0cdd",
    "arch_2dfe4a965719",
    "arch_38d501cdd32a",
    "arch_46f2067d1b25",
    "arch_55fee5ee1b47",
    "arch_5ec69fef5431",
    "arch_ecbbd59498c8",
    "arch_07afe4d1afe3",
    "arch_14c45ee748de",
    "arch_16d346427ca3",
    "arch_17987b6fd806",
    "arch_80b56fe4d44c",
    "arch_d6aec71ce08d",
    "arch_01f325b4e1de",
    "arch_0af261125bb6",
    "arch_0c4e9c9ee426",
    "arch_3c5fb574a252",
    "arch_3c7a03b2a050",
    "arch_47c6bccd0f91",
    "arch_649b534fcc1a",
    "arch_868ac68d2777",
    "arch_9be0531db18b",
    "arch_a5eace0ee548",
    "arch_cc49e34a1e9d",
    "arch_e90c819732d8",
    "arch_1bc0ae048ecc",
    "arch_1df5ff65d4d1",
    "arch_390057f4b1e9",
    "arch_39d69c7b2fb1",
    "arch_497eaf815b03",
    "arch_5368ea328666",
    "arch_6ec948a642ac",
    "arch_8be3bde33303",
    "arch_a0371897e326",
    "arch_d3ed18c90137",
    "arch_e13f55fbd87b",
    "arch_f7c8ff2e2f66",
    "arch_2dcaa331b416",
    "arch_3b944678649e",
    "arch_63524fbe4146",
    "arch_6f43a9b1b56e",
    "arch_7a3bd5a9b8f9",
    "arch_8101410ebdb4",
    "arch_9f598ae21d30",
    "arch_b16bdbc4109a",
    "arch_bdac1fb64848",
    "arch_d0618c6ed407",
    "arch_e1ae5e5ae265",
    "arch_fa7e79479e46",
    "arch_39a3ab841a08",
    "arch_4eec97b1af77",
    "arch_d2d4d29b5f07",
    "arch_d4436dd1ea4d",
    "arch_d8c022b644a5",
    "arch_dc1be5f0d51e",
    "arch_96fba8eb2ada",
    "arch_9fc759222a6c",
    "arch_b0f0d30899e2",
    "arch_b672c0c2ffc0",
    "arch_e3efcea42753",
    "arch_ed549ae85831",
    "arch_2281df1ebe7d",
    "arch_23588396a98c",
    "arch_2516758567f0",
    "arch_31920a847d25",
    "arch_5f9c6f50acd7",
    "arch_7a1e03668cf8",
    "arch_7aafaeec6cf3",
    "arch_7ad3a71d15fd",
    "arch_8adaa4a63a48",
    "arch_a574b57f8746",
    "arch_b42aa377e2e0",
    "arch_fa34ea38a4e4",
    "arch_2359fa11ef76",
    "arch_3fd607bcea1a",
    "arch_40873ed8c83f",
    "arch_72ed8d3d8fca",
    "arch_9027ce631c80",
    "arch_97ccf13390dc",
    "arch_b4e7c5328d8e",
    "arch_bc0c6c515826",
    "arch_bc24575e6d42",
    "arch_c217cf021f09",
    "arch_dff308387a82",
    "arch_f0efee9d4229",
    "arch_0149e4d15c31",
    "arch_07aaf64e3958",
    "arch_2e3fdce0b439",
    "arch_441b25fd2df3",
    "arch_a057ead0d15a",
    "arch_c77d8ca5d731",
    "arch_2a08f2ba5074",
    "arch_32a1e7b3cb34",
    "arch_4d0cc8747989",
    "arch_57fa072e2ebd",
    "arch_6b39dd52fede",
    "arch_bcdcb4b42daa",
    "arch_2ef0a2018ef7",
    "arch_5c6aaa535af3",
    "arch_64bb1aaa8652",
    "arch_6cc920fe1bb9",
    "arch_bab2720ae208",
    "arch_fa013efa9c6a",
    "arch_03deb8c155ac",
    "arch_07a4fc9326f5",
    "arch_28e04dc3fa70",
    "arch_3fc57b48c731",
    "arch_765a51533fcc",
    "arch_9b79d1dc3db6",
    "arch_a91a966a68f7",
    "arch_b60b5646b627",
    "arch_ddfaa6496ede",
    "arch_e1223c49e1b8",
    "arch_e705c02d85cd",
    "arch_e7f47a0f0412",
    "arch_2248a7a4915f",
    "arch_25d6722185e0",
    "arch_2ec11fd415c0",
    "arch_a6c169a2edf4",
    "arch_a9ff9c499567",
    "arch_bc22aab6622d",
    "arch_c0416de23a79",
    "arch_e0787fb471a6",
    "arch_e52da5f4c871",
    "arch_e80a7ab05662",
    "arch_f3ad4379bb7e",
    "arch_f774510a24ae",
    "arch_2e19e450930e",
    "arch_64407ee0f3cd",
    "arch_b940295488cd",
    "arch_bc476942ca25",
    "arch_fa494f88fa0f",
    "arch_fe49b744d20a",
    "arch_0a1c6c095ba9",
    "arch_214151a145a5",
    "arch_2384df47b271",
    "arch_46e1e10a6121",
    "arch_7bc499eefaa6",
    "arch_8fd69f3994a4",
    "arch_92d1e08d3b5f",
    "arch_9a8fc472e2ea",
    "arch_add9aaf10354",
    "arch_b8ca8cade8e5",
    "arch_ca8fe55f2b35",
    "arch_ef294b8d73ef",
    "arch_1543ffa00444",
    "arch_1551705cb52f",
    "arch_1df97cb6ec78",
    "arch_1f5488585695",
    "arch_232bed4b6b9d",
    "arch_27ce70e6aaaf",
    "arch_3eac00bab602",
    "arch_535aea705e57",
    "arch_9d86a10c9f53",
    "arch_a081f1cbf8b1",
    "arch_ef1b9c13c7a5",
    "arch_f1159b94e136",
    "arch_0912b5c73a75",
    "arch_1725e6854544",
    "arch_22ecb49deb70",
    "arch_399f4d831e5c",
    "arch_419e75b22818",
    "arch_73abda6c79d2",
    "arch_15e2da19c962",
    "arch_514ae4f524cd",
    "arch_6de61162217e",
    "arch_6f3c42bcb893",
    "arch_aa4c4f23d6db",
    "arch_eb4d11e72448",
    "arch_14e2444c6f29",
    "arch_52ec020a66d7",
    "arch_596aed1675bc",
    "arch_9444ca76867d",
    "arch_c20481167c03",
    "arch_c49a6b045d55",
    "arch_2d260b75cf1f",
    "arch_373d19512393",
    "arch_588c23978578",
    "arch_79cde11b5c21",
    "arch_8142c1aced68",
    "arch_84e2c4578683",
    "arch_8e802f56d666",
    "arch_b421ec47b151",
    "arch_dd8540454f55",
    "arch_dfa88153518e",
    "arch_e3e8b5e047a3",
    "arch_fc2c7f03c066",
    "arch_0c83d099727a",
    "arch_0f82293c93e6",
    "arch_2d99960b96e0",
    "arch_4f7bd0db6050",
    "arch_9f33a5404b5a",
    "arch_a0df09fdc4db",
    "arch_ade162a46464",
    "arch_b34fa72cbab4",
    "arch_b6271d813970",
    "arch_def8999c6dfb",
    "arch_e67fc21ebf2d",
    "arch_f28873ac2801",
    "arch_1236fb4c9192",
    "arch_32462ba2d356",
    "arch_476a360808e2",
    "arch_6ff30ee29bc5",
    "arch_9bfd9fae74d9",
    "arch_e80f615639cf",
    "arch_15fd90d23123",
    "arch_2f5afaaec254",
    "arch_513fc1a80269",
    "arch_680b524a7904",
    "arch_942e646d4227",
    "arch_abde4590a458"
  ],
  "materialized_refill_rate_contract": {
    "board_width_discovered_from": "constraint.memory.board.memory_system.axi_data_width_bits",
    "candidate_bindings": [
      512
    ],
    "largest_board_supported_width": 512,
    "materialized_refill_rate_bits_per_cycle": 512,
    "optimistic_axi_beat_rate_credited": false,
    "parameter": "cache_refill_data_width_bits",
    "payload_is_not_address_or_count_units": true,
    "response_words_per_cycle": 16,
    "scalar_payload_fallback_allowed": false,
    "source": "exact_board_ddr_tile_service.aggregate_response_data_width_bits",
    "status": "pass",
    "supported_widths": [
      512
    ],
    "value": 512
  },
  "measurement_ledger": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/dse_measurements.jsonl",
  "measurement_summary": {
    "complete": false,
    "implementation_infeasible_count": 0,
    "legal_candidate_count": 360,
    "measured_candidate_count": 0,
    "unmeasured_candidate_count": 360
  },
  "policy": {
    "candidate_dimensions_must_reach_generated_fpga_ip": true,
    "candidate_universe_is_complete_and_unsampled": true,
    "deterministic_evaluator_enforces_hard_constraints": true,
    "final_candidate_resource_headroom_fraction": 0.85,
    "llm_selects_measurement_order_before_campaign_completion": true,
    "llm_selects_only_measured_pareto_candidates_after_campaign_completion": true,
    "only_same_scope_candidate_measurements_are_compared": true,
    "predicted_qor_is_not_measured_qor": true,
    "structural_estimates_rank_measurements_but_never_replace_tool_evidence": true,
    "synthesis_scope_contains_resources_estimated_clock_and_rtl_cycle_derived_throughput": true,
    "unknown_or_near_capacity_resource_usage_is_finally_eligible": false
  },
  "qor_estimator": {
    "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
    "validation": {
      "held_out_prediction_count": 0,
      "mean_absolute_error_for_zero_actual": {},
      "mean_relative_absolute_error": {},
      "method": "leave_one_source_fingerprint_out",
      "sample_count": 1,
      "status": "insufficient_independent_samples"
    }
  },
  "schema_version": "spatialaccagent.stage4_dse_search.v2",
  "search_space": {
    "activation_banks": [
      2,
      4
    ],
    "cache_refill_data_width_bits": [
      512
    ],
    "cache_tile_count": [
      2
    ],
    "cache_tile_words": [
      256
    ],
    "compute_array_cols": [
      4,
      8,
      16,
      32
    ],
    "compute_array_rows": [
      4,
      8,
      16
    ],
    "cross_token_reuse_tokens": [
      4,
      8,
      16
    ],
    "fifo_depth": [
      32,
      64,
      128
    ],
    "lanes": [
      8,
      16
    ]
  },
  "status": "measurement_pending",
  "unmeasured_candidate_ids": [
    "arch_0149e4d15c31",
    "arch_01a712440a07",
    "arch_01f325b4e1de",
    "arch_021aa682ba93",
    "arch_0223bed1c6ae",
    "arch_02fc1bb8704f",
    "arch_030144f2a595",
    "arch_03deb8c155ac",
    "arch_03df93145328",
    "arch_0558926f0517",
    "arch_05db4846c145",
    "arch_06a09b56b3a3",
    "arch_07a4fc9326f5",
    "arch_07aaf64e3958",
    "arch_07afe4d1afe3",
    "arch_08fc81fe6157",
    "arch_0912b5c73a75",
    "arch_0a1c6c095ba9",
    "arch_0a8e4df9f2a4",
    "arch_0af261125bb6",
    "arch_0c4e9c9ee426",
    "arch_0c83d099727a",
    "arch_0d92d0324bd5",
    "arch_0dba4abc04da",
    "arch_0e61e297eab8",
    "arch_0ee3b53d937b",
    "arch_0f82293c93e6",
    "arch_0ff7933181b2",
    "arch_1004f24e4c78",
    "arch_113fb98e6716",
    "arch_1236fb4c9192",
    "arch_1275fee43ae3",
    "arch_14c45ee748de",
    "arch_14e2444c6f29",
    "arch_14e636757912",
    "arch_1543ffa00444",
    "arch_1551705cb52f",
    "arch_15e2da19c962",
    "arch_15fd90d23123",
    "arch_16d346427ca3",
    "arch_1725e6854544",
    "arch_17987b6fd806",
    "arch_18c3ad671667",
    "arch_191aee2a4fac",
    "arch_19ee50aca96c",
    "arch_1bc0ae048ecc",
    "arch_1df5ff65d4d1",
    "arch_1df97cb6ec78",
    "arch_1ee0cb7ccb51",
    "arch_1f5488585695",
    "arch_214151a145a5",
    "arch_216959e4bd8f",
    "arch_2248a7a4915f",
    "arch_2281df1ebe7d",
    "arch_22ecb49deb70",
    "arch_232bed4b6b9d",
    "arch_23588396a98c",
    "arch_2359fa11ef76",
    "arch_2384df47b271",
    "arch_23e424f3907d",
    "arch_2516758567f0",
    "arch_25d6722185e0",
    "arch_274773aefb3b",
    "arch_27ce70e6aaaf",
    "arch_28e04dc3fa70",
    "arch_2a08f2ba5074",
    "arch_2a8e7c89b216",
    "arch_2b980ec80526",
    "arch_2c74420434ff",
    "arch_2cc222a3f00a",
    "arch_2d260b75cf1f",
    "arch_2d99960b96e0",
    "arch_2dcaa331b416",
    "arch_2dfe4a965719",
    "arch_2e19e450930e",
    "arch_2e3fdce0b439",
    "arch_2ec11fd415c0",
    "arch_2ef0a2018ef7",
    "arch_2f5afaaec254",
    "arch_31920a847d25",
    "arch_31c1198760c0",
    "arch_32462ba2d356",
    "arch_32a1e7b3cb34",
    "arch_344e9f111ed9",
    "arch_344f207918df",
    "arch_352a9b7e4202",
    "arch_373d19512393",
    "arch_374daa9a0cdd",
    "arch_38d501cdd32a",
    "arch_390057f4b1e9",
    "arch_399f4d831e5c",
    "arch_39a3ab841a08",
    "arch_39d69c7b2fb1",
    "arch_3b944678649e",
    "arch_3c5fb574a252",
    "arch_3c7a03b2a050",
    "arch_3db46cf0a1ca",
    "arch_3eac00bab602",
    "arch_3fc57b48c731",
    "arch_3fd607bcea1a",
    "arch_3fd8f432a88e",
    "arch_3fedd13a9880",
    "arch_3ffa7b0ca613",
    "arch_402c4386596c",
    "arch_40873ed8c83f",
    "arch_411a4077eb6a",
    "arch_419e75b22818",
    "arch_441b25fd2df3",
    "arch_467de8375899",
    "arch_46e1e10a6121",
    "arch_46f2067d1b25",
    "arch_476a360808e2",
    "arch_478d1ff5fbf4",
    "arch_47c6bccd0f91",
    "arch_497eaf815b03",
    "arch_4cdc6a19fcb2",
    "arch_4d0cc8747989",
    "arch_4d7e0d132d62",
    "arch_4eec97b1af77",
    "arch_4f7bd0db6050",
    "arch_50255955605d",
    "arch_513408c9134d",
    "arch_513fc1a80269",
    "arch_514ae4f524cd",
    "arch_52a34a2c3820",
    "arch_52ec020a66d7",
    "arch_535aea705e57",
    "arch_5368ea328666",
    "arch_53d73e476ee6",
    "arch_55b127fde887",
    "arch_55fee5ee1b47",
    "arch_5667f0665e83",
    "arch_57fa072e2ebd",
    "arch_588c23978578",
    "arch_5929d2f7c953",
    "arch_596aed1675bc",
    "arch_5a1e3b388ff2",
    "arch_5b4f9ef48e3b",
    "arch_5ba6728b6afa",
    "arch_5c6aaa535af3",
    "arch_5ec69fef5431",
    "arch_5f9c6f50acd7",
    "arch_5fece9dbfb5d",
    "arch_6226a7032ff5",
    "arch_63524fbe4146",
    "arch_63e2712b0d8c",
    "arch_64407ee0f3cd",
    "arch_649b534fcc1a",
    "arch_64bb1aaa8652",
    "arch_65d82c71ed87",
    "arch_660928fbe87a",
    "arch_66eda2a340a7",
    "arch_67216be7c2c4",
    "arch_680b524a7904",
    "arch_6b39dd52fede",
    "arch_6b783b8c3b5f",
    "arch_6c628f49a37f",
    "arch_6cc920fe1bb9",
    "arch_6de61162217e",
    "arch_6e9d2e7c3ed7",
    "arch_6ec948a642ac",
    "arch_6f0b8aa2f9e4",
    "arch_6f3c42bcb893",
    "arch_6f43a9b1b56e",
    "arch_6ff30ee29bc5",
    "arch_72583f74eeea",
    "arch_72ed8d3d8fca",
    "arch_73abda6c79d2",
    "arch_74c0530f0375",
    "arch_74d3e6a2a3af",
    "arch_752b20bb417a",
    "arch_7532ebee1a9b",
    "arch_755a0908dcb3",
    "arch_765a51533fcc",
    "arch_79cde11b5c21",
    "arch_7a1e03668cf8",
    "arch_7a3bd5a9b8f9",
    "arch_7aafaeec6cf3",
    "arch_7ad3a71d15fd",
    "arch_7bc499eefaa6",
    "arch_7be2c5f02837",
    "arch_7c0c69b4f459",
    "arch_7ca75f5a86b5",
    "arch_7d79947fdb78",
    "arch_7f12b514ba45",
    "arch_7f4f2d7e7b00",
    "arch_8081df385844",
    "arch_80b56fe4d44c",
    "arch_8101410ebdb4",
    "arch_8142c1aced68",
    "arch_83048d4a5057",
    "arch_84e2c4578683",
    "arch_856dedaabba3",
    "arch_86495e0d541d",
    "arch_868ac68d2777",
    "arch_8adaa4a63a48",
    "arch_8be3bde33303",
    "arch_8c507b05ffa6",
    "arch_8c97f72ea796",
    "arch_8e30759b71e1",
    "arch_8e802f56d666",
    "arch_8fd69f3994a4",
    "arch_9027ce631c80",
    "arch_91e20cc0cc06",
    "arch_92d1e08d3b5f",
    "arch_932136faeec5",
    "arch_942e646d4227",
    "arch_9444ca76867d",
    "arch_95fae451adb1",
    "arch_96fba8eb2ada",
    "arch_97ccf13390dc",
    "arch_99a0aedcbbb9",
    "arch_9a8fc472e2ea",
    "arch_9b643156bb48",
    "arch_9b79d1dc3db6",
    "arch_9be0531db18b",
    "arch_9bfd9fae74d9",
    "arch_9d86a10c9f53",
    "arch_9e795d17f42b",
    "arch_9f14bfe18e8a",
    "arch_9f33a5404b5a",
    "arch_9f598ae21d30",
    "arch_9fc759222a6c",
    "arch_9fdebc4c6ae4",
    "arch_a0371897e326",
    "arch_a057ead0d15a",
    "arch_a081f1cbf8b1",
    "arch_a0df09fdc4db",
    "arch_a4977bb1a698",
    "arch_a50533321276",
    "arch_a517773d3161",
    "arch_a574b57f8746",
    "arch_a5eace0ee548",
    "arch_a6c169a2edf4",
    "arch_a6dcde4258a3",
    "arch_a8ff6d080f7c",
    "arch_a91a966a68f7",
    "arch_a9ff9c499567",
    "arch_aa4c4f23d6db",
    "arch_abde4590a458",
    "arch_acb89bb3ba15",
    "arch_ad8892b42ec7",
    "arch_add9aaf10354",
    "arch_ade162a46464",
    "arch_ae55c26ddf41",
    "arch_afa14018a13b",
    "arch_b0f0d30899e2",
    "arch_b16bdbc4109a",
    "arch_b32181bed209",
    "arch_b34fa72cbab4",
    "arch_b421ec47b151",
    "arch_b42aa377e2e0",
    "arch_b4e7c5328d8e",
    "arch_b55820969f9c",
    "arch_b60b5646b627",
    "arch_b6271d813970",
    "arch_b637f89f8261",
    "arch_b672c0c2ffc0",
    "arch_b8ca8cade8e5",
    "arch_b927f500990e",
    "arch_b940295488cd",
    "arch_b96e75fd8e2b",
    "arch_bab2720ae208",
    "arch_bb83e3a55f0f",
    "arch_bbbbb77d09c4",
    "arch_bc0c6c515826",
    "arch_bc14d0103c4e",
    "arch_bc22aab6622d",
    "arch_bc24575e6d42",
    "arch_bc476942ca25",
    "arch_bc620d11c1ef",
    "arch_bcdcb4b42daa",
    "arch_bd5de714ba6a",
    "arch_bdac1fb64848",
    "arch_bef81f548f0a",
    "arch_c0416de23a79",
    "arch_c20481167c03",
    "arch_c217cf021f09",
    "arch_c35fd286abd0",
    "arch_c4322375ee28",
    "arch_c49a6b045d55",
    "arch_c5b9b254f86f",
    "arch_c76dfda5addc",
    "arch_c77d8ca5d731",
    "arch_ca8fe55f2b35",
    "arch_cb076296c15d",
    "arch_cc49e34a1e9d",
    "arch_d0618c6ed407",
    "arch_d2c19e7ccba8",
    "arch_d2d4d29b5f07",
    "arch_d3ed18c90137",
    "arch_d4436dd1ea4d",
    "arch_d4daf9f9e284",
    "arch_d5f87b0baf38",
    "arch_d6aec71ce08d",
    "arch_d76fd2b6079a",
    "arch_d85783e09d4a",
    "arch_d8a8e84357ef",
    "arch_d8c022b644a5",
    "arch_d8e431a52f45",
    "arch_d989ceb26d47",
    "arch_da4e3559d223",
    "arch_da70f9eceb94",
    "arch_daa52f42cfa6",
    "arch_dc1be5f0d51e",
    "arch_dd8540454f55",
    "arch_ddfaa6496ede",
    "arch_def8999c6dfb",
    "arch_df4c44a5c331",
    "arch_df4cca5e7b2a",
    "arch_dfa88153518e",
    "arch_dff308387a82",
    "arch_e0787fb471a6",
    "arch_e1223c49e1b8",
    "arch_e13f55fbd87b",
    "arch_e19feb4aa56e",
    "arch_e1ae5e5ae265",
    "arch_e3182a853293",
    "arch_e3e8b5e047a3",
    "arch_e3efcea42753",
    "arch_e52da5f4c871",
    "arch_e5b8db7ec68b",
    "arch_e67fc21ebf2d",
    "arch_e705c02d85cd",
    "arch_e7f47a0f0412",
    "arch_e80a7ab05662",
    "arch_e80f615639cf",
    "arch_e8cda37195fb",
    "arch_e90c819732d8",
    "arch_ea3d55fb6e90",
    "arch_eacdf0e7ef55",
    "arch_eb27a97cda51",
    "arch_eb4d11e72448",
    "arch_ebc365d6e4b6",
    "arch_ecbbd59498c8",
    "arch_ed549ae85831",
    "arch_ef1b9c13c7a5",
    "arch_ef294b8d73ef",
    "arch_ef8819e2f9c6",
    "arch_f0efee9d4229",
    "arch_f1159b94e136",
    "arch_f28873ac2801",
    "arch_f37280b242a9",
    "arch_f3ad4379bb7e",
    "arch_f4aee385e8a1",
    "arch_f774510a24ae",
    "arch_f78411f21be4",
    "arch_f7c8ff2e2f66",
    "arch_f7ff22e0d43a",
    "arch_f8a08c194b06",
    "arch_fa013efa9c6a",
    "arch_fa34ea38a4e4",
    "arch_fa494f88fa0f",
    "arch_fa7e79479e46",
    "arch_faeea629eee9",
    "arch_fb85396f2ffc",
    "arch_fc2c7f03c066",
    "arch_fe027b778f3a",
    "arch_fe49b744d20a",
    "arch_fe61cdad7cf2"
  ]
}
</dse_search_space>

<dse_selection_evidence>
{
  "candidate_count": 360,
  "candidate_dimensions": {
    "activation_banks": [
      2,
      4
    ],
    "cache_refill_data_width_bits": [
      512
    ],
    "cache_tile_count": [
      2
    ],
    "cache_tile_words": [
      256
    ],
    "compute_array_cols": [
      4,
      8,
      16,
      32
    ],
    "compute_array_rows": [
      4,
      8,
      16
    ],
    "cross_token_reuse_tokens": [
      4,
      8,
      16
    ],
    "fifo_depth": [
      32,
      64,
      128
    ],
    "lanes": [
      8,
      16
    ]
  },
  "eligible_candidates": [
    {
      "candidate_id": "arch_0149e4d15c31",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_01a712440a07",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_01f325b4e1de",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_021aa682ba93",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_0223bed1c6ae",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_02fc1bb8704f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_030144f2a595",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_03deb8c155ac",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_03df93145328",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_0558926f0517",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_05db4846c145",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_06a09b56b3a3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_07a4fc9326f5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_07aaf64e3958",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_07afe4d1afe3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_08fc81fe6157",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_0912b5c73a75",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_0a1c6c095ba9",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_0a8e4df9f2a4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_0af261125bb6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_0c4e9c9ee426",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_0c83d099727a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_0d92d0324bd5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_0dba4abc04da",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_0e61e297eab8",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_0ee3b53d937b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_0f82293c93e6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_0ff7933181b2",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_1004f24e4c78",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_113fb98e6716",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_1236fb4c9192",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_1275fee43ae3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_14c45ee748de",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_14e2444c6f29",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_14e636757912",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_1543ffa00444",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_1551705cb52f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_15e2da19c962",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_15fd90d23123",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_16d346427ca3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_1725e6854544",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_17987b6fd806",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_18c3ad671667",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_191aee2a4fac",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_19ee50aca96c",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_1bc0ae048ecc",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_1df5ff65d4d1",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_1df97cb6ec78",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_1ee0cb7ccb51",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_1f5488585695",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_214151a145a5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_216959e4bd8f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_2248a7a4915f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2281df1ebe7d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_22ecb49deb70",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_232bed4b6b9d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_23588396a98c",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_2359fa11ef76",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_2384df47b271",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_23e424f3907d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2516758567f0",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_25d6722185e0",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_274773aefb3b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_27ce70e6aaaf",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_28e04dc3fa70",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2a08f2ba5074",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_2a8e7c89b216",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2b980ec80526",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2c74420434ff",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2cc222a3f00a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2d260b75cf1f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2d99960b96e0",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_2dcaa331b416",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2dfe4a965719",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_2e19e450930e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2e3fdce0b439",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2ec11fd415c0",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_2ef0a2018ef7",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_2f5afaaec254",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_31920a847d25",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_31c1198760c0",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_32462ba2d356",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_32a1e7b3cb34",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_344e9f111ed9",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_344f207918df",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_352a9b7e4202",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_373d19512393",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_374daa9a0cdd",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_38d501cdd32a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_390057f4b1e9",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_399f4d831e5c",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_39a3ab841a08",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_39d69c7b2fb1",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_3b944678649e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_3c5fb574a252",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_3c7a03b2a050",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_3db46cf0a1ca",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_3eac00bab602",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_3fc57b48c731",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_3fd607bcea1a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_3fd8f432a88e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_3fedd13a9880",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_3ffa7b0ca613",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_402c4386596c",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_40873ed8c83f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_411a4077eb6a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_419e75b22818",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_441b25fd2df3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_467de8375899",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_46e1e10a6121",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_46f2067d1b25",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_476a360808e2",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_478d1ff5fbf4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_47c6bccd0f91",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_497eaf815b03",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_4cdc6a19fcb2",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_4d0cc8747989",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_4d7e0d132d62",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_4eec97b1af77",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_4f7bd0db6050",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_50255955605d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_513408c9134d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_513fc1a80269",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_514ae4f524cd",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_52a34a2c3820",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_52ec020a66d7",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_535aea705e57",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_5368ea328666",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_53d73e476ee6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_55b127fde887",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_55fee5ee1b47",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_5667f0665e83",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_57fa072e2ebd",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_588c23978578",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_5929d2f7c953",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_596aed1675bc",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_5a1e3b388ff2",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_5b4f9ef48e3b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_5ba6728b6afa",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_5c6aaa535af3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_5ec69fef5431",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_5f9c6f50acd7",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_5fece9dbfb5d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_6226a7032ff5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_63524fbe4146",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_63e2712b0d8c",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_64407ee0f3cd",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_649b534fcc1a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_64bb1aaa8652",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_65d82c71ed87",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_660928fbe87a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_66eda2a340a7",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_67216be7c2c4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_680b524a7904",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_6b39dd52fede",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_6b783b8c3b5f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_6c628f49a37f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_6cc920fe1bb9",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_6de61162217e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_6e9d2e7c3ed7",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_6ec948a642ac",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_6f0b8aa2f9e4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_6f3c42bcb893",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_6f43a9b1b56e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_6ff30ee29bc5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_72583f74eeea",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_72ed8d3d8fca",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_73abda6c79d2",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_74c0530f0375",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_74d3e6a2a3af",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_752b20bb417a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_7532ebee1a9b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_755a0908dcb3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_765a51533fcc",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_79cde11b5c21",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_7a1e03668cf8",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_7a3bd5a9b8f9",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_7aafaeec6cf3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_7ad3a71d15fd",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_7bc499eefaa6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_7be2c5f02837",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_7c0c69b4f459",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_7ca75f5a86b5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_7d79947fdb78",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_7f12b514ba45",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_7f4f2d7e7b00",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_8081df385844",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_80b56fe4d44c",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_8101410ebdb4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_8142c1aced68",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_83048d4a5057",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_84e2c4578683",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_856dedaabba3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_86495e0d541d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_868ac68d2777",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_8adaa4a63a48",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_8be3bde33303",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_8c507b05ffa6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_8c97f72ea796",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_8e30759b71e1",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_8e802f56d666",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_8fd69f3994a4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_9027ce631c80",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_91e20cc0cc06",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_92d1e08d3b5f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_932136faeec5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_942e646d4227",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_9444ca76867d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_95fae451adb1",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_96fba8eb2ada",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_97ccf13390dc",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_99a0aedcbbb9",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_9a8fc472e2ea",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_9b643156bb48",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_9b79d1dc3db6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_9be0531db18b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_9bfd9fae74d9",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_9d86a10c9f53",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_9e795d17f42b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_9f14bfe18e8a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_9f33a5404b5a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_9f598ae21d30",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_9fc759222a6c",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_9fdebc4c6ae4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a0371897e326",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a057ead0d15a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a081f1cbf8b1",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_a0df09fdc4db",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_a4977bb1a698",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a50533321276",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_a517773d3161",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a574b57f8746",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_a5eace0ee548",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a6c169a2edf4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a6dcde4258a3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a8ff6d080f7c",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a91a966a68f7",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_a9ff9c499567",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_aa4c4f23d6db",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_abde4590a458",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_acb89bb3ba15",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_ad8892b42ec7",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_add9aaf10354",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_ade162a46464",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_ae55c26ddf41",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_afa14018a13b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_b0f0d30899e2",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_b16bdbc4109a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_b32181bed209",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_b34fa72cbab4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_b421ec47b151",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_b42aa377e2e0",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_b4e7c5328d8e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_b55820969f9c",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_b60b5646b627",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_b6271d813970",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_b637f89f8261",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_b672c0c2ffc0",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_b8ca8cade8e5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_b927f500990e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_b940295488cd",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_b96e75fd8e2b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_bab2720ae208",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_bb83e3a55f0f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_bbbbb77d09c4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_bc0c6c515826",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_bc14d0103c4e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_bc22aab6622d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_bc24575e6d42",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_bc476942ca25",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_bc620d11c1ef",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_bcdcb4b42daa",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_bd5de714ba6a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_bdac1fb64848",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_bef81f548f0a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_c0416de23a79",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_c20481167c03",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_c217cf021f09",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_c35fd286abd0",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_c4322375ee28",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_c49a6b045d55",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_c5b9b254f86f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_c76dfda5addc",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_c77d8ca5d731",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_ca8fe55f2b35",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_cb076296c15d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_cc49e34a1e9d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d0618c6ed407",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d2c19e7ccba8",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d2d4d29b5f07",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d3ed18c90137",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d4436dd1ea4d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d4daf9f9e284",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d5f87b0baf38",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d6aec71ce08d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_d76fd2b6079a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d85783e09d4a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_d8a8e84357ef",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_d8c022b644a5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_d8e431a52f45",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_d989ceb26d47",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_da4e3559d223",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_da70f9eceb94",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_daa52f42cfa6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_dc1be5f0d51e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_dd8540454f55",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_ddfaa6496ede",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_def8999c6dfb",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_df4c44a5c331",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_df4cca5e7b2a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_dfa88153518e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_dff308387a82",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_e0787fb471a6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e1223c49e1b8",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e13f55fbd87b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e19feb4aa56e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e1ae5e5ae265",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e3182a853293",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_e3e8b5e047a3",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e3efcea42753",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e52da5f4c871",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e5b8db7ec68b",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    },
    {
      "candidate_id": "arch_e67fc21ebf2d",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_e705c02d85cd",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e7f47a0f0412",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e80a7ab05662",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e80f615639cf",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e8cda37195fb",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_e90c819732d8",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_ea3d55fb6e90",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_eacdf0e7ef55",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_eb27a97cda51",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_eb4d11e72448",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_ebc365d6e4b6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_ecbbd59498c8",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_ed549ae85831",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_ef1b9c13c7a5",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_ef294b8d73ef",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_ef8819e2f9c6",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_f0efee9d4229",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_f1159b94e136",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_f28873ac2801",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_f37280b242a9",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_f3ad4379bb7e",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_f4aee385e8a1",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_f774510a24ae",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_f78411f21be4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_f7c8ff2e2f66",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_f7ff22e0d43a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_f8a08c194b06",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_fa013efa9c6a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_fa34ea38a4e4",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 8,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 5
      }
    },
    {
      "candidate_id": "arch_fa494f88fa0f",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_fa7e79479e46",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 16,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_faeea629eee9",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 16,
        "fifo_depth": 32,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 8
      }
    },
    {
      "candidate_id": "arch_fb85396f2ffc",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 32,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_fc2c7f03c066",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 4,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_fe027b778f3a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 64,
        "lanes": 8,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_fe49b744d20a",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 4,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 4,
        "compute_array_rows": 8,
        "cross_token_reuse_tokens": 4,
        "fifo_depth": 64,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 16
      }
    },
    {
      "candidate_id": "arch_fe61cdad7cf2",
      "feasible": true,
      "hard_constraint_errors": [],
      "measurement": null,
      "measurement_scope": null,
      "measurement_status": "unmeasured",
      "parameters": {
        "activation_banks": 2,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "cross_token_reuse_tokens": 8,
        "fifo_depth": 128,
        "lanes": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        }
      },
      "qor_estimate": {
        "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
        "reason": "no compatible source-bound calibration sample",
        "status": "insufficient_evidence"
      },
      "resource_headroom": {
        "maximum_utilization_fraction": 0.85,
        "measured_utilization": {},
        "missing_resource_measurements": [
          "bram18",
          "bram36",
          "dsp",
          "ff",
          "lut",
          "uram"
        ],
        "status": "unknown"
      },
      "resource_lower_bounds": {
        "uram": 30
      }
    }
  ],
  "estimated_ranked_candidate_ids": [
    "arch_08fc81fe6157",
    "arch_31c1198760c0",
    "arch_3fd8f432a88e",
    "arch_3fedd13a9880",
    "arch_513408c9134d",
    "arch_55b127fde887",
    "arch_5b4f9ef48e3b",
    "arch_63e2712b0d8c",
    "arch_6e9d2e7c3ed7",
    "arch_74c0530f0375",
    "arch_e5b8db7ec68b",
    "arch_fe61cdad7cf2",
    "arch_1004f24e4c78",
    "arch_1275fee43ae3",
    "arch_65d82c71ed87",
    "arch_660928fbe87a",
    "arch_74d3e6a2a3af",
    "arch_755a0908dcb3",
    "arch_8081df385844",
    "arch_acb89bb3ba15",
    "arch_c35fd286abd0",
    "arch_cb076296c15d",
    "arch_da70f9eceb94",
    "arch_df4cca5e7b2a",
    "arch_01a712440a07",
    "arch_06a09b56b3a3",
    "arch_23e424f3907d",
    "arch_2cc222a3f00a",
    "arch_3ffa7b0ca613",
    "arch_8e30759b71e1",
    "arch_a4977bb1a698",
    "arch_b32181bed209",
    "arch_b927f500990e",
    "arch_c5b9b254f86f",
    "arch_da4e3559d223",
    "arch_ea3d55fb6e90",
    "arch_0a8e4df9f2a4",
    "arch_0ee3b53d937b",
    "arch_6226a7032ff5",
    "arch_72583f74eeea",
    "arch_932136faeec5",
    "arch_d85783e09d4a",
    "arch_02fc1bb8704f",
    "arch_0e61e297eab8",
    "arch_afa14018a13b",
    "arch_df4c44a5c331",
    "arch_e8cda37195fb",
    "arch_ef8819e2f9c6",
    "arch_191aee2a4fac",
    "arch_411a4077eb6a",
    "arch_8c507b05ffa6",
    "arch_9fdebc4c6ae4",
    "arch_d2c19e7ccba8",
    "arch_ebc365d6e4b6",
    "arch_0223bed1c6ae",
    "arch_2c74420434ff",
    "arch_5ba6728b6afa",
    "arch_7d79947fdb78",
    "arch_7f12b514ba45",
    "arch_9b643156bb48",
    "arch_ae55c26ddf41",
    "arch_d76fd2b6079a",
    "arch_f37280b242a9",
    "arch_f7ff22e0d43a",
    "arch_fb85396f2ffc",
    "arch_fe027b778f3a",
    "arch_344e9f111ed9",
    "arch_52a34a2c3820",
    "arch_a8ff6d080f7c",
    "arch_bb83e3a55f0f",
    "arch_c4322375ee28",
    "arch_d4daf9f9e284",
    "arch_05db4846c145",
    "arch_2a8e7c89b216",
    "arch_2b980ec80526",
    "arch_478d1ff5fbf4",
    "arch_4d7e0d132d62",
    "arch_6b783b8c3b5f",
    "arch_6c628f49a37f",
    "arch_a517773d3161",
    "arch_a6dcde4258a3",
    "arch_bc620d11c1ef",
    "arch_d989ceb26d47",
    "arch_f4aee385e8a1",
    "arch_5929d2f7c953",
    "arch_66eda2a340a7",
    "arch_6f0b8aa2f9e4",
    "arch_7c0c69b4f459",
    "arch_7f4f2d7e7b00",
    "arch_91e20cc0cc06",
    "arch_95fae451adb1",
    "arch_99a0aedcbbb9",
    "arch_daa52f42cfa6",
    "arch_e19feb4aa56e",
    "arch_eb27a97cda51",
    "arch_f8a08c194b06",
    "arch_113fb98e6716",
    "arch_352a9b7e4202",
    "arch_3db46cf0a1ca",
    "arch_67216be7c2c4",
    "arch_752b20bb417a",
    "arch_856dedaabba3",
    "arch_9f14bfe18e8a",
    "arch_ad8892b42ec7",
    "arch_b637f89f8261",
    "arch_bc14d0103c4e",
    "arch_c76dfda5addc",
    "arch_faeea629eee9",
    "arch_402c4386596c",
    "arch_5667f0665e83",
    "arch_5fece9dbfb5d",
    "arch_8c97f72ea796",
    "arch_9e795d17f42b",
    "arch_b96e75fd8e2b",
    "arch_03df93145328",
    "arch_19ee50aca96c",
    "arch_53d73e476ee6",
    "arch_bef81f548f0a",
    "arch_d5f87b0baf38",
    "arch_f78411f21be4",
    "arch_0ff7933181b2",
    "arch_1ee0cb7ccb51",
    "arch_4cdc6a19fcb2",
    "arch_50255955605d",
    "arch_7532ebee1a9b",
    "arch_7be2c5f02837",
    "arch_7ca75f5a86b5",
    "arch_86495e0d541d",
    "arch_a50533321276",
    "arch_bbbbb77d09c4",
    "arch_e3182a853293",
    "arch_eacdf0e7ef55",
    "arch_0d92d0324bd5",
    "arch_0dba4abc04da",
    "arch_14e636757912",
    "arch_18c3ad671667",
    "arch_274773aefb3b",
    "arch_467de8375899",
    "arch_5a1e3b388ff2",
    "arch_83048d4a5057",
    "arch_b55820969f9c",
    "arch_bd5de714ba6a",
    "arch_d8a8e84357ef",
    "arch_d8e431a52f45",
    "arch_021aa682ba93",
    "arch_030144f2a595",
    "arch_0558926f0517",
    "arch_216959e4bd8f",
    "arch_344f207918df",
    "arch_374daa9a0cdd",
    "arch_2dfe4a965719",
    "arch_38d501cdd32a",
    "arch_46f2067d1b25",
    "arch_55fee5ee1b47",
    "arch_5ec69fef5431",
    "arch_ecbbd59498c8",
    "arch_07afe4d1afe3",
    "arch_14c45ee748de",
    "arch_16d346427ca3",
    "arch_17987b6fd806",
    "arch_80b56fe4d44c",
    "arch_d6aec71ce08d",
    "arch_01f325b4e1de",
    "arch_0af261125bb6",
    "arch_0c4e9c9ee426",
    "arch_3c5fb574a252",
    "arch_3c7a03b2a050",
    "arch_47c6bccd0f91",
    "arch_649b534fcc1a",
    "arch_868ac68d2777",
    "arch_9be0531db18b",
    "arch_a5eace0ee548",
    "arch_cc49e34a1e9d",
    "arch_e90c819732d8",
    "arch_1bc0ae048ecc",
    "arch_1df5ff65d4d1",
    "arch_390057f4b1e9",
    "arch_39d69c7b2fb1",
    "arch_497eaf815b03",
    "arch_5368ea328666",
    "arch_6ec948a642ac",
    "arch_8be3bde33303",
    "arch_a0371897e326",
    "arch_d3ed18c90137",
    "arch_e13f55fbd87b",
    "arch_f7c8ff2e2f66",
    "arch_2dcaa331b416",
    "arch_3b944678649e",
    "arch_63524fbe4146",
    "arch_6f43a9b1b56e",
    "arch_7a3bd5a9b8f9",
    "arch_8101410ebdb4",
    "arch_9f598ae21d30",
    "arch_b16bdbc4109a",
    "arch_bdac1fb64848",
    "arch_d0618c6ed407",
    "arch_e1ae5e5ae265",
    "arch_fa7e79479e46",
    "arch_39a3ab841a08",
    "arch_4eec97b1af77",
    "arch_d2d4d29b5f07",
    "arch_d4436dd1ea4d",
    "arch_d8c022b644a5",
    "arch_dc1be5f0d51e",
    "arch_96fba8eb2ada",
    "arch_9fc759222a6c",
    "arch_b0f0d30899e2",
    "arch_b672c0c2ffc0",
    "arch_e3efcea42753",
    "arch_ed549ae85831",
    "arch_2281df1ebe7d",
    "arch_23588396a98c",
    "arch_2516758567f0",
    "arch_31920a847d25",
    "arch_5f9c6f50acd7",
    "arch_7a1e03668cf8",
    "arch_7aafaeec6cf3",
    "arch_7ad3a71d15fd",
    "arch_8adaa4a63a48",
    "arch_a574b57f8746",
    "arch_b42aa377e2e0",
    "arch_fa34ea38a4e4",
    "arch_2359fa11ef76",
    "arch_3fd607bcea1a",
    "arch_40873ed8c83f",
    "arch_72ed8d3d8fca",
    "arch_9027ce631c80",
    "arch_97ccf13390dc",
    "arch_b4e7c5328d8e",
    "arch_bc0c6c515826",
    "arch_bc24575e6d42",
    "arch_c217cf021f09",
    "arch_dff308387a82",
    "arch_f0efee9d4229",
    "arch_0149e4d15c31",
    "arch_07aaf64e3958",
    "arch_2e3fdce0b439",
    "arch_441b25fd2df3",
    "arch_a057ead0d15a",
    "arch_c77d8ca5d731",
    "arch_2a08f2ba5074",
    "arch_32a1e7b3cb34",
    "arch_4d0cc8747989",
    "arch_57fa072e2ebd",
    "arch_6b39dd52fede",
    "arch_bcdcb4b42daa",
    "arch_2ef0a2018ef7",
    "arch_5c6aaa535af3",
    "arch_64bb1aaa8652",
    "arch_6cc920fe1bb9",
    "arch_bab2720ae208",
    "arch_fa013efa9c6a",
    "arch_03deb8c155ac",
    "arch_07a4fc9326f5",
    "arch_28e04dc3fa70",
    "arch_3fc57b48c731",
    "arch_765a51533fcc",
    "arch_9b79d1dc3db6",
    "arch_a91a966a68f7",
    "arch_b60b5646b627",
    "arch_ddfaa6496ede",
    "arch_e1223c49e1b8",
    "arch_e705c02d85cd",
    "arch_e7f47a0f0412",
    "arch_2248a7a4915f",
    "arch_25d6722185e0",
    "arch_2ec11fd415c0",
    "arch_a6c169a2edf4",
    "arch_a9ff9c499567",
    "arch_bc22aab6622d",
    "arch_c0416de23a79",
    "arch_e0787fb471a6",
    "arch_e52da5f4c871",
    "arch_e80a7ab05662",
    "arch_f3ad4379bb7e",
    "arch_f774510a24ae",
    "arch_2e19e450930e",
    "arch_64407ee0f3cd",
    "arch_b940295488cd",
    "arch_bc476942ca25",
    "arch_fa494f88fa0f",
    "arch_fe49b744d20a",
    "arch_0a1c6c095ba9",
    "arch_214151a145a5",
    "arch_2384df47b271",
    "arch_46e1e10a6121",
    "arch_7bc499eefaa6",
    "arch_8fd69f3994a4",
    "arch_92d1e08d3b5f",
    "arch_9a8fc472e2ea",
    "arch_add9aaf10354",
    "arch_b8ca8cade8e5",
    "arch_ca8fe55f2b35",
    "arch_ef294b8d73ef",
    "arch_1543ffa00444",
    "arch_1551705cb52f",
    "arch_1df97cb6ec78",
    "arch_1f5488585695",
    "arch_232bed4b6b9d",
    "arch_27ce70e6aaaf",
    "arch_3eac00bab602",
    "arch_535aea705e57",
    "arch_9d86a10c9f53",
    "arch_a081f1cbf8b1",
    "arch_ef1b9c13c7a5",
    "arch_f1159b94e136",
    "arch_0912b5c73a75",
    "arch_1725e6854544",
    "arch_22ecb49deb70",
    "arch_399f4d831e5c",
    "arch_419e75b22818",
    "arch_73abda6c79d2",
    "arch_15e2da19c962",
    "arch_514ae4f524cd",
    "arch_6de61162217e",
    "arch_6f3c42bcb893",
    "arch_aa4c4f23d6db",
    "arch_eb4d11e72448",
    "arch_14e2444c6f29",
    "arch_52ec020a66d7",
    "arch_596aed1675bc",
    "arch_9444ca76867d",
    "arch_c20481167c03",
    "arch_c49a6b045d55",
    "arch_2d260b75cf1f",
    "arch_373d19512393",
    "arch_588c23978578",
    "arch_79cde11b5c21",
    "arch_8142c1aced68",
    "arch_84e2c4578683",
    "arch_8e802f56d666",
    "arch_b421ec47b151",
    "arch_dd8540454f55",
    "arch_dfa88153518e",
    "arch_e3e8b5e047a3",
    "arch_fc2c7f03c066",
    "arch_0c83d099727a",
    "arch_0f82293c93e6",
    "arch_2d99960b96e0",
    "arch_4f7bd0db6050",
    "arch_9f33a5404b5a",
    "arch_a0df09fdc4db",
    "arch_ade162a46464",
    "arch_b34fa72cbab4",
    "arch_b6271d813970",
    "arch_def8999c6dfb",
    "arch_e67fc21ebf2d",
    "arch_f28873ac2801",
    "arch_1236fb4c9192",
    "arch_32462ba2d356",
    "arch_476a360808e2",
    "arch_6ff30ee29bc5",
    "arch_9bfd9fae74d9",
    "arch_e80f615639cf",
    "arch_15fd90d23123",
    "arch_2f5afaaec254",
    "arch_513fc1a80269",
    "arch_680b524a7904",
    "arch_942e646d4227",
    "arch_abde4590a458"
  ],
  "measured_pareto_candidates": [],
  "measurement_summary": {
    "complete": false,
    "implementation_infeasible_count": 0,
    "legal_candidate_count": 360,
    "measured_candidate_count": 0,
    "unmeasured_candidate_count": 360
  },
  "policy": {
    "candidate_ids_and_parameters_are_complete_for_selection": true,
    "eligible_candidates_are_the_only_selectable_candidates": true,
    "qor_is_valid_only_when_measurement_status_is_measured": true,
    "unmeasured_candidates_must_be_selected_before_pareto_selection": true
  },
  "qor_calibration_samples": [
    {
      "board": {
        "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
        "resource_budget": {
          "bram": 2160,
          "bram18": 4320,
          "bram36": 2160,
          "dsp": 6840,
          "ff": 2364480,
          "lut": 1182240,
          "uram": 960
        },
        "resource_budget_source": "real_vivado_target_part_probe"
      },
      "clock_frequency_mhz": 157.43073047858942,
      "cost_features": {
        "family": "qwen2",
        "linear_schedule": "context_interleaved_fp_pipeline_v1",
        "memory_implementation": [
          "xpm_uram",
          "xpm_bram",
          "xpm_uram"
        ],
        "parameters": {
          "activation_banks": 1,
          "activation_memory": "xpm_bram",
          "burst_beats": 1,
          "clock_target_m_hz": 250,
          "clock_target_mhz": 250,
          "compute_array_cols": 16,
          "compute_array_rows": 8,
          "compute_backend": "vivado_fp_ip",
          "design_id": "qwen2",
          "elem_bits": 16,
          "fifo_depth": 4,
          "fifo_memory": "xpm_bram",
          "head_dim": 64,
          "hidden_size": 896,
          "input_bits": 32,
          "intermediate_size": 4864,
          "lanes": 16,
          "large_cache_memory": "xpm_uram",
          "max_seq_len": 16,
          "model_type": "qwen2",
          "num_kv_heads": 2,
          "num_q_heads": 14,
          "output_bits": 32,
          "pipeline_depth": 1,
          "target_max_seq_len": 16,
          "weight_banks": 1,
          "weight_banks_by_role": {
            "weight": 1,
            "weight_attn_out": 1,
            "weight_mlp_down": 1,
            "weight_mlp_gate": 1,
            "weight_mlp_up": 1,
            "weight_qkv": 1,
            "weight_qkv_bias": 1
          },
          "weight_memory": "xpm_uram"
        },
        "part": "xcvu9p_CIV-flgb2104-2-i",
        "precision_bits": 16,
        "proxies": {
          "bram18": 180,
          "bram36": 180,
          "clock_frequency_mhz": 1.0,
          "cycles": 1077661224.0,
          "dsp": 768,
          "ff": 77184,
          "lut": 2400,
          "uram": 1032
        },
        "workload": {
          "batch_size": 1,
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 16,
          "model_layers": 24,
          "processed_tokens": 16,
          "runtime_sequence": [
            "load input_tokens",
            "load layer 0 weights into weight_buffer_a",
            "start accelerator",
            "prefetch next layer weights into inactive weight buffer while active layer computes",
            "poll runtime_status or done",
            "read output_tokens"
          ],
          "sequence_length": 16,
          "weight_transfer_rules": [
            "all addresses are byte offsets from the accelerator DDR window base",
            "all transfer byte counts are aligned to axi_data_width_bits",
            "weight_buffer_a and weight_buffer_b alternate by layer to allow prefetch of layer N+1 while layer N computes"
          ]
        }
      },
      "design_parameters_source": {
        "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala": "package spatialaccagent.generated\n\nimport spatialaccagent.templates._\n\nobject GeneratedDesignParams {\n  val designId: String = \"qwen2\"\n  val modelType: String = \"qwen2\"\n  val targetMaxSeqLen: Int = 16\n  val clockTargetMHz: Int = 250\n  val inputBits: Int = 32\n  val elemBits: Int = 16\n  val outputBits: Int = 32\n  val lanes: Int = 16\n  val computeArrayRows: Int = 8\n  val computeArrayCols: Int = 16\n  val computeBackend: String = \"vivado_fp_ip\"\n  val weightMemory: String = \"xpm_uram\"\n  val activationMemory: String = \"xpm_bram\"\n  val fifoMemory: String = \"xpm_bram\"\n  val largeCacheMemory: String = \"xpm_uram\"\n  val fifoDepth: Int = 4\n  val weightBanks: Int = 1\n  val activationBanks: Int = 1\n  val weightBanksByRole: Map[String, Int] = Map(\"weight\" -> 1, \"weight_attn_out\" -> 1, \"weight_mlp_down\" -> 1, \"weight_mlp_gate\" -> 1, \"weight_mlp_up\" -> 1, \"weight_qkv\" -> 1, \"weight_qkv_bias\" -> 1)\n  val burstBeats: Int = 1\n  val pipelineDepth: Int = 1\n  val operatorSequence: Seq[String] = Seq(\"rms_norm_1\", \"self_attention\", \"residual_add_1\", \"rms_norm_2\", \"mlp_gate_proj\", \"mlp_up_proj\", \"activation_mul\", \"mlp_down_proj\", \"residual_add_2\")\n  val stageIds: Seq[String] = Seq(\"stage_00_rms_norm_1\", \"stage_01_self_attention\", \"stage_02_residual_add_1\", \"stage_03_rms_norm_2\", \"stage_04_mlp_gate_proj\", \"stage_05_mlp_up_proj\", \"stage_06_activation_mul\", \"stage_07_mlp_down_proj\", \"stage_08_residual_add_2\")\n  val params = LlamaStyleBlockParams(batchSize = 16, computeArrayCols = 16, computeArrayRows = 8, elemBits = 16, headDim = 64, hiddenSize = 896, inputBits = 32, intermediateSize = 4864, kvHeads = 2, lanes = 16, maxSeqLen = 16, outputBits = 32, qHeads = 14)\n}\n"
      },
      "evidence_paths": [
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/formal_20260922_r432_qwen2/backend_board/case_diagnostics/app_shell_runtime_vivado.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/formal_20260922_r432_qwen2/app_shell_runtime_bitstream/app_shell_synth_utilization.rpt",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/formal_20260922_r432_qwen2/app_shell_runtime_bitstream/app_shell_synth_timing.rpt",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/formal_20260922_r432_qwen2/app_shell_runtime_bitstream/app_shell_synth_power.rpt",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/formal_20260922_r432_qwen2/backend_board/qor/source_cycle_analysis.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/formal_20260922_r432_qwen2/backend_board/qor/qor_metrics.json"
      ],
      "measurement_scope": "generated_kernel_synthesis",
      "metric_quality": "post_synthesis_clock_and_analytical_source_cycles",
      "parameters": {
        "activation_banks": 1,
        "activation_memory": "xpm_bram",
        "burst_beats": 1,
        "clock_target_m_hz": 250,
        "clock_target_mhz": 250,
        "compute_array_cols": 16,
        "compute_array_rows": 8,
        "compute_backend": "vivado_fp_ip",
        "design_id": "qwen2",
        "elem_bits": 16,
        "fifo_depth": 4,
        "fifo_memory": "xpm_bram",
        "head_dim": 64,
        "hidden_size": 896,
        "input_bits": 32,
        "intermediate_size": 4864,
        "lanes": 16,
        "large_cache_memory": "xpm_uram",
        "max_seq_len": 16,
        "model_type": "qwen2",
        "num_kv_heads": 2,
        "num_q_heads": 14,
        "output_bits": 32,
        "pipeline_depth": 1,
        "target_max_seq_len": 16,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_mlp_down": 1,
          "weight_mlp_gate": 1,
          "weight_mlp_up": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        },
        "weight_memory": "xpm_uram"
      },
      "performance_estimation": {
        "assumptions": [
          "The supplied synthesis evidence binds this analysis to archive SHA-256 2e55182fa96b5ff0d581d328cb44934247a17e077f7ca756536ceaff1594ff5c; no further synthesis attestation is needed.",
          "The configured sequence is 16 positions with batch size 1, hidden size 896, and 16 lanes. Thus processed_tokens is 16, and one hidden vector is 56 ingress beats.",
          "The single physical Qwen2Block is reused sequentially for 24 model layers. Initial layer weights are preloaded, external backpressure and memory-transfer stalls are excluded, and inter-layer handoff is assumed to be zero.",
          "For the nominal schedule, accepted serialized-IP requests see result-ready high; the stated Vivado C_Latency values bound their issue/wait service. Tagged add/multiply pipelines use the configured C_Rate=1 and their actual source contexts and reductions.",
          "The cycle accounting uses the source FSM issue, wait, memory-read, and transfer transitions. This is an analytical projection, not a measured run; no simulation was executed."
        ],
        "counter_source": "source_schedule_analysis",
        "derivation": "The emitted GeneratedAcceleratorTop instantiates Qwen2Block. Its connected path is RMSNorm1 -> QKVProjection -> RoPE -> AttentionGQA -> ResidualAdd1 -> RMSNorm2 -> GatedMLP (gate and up Linear projections, SiLU Activation, ElementwiseMul, down Linear projection) -> ResidualAdd2 -> io_out. The estimate follows that complete path. The supplied matching expanded Linear and AttentionGQA RTL is omitted only because it exceeds the size limit; their loop, counter, and handshake behavior is taken from the included matching Linear.scala and Attention.scala sources, with connectivity checked against Qwen2Block.sv.\n\nRuntime configuration gives 896 hidden elements and 16 lanes: 896/16=56 beats per token. The generated top uses 512-bit streams, or 16 32-bit ingress elements per beat. Workload batch_size*sequence_length=1*16, so processed_tokens=16 (not multiplied by 24 layers). The accepted start can coincide with the first RMSNorm input handshake: the wrapper asserts active for io.start and RMSNorm1 is ready with its preloaded weights. Therefore start_to_first_input_cycles=0.\n\nPer-stage service/fill/drain accounting (cycles; terms below count source loop work and serialized FSM service, not a sum of every operator's latency for every token):\n- RMSNorm1: collect 56 beats; accumulation performs 56 memory read/capture pairs and 896 serial lane iterations. Each lane pairs the sum add with the square multiply, then performs the square-sum add: 896*(12+1+12+1)=23,296 cycles. Final mean/epsilon/sqrt/reciprocal issue-waits contribute 10+13+30+30=83. The 56-beat normalize/scale/emit loop is 56*(2+10+10+1)=1,288. Including 56 collection cycles gives a source service interval of 24,835 cycles between token starts absent downstream stalls.\n- QKV Linear: dimensions are 896->1152, with 56 input rows, 72 output beats, 8 MAC rows, and 16 MAC columns. The source has 2 output groups per beat, 144 groups/token, and 56 terms/group. The context count is highestOneBit(min(56,16))=16. Each group accounts for 56 one-per-cycle read requests, 69 cycles for multiplier/reduction/accumulator fill and final drain (mul latency 9, four reduction-add levels at 12, accumulator add at 12), and 75 cycles for the five context-fold phases (8,4,2,1, and bias; C_Rate=1 with the phase drains). Including the group setup/read control gives 202 cycles/group, or 144*202=29,088 cycles/token. The two input banks let RMSNorm1 run ahead initially. Once their actual reuse condition is reached, they backpressure RMSNorm1; applying the bank-release and RMSNorm emit-drain conditions yields the RLE ingress gaps below.\n- QKV reformat and RoPE: QKV framing is 14 heads*8 beats. QKVProjection reads three fields of eight scalar lanes (48 read/capture cycles per output beat plus its output handshake), then RoPE handles eight serialized lanes per beat using its memory reads, parallel multiply issue/wait, and add issue/wait. The combined per-token reformat/RoPE service is about 72 collection cycles + 5,488 reformat cycles + 26,096 RoPE cycles =31,656 cycles. This path is slower than the QKV Linear, but its projected-memory and two Linear output banks absorb the finite backlog for this 16-token ingress sequence; it does not create an additional ingress gap in the listed run. It is included in the first-token fill and attention-input timing.\n- AttentionGQA and Softmax: collection is sequence-framed, but the RTL starts workRow when tokenReady(workRow) is set; it does not wait for collectionClosed before row 0. With QKV/RoPE delivery, each row is ready before the preceding, much longer attention row finishes. For row r, the actual causal score loop is 14 heads*(r+1) keys*64 dimensions. Each dimension serializes fp_mul (9-cycle IP) and fp_add (12-cycle IP); including issue/wait transitions, memory read/capture, score scaling, and write gives about 1,614 cycles/key/head. Context uses 64 parallel multiply lanes and 64 parallel add lanes, with read/capture and accumulator write, about 30 cycles/key/head. The output projection is 896->896 with 14 input beats, 56 output beats, two output groups, and the same 202-cycle group service: 112*202=22,624 cycles/row. Softmax scans all 16 causal/masked positions and emits all 16 probabilities; its single-lane probability conversion/divide loop is retained. Summing row loop bounds, projection, softmax, and context/finalize control gives about 3,512,136 cycles from row-0 availability through the final attention output. The full sequence has been collected before this work finishes; there is no additional post-collection barrier wait.\n- ResidualAdd1 and RMSNorm2: ResidualAdd1 joins the computed attention beat with the stored input residual through ready/valid FIFOs and 16 parallel adds. RMSNorm2 then repeats the 56-beat collection, 896-lane reduction, final normalization, and emission service. Its output is the actual input to the MLP, not a terminus at attention.\n- GatedMLP and final residual: gate and up projections run concurrently. Each 896->4864 Linear has 608 groups/token at 202 cycles/group, 122,816 cycles. SiLU is serialized over 16 lanes for each of 304 intermediate beats: each lane's classify, conversion, ROM, product conversion, and scale sequence is 42 cycles; including beat accept/emit gives 304*(16*42+2)=204,896 cycles. ElementwiseMul joins the independently buffered up and activated streams; its 16-lane multiply and FIFO service are overlapped with activation, with the final product requiring about 11 cycles. The 4864->896 down Linear has 112 output groups; 304 read terms, 69 arithmetic fill/drain, 75 fold, and 2 setup cycles give 450/group, or 50,400 cycles. ResidualAdd2 is the final 56-beat join and transfer, about 56*14=784 cycles. Thus the tail is included through the block's actual io_out driver.\n\nThe first QKV/RoPE token becomes available about 85,579 cycles after first ingress. The attention row calculation totals about 3,512,136 cycles; the preceding row work makes all required query tokens ready before their row is selected. The final-token-relative attention completion is therefore approximately 85,579+3,512,136-404,267=3,193,448 cycles. Adding the final residual/RMS2/MLP/down-projection/residual tail (approximately 404,415 cycles from the final attention beat) gives last_token_start_to_completion_cycles=3,597,863. This drain is relative to the actual final ingress token start, not an idealized start.\n\nThe ingress intervals cover exactly 15 gaps: 7*24,835, then 26,806 when the nested QKV Linear input-bank release delays the RMSNorm output drain, then 7*29,088 at the QKV Linear service interval. Their sum is 404,267 cycles. The steady-state ingress II is the QKV Linear's 29,088-cycle service interval for this buffered 16-token run. The framework's per-layer expression is 0+404,267+3,597,863=4,002,130 cycles; sequential reuse for 24 layers projects 96,051,120 cycles under the stated zero-handoff assumption.",
        "estimate_scope": "generated_pipeline_schedule",
        "latency_cycles": 96051120,
        "measurement_kind": "analytical_estimate",
        "model_layers": 24,
        "performance_model": "single_block_reuse_operator_token_pipeline_v2_no_handoff",
        "pipeline_schedule": {
          "exposed_layer_handoff_cycles": 0,
          "last_token_start_to_completion_cycles": 3597863,
          "mode": "single_block_reuse",
          "operator_token_overlap": true,
          "start_to_first_input_cycles": 0,
          "steady_state_ii_cycles": 29088,
          "token_start_intervals": [
            {
              "cycles": 24835,
              "repetitions": 7
            },
            {
              "cycles": 26806,
              "repetitions": 1
            },
            {
              "cycles": 29088,
              "repetitions": 7
            }
          ]
        },
        "processed_tokens": 16,
        "schedule_policy": {
          "external_backpressure_cycles": 0,
          "initial_layer_weights_preloaded": true,
          "mode": "nominal_no_stall",
          "model_layer_execution": "sequential_reuse_of_the_same_block",
          "next_layer_weight_prefetch": "overlapped_with_current_layer_compute",
          "operator_initiation_interval_source": "synthesized_ip_configuration_and_rtl",
          "performance_model": "single_block_reuse_operator_token_pipeline_v2_no_handoff",
          "physical_transformer_blocks": 1
        },
        "source_fingerprint": "973d2bb8c5478b46d7c49fba707160b7f205f3407ca3335fba1d01312ce05763",
        "source_refs": [
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/scripts/gen_xilinx_fp_ips_23.tcl",
          "generated/chisel/simulation/fpga_ip_modules.txt",
          "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala",
          "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/Attention.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/Linear.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/Norm.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/QKVProjection.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/RoPE.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/Softmax.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/FFN.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/Activation.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/Elementwise.scala",
          "generated/chisel/src/main/scala/spatialaccagent/templates/PhysicalResources.scala",
          "generated/chisel/vivado/GeneratedAcceleratorTop.sv",
          "generated/chisel/vivado/GeneratedAxiDdrTop.sv",
          "generated/chisel/vivado/Qwen2Block.sv",
          "generated/chisel/vivado/RMSNorm.sv",
          "generated/chisel/vivado/VectorNorm.sv",
          "generated/chisel/vivado/QKVProjection.sv",
          "generated/chisel/vivado/RoPE.sv",
          "generated/chisel/vivado/Softmax.sv",
          "generated/chisel/vivado/GatedMLP.sv",
          "generated/chisel/vivado/Activation.sv",
          "generated/chisel/vivado/ElementwiseMul.sv",
          "generated/chisel/vivado/ResidualAdd.sv",
          "generated/chisel/vivado/PhysicalFp32Add.sv",
          "generated/chisel/vivado/PhysicalFp32Mul.sv",
          "generated/chisel/vivado/PhysicalFp32Div.sv",
          "generated/chisel/vivado/PhysicalFp32Sqrt.sv",
          "generated/chisel/vivado/PhysicalFp32Sub.sv",
          "generated/chisel/vivado/PhysicalFp32CompareLt.sv",
          "generated/chisel/vivado/PhysicalFp32AddPipeline.sv",
          "generated/chisel/vivado/PhysicalFp32MulPipeline.sv",
          "generated/chisel/vivado/PhysicalFp32ToSigned.sv",
          "generated/chisel/vivado/PhysicalSignedToFp32.sv",
          "generated/chisel/vivado/PhysicalFp16ToFp32.sv",
          "generated/chisel/vivado/PhysicalFp32ToFp16.sv",
          "generated/chisel/vivado/PhysicalStreamFifo.sv",
          "generated/chisel/vivado/PhysicalStreamFifo_11.sv",
          "generated/chisel/vivado/PhysicalStreamFifo_2.sv",
          "generated/chisel/vivado/PhysicalStreamFifo_3.sv",
          "generated/chisel/vivado/PhysicalSimpleDualPortMemory.sv",
          "generated/chisel/vivado/PhysicalSimpleDualPortMemory_17.sv"
        ],
        "status": "pass",
        "synthesis_source_archive_sha256": "2e55182fa96b5ff0d581d328cb44934247a17e077f7ca756536ceaff1594ff5c"
      },
      "performance_model": "single_block_reuse_operator_token_pipeline_v2_no_handoff",
      "performance_tokens_per_second": 26.224490538553123,
      "resources": {
        "bram18": 31,
        "bram36": 1204,
        "dsp": 3101,
        "ff": 608045,
        "lut": 364708,
        "uram": 855
      },
      "schema_version": "spatialaccagent.dse_qor_sample.v1",
      "source_fingerprint": "973d2bb8c5478b46d7c49fba707160b7f205f3407ca3335fba1d01312ce05763",
      "synthesis_source_archive_sha256": "2e55182fa96b5ff0d581d328cb44934247a17e077f7ca756536ceaff1594ff5c",
      "timestamp": "2026-10-16T13:44:33.938552Z",
      "workload": {
        "batch_size": 1,
        "hidden_size": 896,
        "intermediate_size": 4864,
        "lanes": 16,
        "model_layers": 24,
        "processed_tokens": 16,
        "runtime_sequence": [
          "load input_tokens",
          "load layer 0 weights into weight_buffer_a",
          "start accelerator",
          "prefetch next layer weights into inactive weight buffer while active layer computes",
          "poll runtime_status or done",
          "read output_tokens"
        ],
        "sequence_length": 16,
        "weight_transfer_rules": [
          "all addresses are byte offsets from the accelerator DDR window base",
          "all transfer byte counts are aligned to axi_data_width_bits",
          "weight_buffer_a and weight_buffer_b alternate by layer to allow prefetch of layer N+1 while layer N computes"
        ]
      }
    }
  ],
  "qor_estimator": {
    "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
    "validation": {
      "held_out_prediction_count": 0,
      "mean_absolute_error_for_zero_actual": {},
      "mean_relative_absolute_error": {},
      "method": "leave_one_source_fingerprint_out",
      "sample_count": 1,
      "status": "insufficient_independent_samples"
    }
  },
  "qor_targets": {
    "power_report_required": false,
    "source": "task_spec"
  },
  "resource_budget": {
    "bram": 2160,
    "bram18": 4320,
    "bram36": 2160,
    "dsp": 6840,
    "ff": 2364480,
    "lut": 1182240,
    "uram": 960
  },
  "schema_version": "spatialaccagent.stage4_dse_llm_selection_evidence.v1",
  "selection_objective": "Meet throughput and clock targets within resource budgets while retaining at least 15% measured resource headroom for final candidates, then maximize tokens per second; resource minimization is only a tie-breaker.",
  "target_continuation_policy": {
    "below_target_candidate_is_final": false,
    "completion_evidence": "Report estimated target attainment separately from source-bound Vivado resource feasibility and timing; unknown resource usage is not proof of fitting.",
    "on_candidate_universe_exhausted": "Request an architecture/design-space replan within the user's resource and implementation constraints; do not repeat exhausted candidates, invent QoR, or silently lower the target.",
    "on_estimated_target_miss": "Continue throughput-first DSE. A below-target candidate may be measured to calibrate the estimator, but is not the final target-achieving design.",
    "target_source": "qor_targets and discovered resource_budget"
  }
}
</dse_selection_evidence>

<formal_dse_campaign>
{
  "campaign_complete": false,
  "eligible_candidate_count": 360,
  "eligible_candidate_ids": [
    "arch_0149e4d15c31",
    "arch_01a712440a07",
    "arch_01f325b4e1de",
    "arch_021aa682ba93",
    "arch_0223bed1c6ae",
    "arch_02fc1bb8704f",
    "arch_030144f2a595",
    "arch_03deb8c155ac",
    "arch_03df93145328",
    "arch_0558926f0517",
    "arch_05db4846c145",
    "arch_06a09b56b3a3",
    "arch_07a4fc9326f5",
    "arch_07aaf64e3958",
    "arch_07afe4d1afe3",
    "arch_08fc81fe6157",
    "arch_0912b5c73a75",
    "arch_0a1c6c095ba9",
    "arch_0a8e4df9f2a4",
    "arch_0af261125bb6",
    "arch_0c4e9c9ee426",
    "arch_0c83d099727a",
    "arch_0d92d0324bd5",
    "arch_0dba4abc04da",
    "arch_0e61e297eab8",
    "arch_0ee3b53d937b",
    "arch_0f82293c93e6",
    "arch_0ff7933181b2",
    "arch_1004f24e4c78",
    "arch_113fb98e6716",
    "arch_1236fb4c9192",
    "arch_1275fee43ae3",
    "arch_14c45ee748de",
    "arch_14e2444c6f29",
    "arch_14e636757912",
    "arch_1543ffa00444",
    "arch_1551705cb52f",
    "arch_15e2da19c962",
    "arch_15fd90d23123",
    "arch_16d346427ca3",
    "arch_1725e6854544",
    "arch_17987b6fd806",
    "arch_18c3ad671667",
    "arch_191aee2a4fac",
    "arch_19ee50aca96c",
    "arch_1bc0ae048ecc",
    "arch_1df5ff65d4d1",
    "arch_1df97cb6ec78",
    "arch_1ee0cb7ccb51",
    "arch_1f5488585695",
    "arch_214151a145a5",
    "arch_216959e4bd8f",
    "arch_2248a7a4915f",
    "arch_2281df1ebe7d",
    "arch_22ecb49deb70",
    "arch_232bed4b6b9d",
    "arch_23588396a98c",
    "arch_2359fa11ef76",
    "arch_2384df47b271",
    "arch_23e424f3907d",
    "arch_2516758567f0",
    "arch_25d6722185e0",
    "arch_274773aefb3b",
    "arch_27ce70e6aaaf",
    "arch_28e04dc3fa70",
    "arch_2a08f2ba5074",
    "arch_2a8e7c89b216",
    "arch_2b980ec80526",
    "arch_2c74420434ff",
    "arch_2cc222a3f00a",
    "arch_2d260b75cf1f",
    "arch_2d99960b96e0",
    "arch_2dcaa331b416",
    "arch_2dfe4a965719",
    "arch_2e19e450930e",
    "arch_2e3fdce0b439",
    "arch_2ec11fd415c0",
    "arch_2ef0a2018ef7",
    "arch_2f5afaaec254",
    "arch_31920a847d25",
    "arch_31c1198760c0",
    "arch_32462ba2d356",
    "arch_32a1e7b3cb34",
    "arch_344e9f111ed9",
    "arch_344f207918df",
    "arch_352a9b7e4202",
    "arch_373d19512393",
    "arch_374daa9a0cdd",
    "arch_38d501cdd32a",
    "arch_390057f4b1e9",
    "arch_399f4d831e5c",
    "arch_39a3ab841a08",
    "arch_39d69c7b2fb1",
    "arch_3b944678649e",
    "arch_3c5fb574a252",
    "arch_3c7a03b2a050",
    "arch_3db46cf0a1ca",
    "arch_3eac00bab602",
    "arch_3fc57b48c731",
    "arch_3fd607bcea1a",
    "arch_3fd8f432a88e",
    "arch_3fedd13a9880",
    "arch_3ffa7b0ca613",
    "arch_402c4386596c",
    "arch_40873ed8c83f",
    "arch_411a4077eb6a",
    "arch_419e75b22818",
    "arch_441b25fd2df3",
    "arch_467de8375899",
    "arch_46e1e10a6121",
    "arch_46f2067d1b25",
    "arch_476a360808e2",
    "arch_478d1ff5fbf4",
    "arch_47c6bccd0f91",
    "arch_497eaf815b03",
    "arch_4cdc6a19fcb2",
    "arch_4d0cc8747989",
    "arch_4d7e0d132d62",
    "arch_4eec97b1af77",
    "arch_4f7bd0db6050",
    "arch_50255955605d",
    "arch_513408c9134d",
    "arch_513fc1a80269",
    "arch_514ae4f524cd",
    "arch_52a34a2c3820",
    "arch_52ec020a66d7",
    "arch_535aea705e57",
    "arch_5368ea328666",
    "arch_53d73e476ee6",
    "arch_55b127fde887",
    "arch_55fee5ee1b47",
    "arch_5667f0665e83",
    "arch_57fa072e2ebd",
    "arch_588c23978578",
    "arch_5929d2f7c953",
    "arch_596aed1675bc",
    "arch_5a1e3b388ff2",
    "arch_5b4f9ef48e3b",
    "arch_5ba6728b6afa",
    "arch_5c6aaa535af3",
    "arch_5ec69fef5431",
    "arch_5f9c6f50acd7",
    "arch_5fece9dbfb5d",
    "arch_6226a7032ff5",
    "arch_63524fbe4146",
    "arch_63e2712b0d8c",
    "arch_64407ee0f3cd",
    "arch_649b534fcc1a",
    "arch_64bb1aaa8652",
    "arch_65d82c71ed87",
    "arch_660928fbe87a",
    "arch_66eda2a340a7",
    "arch_67216be7c2c4",
    "arch_680b524a7904",
    "arch_6b39dd52fede",
    "arch_6b783b8c3b5f",
    "arch_6c628f49a37f",
    "arch_6cc920fe1bb9",
    "arch_6de61162217e",
    "arch_6e9d2e7c3ed7",
    "arch_6ec948a642ac",
    "arch_6f0b8aa2f9e4",
    "arch_6f3c42bcb893",
    "arch_6f43a9b1b56e",
    "arch_6ff30ee29bc5",
    "arch_72583f74eeea",
    "arch_72ed8d3d8fca",
    "arch_73abda6c79d2",
    "arch_74c0530f0375",
    "arch_74d3e6a2a3af",
    "arch_752b20bb417a",
    "arch_7532ebee1a9b",
    "arch_755a0908dcb3",
    "arch_765a51533fcc",
    "arch_79cde11b5c21",
    "arch_7a1e03668cf8",
    "arch_7a3bd5a9b8f9",
    "arch_7aafaeec6cf3",
    "arch_7ad3a71d15fd",
    "arch_7bc499eefaa6",
    "arch_7be2c5f02837",
    "arch_7c0c69b4f459",
    "arch_7ca75f5a86b5",
    "arch_7d79947fdb78",
    "arch_7f12b514ba45",
    "arch_7f4f2d7e7b00",
    "arch_8081df385844",
    "arch_80b56fe4d44c",
    "arch_8101410ebdb4",
    "arch_8142c1aced68",
    "arch_83048d4a5057",
    "arch_84e2c4578683",
    "arch_856dedaabba3",
    "arch_86495e0d541d",
    "arch_868ac68d2777",
    "arch_8adaa4a63a48",
    "arch_8be3bde33303",
    "arch_8c507b05ffa6",
    "arch_8c97f72ea796",
    "arch_8e30759b71e1",
    "arch_8e802f56d666",
    "arch_8fd69f3994a4",
    "arch_9027ce631c80",
    "arch_91e20cc0cc06",
    "arch_92d1e08d3b5f",
    "arch_932136faeec5",
    "arch_942e646d4227",
    "arch_9444ca76867d",
    "arch_95fae451adb1",
    "arch_96fba8eb2ada",
    "arch_97ccf13390dc",
    "arch_99a0aedcbbb9",
    "arch_9a8fc472e2ea",
    "arch_9b643156bb48",
    "arch_9b79d1dc3db6",
    "arch_9be0531db18b",
    "arch_9bfd9fae74d9",
    "arch_9d86a10c9f53",
    "arch_9e795d17f42b",
    "arch_9f14bfe18e8a",
    "arch_9f33a5404b5a",
    "arch_9f598ae21d30",
    "arch_9fc759222a6c",
    "arch_9fdebc4c6ae4",
    "arch_a0371897e326",
    "arch_a057ead0d15a",
    "arch_a081f1cbf8b1",
    "arch_a0df09fdc4db",
    "arch_a4977bb1a698",
    "arch_a50533321276",
    "arch_a517773d3161",
    "arch_a574b57f8746",
    "arch_a5eace0ee548",
    "arch_a6c169a2edf4",
    "arch_a6dcde4258a3",
    "arch_a8ff6d080f7c",
    "arch_a91a966a68f7",
    "arch_a9ff9c499567",
    "arch_aa4c4f23d6db",
    "arch_abde4590a458",
    "arch_acb89bb3ba15",
    "arch_ad8892b42ec7",
    "arch_add9aaf10354",
    "arch_ade162a46464",
    "arch_ae55c26ddf41",
    "arch_afa14018a13b",
    "arch_b0f0d30899e2",
    "arch_b16bdbc4109a",
    "arch_b32181bed209",
    "arch_b34fa72cbab4",
    "arch_b421ec47b151",
    "arch_b42aa377e2e0",
    "arch_b4e7c5328d8e",
    "arch_b55820969f9c",
    "arch_b60b5646b627",
    "arch_b6271d813970",
    "arch_b637f89f8261",
    "arch_b672c0c2ffc0",
    "arch_b8ca8cade8e5",
    "arch_b927f500990e",
    "arch_b940295488cd",
    "arch_b96e75fd8e2b",
    "arch_bab2720ae208",
    "arch_bb83e3a55f0f",
    "arch_bbbbb77d09c4",
    "arch_bc0c6c515826",
    "arch_bc14d0103c4e",
    "arch_bc22aab6622d",
    "arch_bc24575e6d42",
    "arch_bc476942ca25",
    "arch_bc620d11c1ef",
    "arch_bcdcb4b42daa",
    "arch_bd5de714ba6a",
    "arch_bdac1fb64848",
    "arch_bef81f548f0a",
    "arch_c0416de23a79",
    "arch_c20481167c03",
    "arch_c217cf021f09",
    "arch_c35fd286abd0",
    "arch_c4322375ee28",
    "arch_c49a6b045d55",
    "arch_c5b9b254f86f",
    "arch_c76dfda5addc",
    "arch_c77d8ca5d731",
    "arch_ca8fe55f2b35",
    "arch_cb076296c15d",
    "arch_cc49e34a1e9d",
    "arch_d0618c6ed407",
    "arch_d2c19e7ccba8",
    "arch_d2d4d29b5f07",
    "arch_d3ed18c90137",
    "arch_d4436dd1ea4d",
    "arch_d4daf9f9e284",
    "arch_d5f87b0baf38",
    "arch_d6aec71ce08d",
    "arch_d76fd2b6079a",
    "arch_d85783e09d4a",
    "arch_d8a8e84357ef",
    "arch_d8c022b644a5",
    "arch_d8e431a52f45",
    "arch_d989ceb26d47",
    "arch_da4e3559d223",
    "arch_da70f9eceb94",
    "arch_daa52f42cfa6",
    "arch_dc1be5f0d51e",
    "arch_dd8540454f55",
    "arch_ddfaa6496ede",
    "arch_def8999c6dfb",
    "arch_df4c44a5c331",
    "arch_df4cca5e7b2a",
    "arch_dfa88153518e",
    "arch_dff308387a82",
    "arch_e0787fb471a6",
    "arch_e1223c49e1b8",
    "arch_e13f55fbd87b",
    "arch_e19feb4aa56e",
    "arch_e1ae5e5ae265",
    "arch_e3182a853293",
    "arch_e3e8b5e047a3",
    "arch_e3efcea42753",
    "arch_e52da5f4c871",
    "arch_e5b8db7ec68b",
    "arch_e67fc21ebf2d",
    "arch_e705c02d85cd",
    "arch_e7f47a0f0412",
    "arch_e80a7ab05662",
    "arch_e80f615639cf",
    "arch_e8cda37195fb",
    "arch_e90c819732d8",
    "arch_ea3d55fb6e90",
    "arch_eacdf0e7ef55",
    "arch_eb27a97cda51",
    "arch_eb4d11e72448",
    "arch_ebc365d6e4b6",
    "arch_ecbbd59498c8",
    "arch_ed549ae85831",
    "arch_ef1b9c13c7a5",
    "arch_ef294b8d73ef",
    "arch_ef8819e2f9c6",
    "arch_f0efee9d4229",
    "arch_f1159b94e136",
    "arch_f28873ac2801",
    "arch_f37280b242a9",
    "arch_f3ad4379bb7e",
    "arch_f4aee385e8a1",
    "arch_f774510a24ae",
    "arch_f78411f21be4",
    "arch_f7c8ff2e2f66",
    "arch_f7ff22e0d43a",
    "arch_f8a08c194b06",
    "arch_fa013efa9c6a",
    "arch_fa34ea38a4e4",
    "arch_fa494f88fa0f",
    "arch_fa7e79479e46",
    "arch_faeea629eee9",
    "arch_fb85396f2ffc",
    "arch_fc2c7f03c066",
    "arch_fe027b778f3a",
    "arch_fe49b744d20a",
    "arch_fe61cdad7cf2"
  ],
  "measured_pareto_frontier": {
    "candidate_count": 0,
    "candidate_ids": []
  }
}
</formal_dse_campaign>

<dse_constraint_report>
{
  "candidate_count": 360,
  "candidate_materialization": {
    "candidate_count": 360,
    "errors": [],
    "generated_fields": {
      "activation_banks": "GeneratedDesignParams.activationBanks",
      "compute_array_cols": "GeneratedDesignParams.computeArrayCols",
      "compute_array_rows": "GeneratedDesignParams.computeArrayRows",
      "fifo_depth": "GeneratedDesignParams.fifoDepth",
      "lanes": "GeneratedDesignParams.lanes",
      "weight_banks_by_role": "GeneratedDesignParams.weightBanksByRole"
    },
    "physical_dimensions": [
      "lanes",
      "compute_array_rows",
      "compute_array_cols",
      "fifo_depth",
      "activation_banks",
      "weight_banks_by_role"
    ],
    "policy": "Every admitted DSE dimension must be materialized in GeneratedDesignParams and passed into the FPGA-IP/XPM configuration before exact app-shell QoR measurement.",
    "schema_version": "spatialaccagent.dse_candidate_materialization.v1",
    "status": "pass"
  },
  "feasible_candidate_count": 360,
  "hard_constraint_error_counts": {},
  "infeasible_candidate_count": 0,
  "policy": {
    "candidate_dimensions_must_reach_generated_fpga_ip": true,
    "candidate_universe_is_complete_and_unsampled": true,
    "deterministic_evaluator_enforces_hard_constraints": true,
    "final_candidate_resource_headroom_fraction": 0.85,
    "llm_selects_measurement_order_before_campaign_completion": true,
    "llm_selects_only_measured_pareto_candidates_after_campaign_completion": true,
    "only_same_scope_candidate_measurements_are_compared": true,
    "predicted_qor_is_not_measured_qor": true,
    "structural_estimates_rank_measurements_but_never_replace_tool_evidence": true,
    "synthesis_scope_contains_resources_estimated_clock_and_rtl_cycle_derived_throughput": true,
    "unknown_or_near_capacity_resource_usage_is_finally_eligible": false
  },
  "schema_version": "spatialaccagent.stage4_dse_constraint_report_projection.v1",
  "source_schema_version": "spatialaccagent.stage4_dse_constraint_report.v1",
  "status": "pass"
}
</dse_constraint_report>

<dse_constraint_report_path>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/dse_constraint_report.json
</dse_constraint_report_path>

<current_sacg_memory_truth>
{
  "active_contamination_barrier_count": 0,
  "active_contamination_barriers": [],
  "active_contamination_barriers_truncated": false,
  "open_backtrack_request_count": 0,
  "open_backtrack_requests": [],
  "open_backtrack_requests_truncated": false,
  "open_retry_request_count": 0,
  "open_retry_requests": [],
  "open_retry_requests_truncated": false,
  "policy": "Only active_contamination_barriers and open retry/backtrack requests in this object are current SACG-memory blockers. Historical, closed, superseded, or rejected records are recovery evidence only and must not be treated as active blockers.",
  "schema_version": "spatialaccagent.sacg_memory_truth.v0",
  "truth_source": "source_sacg_state.memory"
}
</current_sacg_memory_truth>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/pipeline_planning/sacg_state.json
</source_sacg_state>

<llm_policy>
{
  "api_key_configured": true,
  "configuration_error": "",
  "configured_model": "gpt-6.1-sol",
  "endpoint_configured": true,
  "enforce": true,
  "mode": "llm",
  "model": "deepseek-v4-pro",
  "model_selection_policy": "An explicit runtime model selection is authoritative and is recorded with the stage worker; it does not require a duplicate approval artifact.",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "medium",
  "requested_model_override": "deepseek-v4-pro",
  "schema_version": "spatialaccagent.llm_policy.v0"
}
</llm_policy>

<sacg_memory>
{
  "active_contamination_barriers": [],
  "open_backtrack_requests": [],
  "open_retry_requests": [],
  "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
  "recent_contamination_barriers": [],
  "recent_failure_lessons": [],
  "recent_stage_outcomes": [],
  "schema_version": "spatialaccagent.sacg_memory.v0"
}
</sacg_memory>

<sacg_memory_truth>
{
  "active_contamination_barrier_count": 0,
  "active_contamination_barriers": [],
  "active_contamination_barriers_truncated": false,
  "open_backtrack_request_count": 0,
  "open_backtrack_requests": [],
  "open_backtrack_requests_truncated": false,
  "open_retry_request_count": 0,
  "open_retry_requests": [],
  "open_retry_requests_truncated": false,
  "policy": "Only active_contamination_barriers and open retry/backtrack requests in this object are current SACG-memory blockers. Historical, closed, superseded, or rejected records are recovery evidence only and must not be treated as active blockers.",
  "schema_version": "spatialaccagent.sacg_memory_truth.v0",
  "truth_source": "source_sacg_state.memory"
}
</sacg_memory_truth>

<hierarchical_learning_context>
{
  "debug_layer": null,
  "decision_policy": {
    "current_scope_tools_and_exact_board_wrapper_remain_required": true,
    "do_not_repeat_certified_lower_layer_tools_or_prompt_analysis": true,
    "lower_layer_pass_does_not_claim_board_axi_ddr_or_backend_readiness": true,
    "lower_layer_reopen_requires_current_trace_named_contradiction": true,
    "resolved_artifact_identity_lessons_are_not_rtl_failures": true,
    "use_only_live_validated_lower_layer_evidence": true
  },
  "kernel_timing_knowledge": [],
  "resolved_evidence_lessons": [],
  "schema_version": "spatialaccagent.hierarchical_learning_context.v1",
  "status": "no_validated_lower_layer_evidence",
  "status_bar_contract": {
    "covers_only_live_validated_lower_layer_certificates": true,
    "does_not_replace_current_scope_tool_results": true,
    "maintainer": "framework_deterministic_hash_bound_projection",
    "not_an_llm_generated_history_summary": true,
    "raw_evidence_remains_retrievable_by_path_and_sha256": true
  },
  "validated_lower_layer_certificates": [],
  "verification_scope": null
}
</hierarchical_learning_context>

<action_grounding_registry>
{
  "acceptance_checkers": [
    "sacg_static_check",
    "task_card_check",
    "model_config_check",
    "numeric_policy_check",
    "template_coverage_check",
    "parameter_binding_static_check",
    "code_generation_manifest_static_check",
    "stream_plan_check",
    "memory_runtime_plan_check",
    "boundary_contract_check",
    "failure_localization_check",
    "targeted_replay_check",
    "connected_kernel_targeted_replay_check",
    "connected_kernel_cctg_contradiction_reconciliation_check",
    "causal_repair_context_check",
    "template_binding_static_check",
    "repair_boundary_check",
    "verification_plan_static_check",
    "tool_protocol_check",
    "human_boundary_check",
    "hierarchical_verification_plan_check",
    "verification_artifact_contract_check",
    "sacg_reference_check",
    "case_stage_leaf_static",
    "boundary_contract_check",
    "case_leaf_functional",
    "case_leaf_golden_compare",
    "case_single_transformer_layer",
    "case_single_layer_functional",
    "case_single_layer_golden_compare",
    "single_transformer_layer",
    "case_multilayer_pipeline",
    "case_multilayer_functional",
    "case_pipeline_deadlock_check",
    "case_real_weight_artifacts",
    "case_target_model_reference",
    "case_semantic_testbench",
    "case_operator_leaf_semantic_evidence",
    "case_single_layer_semantic_evidence",
    "case_board_semantic_evidence",
    "real_weight_semantic_evidence_check",
    "case_tb_scaffold",
    "case_board_interface_discovery",
    "case_axi_ddr_interface",
    "case_axi_protocol_check",
    "case_ddr_image_roundtrip",
    "case_runtime_abi_check",
    "case_runtime_bitstream",
    "board_runtime",
    "functional_sim",
    "deadlock_watchdog",
    "data_order_trace_check",
    "transfer_count_check",
    "addr_map_check",
    "numeric_compare",
    "artifact_hash_check",
    "codegen_compile_gate_check",
    "codegen_contract_check",
    "codegen_package_static_check",
    "verification_artifact_contract_check",
    "required_real_tool_evidence_check",
    "real_tool.case_real_weight_artifacts",
    "real_tool.boundary_contract_check",
    "real_tool.case_leaf_functional",
    "real_tool.case_leaf_golden_compare",
    "real_tool.case_tb_scaffold",
    "real_tool.case_single_transformer_layer",
    "real_tool.case_single_layer_functional",
    "real_tool.case_single_layer_golden_compare",
    "real_tool.case_multilayer_functional",
    "real_tool.case_pipeline_deadlock_check",
    "real_tool.case_vcs_functional_sim",
    "real_tool.case_verilator_functional_sim",
    "real_tool.case_deadlock_axi_check",
    "real_tool.case_board_interface_discovery",
    "real_tool.case_axi_ddr_interface",
    "real_tool.case_axi_protocol_check",
    "real_tool.case_ddr_image_roundtrip",
    "real_tool.case_vivado_synthesis",
    "real_tool.case_vivado_synthesis_report_check",
    "real_tool.case_vivado_implementation",
    "real_tool.case_vivado_implementation_report_check",
    "real_tool.case_board_shell_wrapper_generate",
    "real_tool.case_runtime_abi_check",
    "real_tool.case_runtime_bitstream",
    "real_tool.app_shell_target_discovery_contract",
    "real_tool.app_shell_target_hint_synthesis",
    "real_tool.app_shell_target_discovery_after_hint",
    "real_tool.board_runtime",
    "real_tool.app_shell_runtime_bitstream",
    "implementation_package_static",
    "timing_resource_check",
    "deployment_board_check",
    "output_validity_check",
    "targeted_failed_checker_rerun",
    "verification_action_audit_check",
    "llm_io_quality_check",
    "llm_semantic_extraction_check",
    "no_static_keyword_semantic_matching_check",
    "sacg_memory_check",
    "stage_retry_request_check",
    "stage_backtrack_request_check",
    "stage_artifact_trust_barrier_check",
    "backend_app_shell_integration_contract_static_check",
    "backend_app_shell_target_discovery_check",
    "backend_app_shell_target_hint_synthesis_check",
    "backend_bounded_recovery_action_check",
    "backend_recovery_approval_ingest",
    "backend_recovery_approval_ingest_check"
  ],
  "policy": "Executable actions should use these tool/checker names when applicable. A registered acceptance checker may also be requested as a validation operation in tool_roles. If a required capability is missing, name it as planned_tool.<short_name> and make the rationale say that multi-agent system capability implementation is required.",
  "schema_version": "spatialaccagent.action_grounding_registry.v0",
  "tool_roles": [
    "sacg_validate",
    "sacg_static_check",
    "task_card_check",
    "model_config_check",
    "numeric_policy_check",
    "template_coverage_check",
    "template_binding_static_check",
    "parameter_binding_static_check",
    "code_generation_manifest_static_check",
    "stream_plan_check",
    "memory_runtime_plan_check",
    "repair_boundary_check",
    "boundary_contract_generate",
    "failure_slice_localization",
    "boundary_trace_rerun",
    "targeted_replay",
    "connected_kernel_cctg_contradiction_targeted_replay",
    "connected_kernel_targeted_replay_check",
    "causal_repair_context_pack",
    "verification_plan_static_check",
    "tool_protocol_check",
    "human_boundary_check",
    "hierarchical_verification_plan_check",
    "verification_artifact_contract_check",
    "sacg_reference_check",
    "codegen_compile_gate",
    "codegen_contract_check",
    "codegen_package_static_check",
    "verification_artifact_contract_check",
    "required_real_tool_evidence_check",
    "real_tool_evidence_check",
    "case_real_weight_artifacts",
    "case_target_model_reference",
    "case_semantic_testbench",
    "case_operator_leaf_semantic_evidence",
    "case_single_layer_semantic_evidence",
    "case_board_semantic_evidence",
    "case_stage_leaf_static",
    "boundary_contract_check",
    "case_leaf_functional",
    "case_leaf_golden_compare",
    "case_single_transformer_layer",
    "case_single_layer_functional",
    "case_single_layer_golden_compare",
    "single_transformer_layer",
    "case_multilayer_pipeline",
    "case_multilayer_functional",
    "case_pipeline_deadlock_check",
    "case_tb_scaffold",
    "case_vcs_functional_sim",
    "functional_sim",
    "case_verilator_functional_sim",
    "case_weight_manifest_generate",
    "case_tb_scaffold_generate",
    "case_vcs_evidence_analyzer",
    "deadlock_watchdog",
    "data_order_trace_check",
    "transfer_count_check",
    "addr_map_check",
    "numeric_compare",
    "artifact_hash_check",
    "case_deadlock_axi_check",
    "case_board_interface_discovery",
    "case_axi_ddr_interface",
    "case_axi_protocol_check",
    "case_ddr_image_roundtrip",
    "case_vivado_synthesis",
    "case_vivado_synthesis_report_check",
    "case_vivado_implementation",
    "case_vivado_implementation_report_check",
    "case_board_shell_wrapper_generate",
    "case_runtime_abi_check",
    "case_runtime_bitstream",
    "case_compute_slot_adapter_generate",
    "app_shell_target_discovery_contract",
    "app_shell_target_hint_synthesis",
    "app_shell_target_discovery_after_hint",
    "backend_bounded_recovery_action",
    "backend_bounded_recovery",
    "backend_recovery_approval_ingest",
    "implementation_package_static",
    "timing_resource_check",
    "deployment_board_check",
    "board_runtime",
    "output_validity_check",
    "case_stage7_metrics",
    "targeted_failed_checker_rerun",
    "bounded_template_repair",
    "pipeline_repair",
    "memory_runtime_repair",
    "architecture_review",
    "team_aggregate",
    "verification_action_audit",
    "llm_io_quality_check",
    "llm_semantic_extraction",
    "no_static_keyword_semantic_matching",
    "sacg_memory_update",
    "sacg_memory_check",
    "stage_retry_request",
    "stage_backtrack_request",
    "stage_artifact_trust_barrier",
    "app_shell_runtime_bitstream"
  ],
  "verification_execution_policy": {
    "acceptance": "Real current-source VCS compilation, elaboration and linking; simulator execution and numerical comparison are not acceptance prerequisites.",
    "executor": "accagent/framework/stage_verification.py: compile_only_stage_gates and compile_only_required_gates_by_level select the existing layer tools in bottom-up order",
    "existing_tool_modes": {
      "case_leaf_functional": "scripts/verification/case_leaf_operator_verify.py: current-source VCS compile-only evidence for operator leaves",
      "case_single_layer_functional": "scripts/verification/case_single_layer_stream_sim.py: current-source VCS compile-only evidence for the connected kernel",
      "case_vcs_functional_sim": "scripts/verification/case_board_vcs_functional.py: compile-only VCS evidence for the exact discovered board wrapper; simulation is not invoked"
    },
    "planning_boundary": "Historical functional/golden DAG nodes describe optional diagnostic capabilities. Missing runtime/golden results and layer certificates are downstream execution obligations during verification_artifacts planning, not missing compile-only capabilities. Use existing tool roles; do not invent another compile-only runner merely because a role retains a functional_sim name.",
    "validation_policy": "vcs_compile_only"
  }
}
</action_grounding_registry>

<action_contract_examples>
[
  {
    "acceptance_checkers": [
      "case_real_weight_artifacts",
      "case_target_model_reference",
      "case_semantic_testbench"
    ],
    "action_type": "verification_evidence_preparation",
    "consumes": [
      "artifact.input.model_config",
      "artifact.input.numeric_policy",
      "artifact.stage3.pipeline_plan",
      "current case-adapter target checkpoint",
      "generated/memory/dut_weight_binding_manifest.json"
    ],
    "id": "example.prepare_real_model_semantic_verification",
    "on_failure": "treat missing reference, explicit tolerance, semantic harness, or DUT weight consumption as a verification-capability/code-generation blocker; do not run a legacy fallback test or promote the layer.",
    "produces": [
      "verification/real_weights/full_tensor_catalog.json",
      "verification/model_reference/reference_manifest.json",
      "verification/semantic_testbench/semantic_testbench_manifest.json",
      "verification/semantic_testbench/dut_weight_binding_requirements.json"
    ],
    "rationale": "Build immutable semantic evidence from the current case adapter before any hardware correctness claim.",
    "requires_approval": false,
    "stage": "verification",
    "tool_roles": [
      "case_weight_manifest_generate",
      "case_target_model_reference",
      "case_semantic_testbench"
    ]
  },
  {
    "acceptance_checkers": [
      "functional_sim",
      "data_order_trace_check",
      "deadlock_watchdog",
      "real_weight_semantic_evidence_check"
    ],
    "action_type": "real_tool_execution",
    "consumes": [
      "artifact.stage5.verification_artifact_contract",
      "verification/model_reference/reference_manifest.json",
      "verification/semantic_testbench/semantic_testbench_manifest.json",
      "generated/memory/dut_weight_binding_manifest.json",
      "verification/board_simulation/board_simulation_manifest.json"
    ],
    "id": "example.run_real_functional_sim",
    "on_failure": "route simulator evidence to the Stage-6 repair loop with the violated SACG constraints; do not proceed to Vivado.",
    "produces": [
      "verification/vcs/case_functional_sim.log",
      "verification/board_simulation/rtl_output.memh",
      "verification/debug_closure/boundary_trace.json",
      "verification/case_diagnostics/vcs_functional_diagnosis.json",
      "verification/semantic_evidence/board_axi_ddr.json"
    ],
    "rationale": "Run a real simulator after static hierarchy and artifact gates pass.",
    "requires_approval": false,
    "stage": "verification",
    "tool_roles": [
      "case_vcs_functional_sim",
      "case_vcs_evidence_analyzer",
      "case_board_semantic_evidence"
    ]
  },
  {
    "acceptance_checkers": [
      "planned_checker.formal_axi_property_check"
    ],
    "action_type": "system_capability_gap",
    "consumes": [
      "artifact.stage5.verification_plan"
    ],
    "id": "example.declare_missing_capability",
    "on_failure": "block promotion until the planned checker is implemented or an approved equivalent exists.",
    "produces": [
      "planned checker implementation task"
    ],
    "rationale": "The design team needs a checker not yet implemented by the multi-agent system.",
    "requires_approval": true,
    "stage": "verification",
    "tool_roles": [
      "planned_tool.formal_axi_property_runner"
    ]
  },
  {
    "acceptance_checkers": [
      "backend_app_shell_target_hint_synthesis_check",
      "backend_bounded_recovery_action_check",
      "human_boundary_check"
    ],
    "action_type": "bounded_recovery",
    "consumes": [
      "artifact.stage7.app_shell_integration_contract",
      "artifact.stage7.app_shell_target_selection_decision",
      "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json"
    ],
    "id": "example.ambiguous_backend_target_recovery",
    "on_failure": "keep runtime bitstream and board runtime blocked until the target contract has cited evidence or explicit approval",
    "produces": [
      "artifact.stage7.backend_bounded_recovery_actions"
    ],
    "rationale": "Real backend evidence produced multiple plausible shell integration targets, so the design team must not guess.",
    "requires_approval": true,
    "stage": "backend_board",
    "tool_roles": [
      "app_shell_target_hint_synthesis",
      "app_shell_target_discovery_after_hint"
    ]
  }
]
</action_contract_examples>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "agent": {
      "type": "string"
    },
    "approval_required_for": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "assumptions": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "executable_actions": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "acceptance_checkers": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "action_type": {
            "type": "string"
          },
          "consumes": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "id": {
            "type": "string"
          },
          "on_failure": {
            "type": "string"
          },
          "produces": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "rationale": {
            "type": "string"
          },
          "requires_approval": {
            "type": "boolean"
          },
          "stage": {
            "type": "string"
          },
          "targeted_replay_plan": {
            "additionalProperties": true,
            "type": "object"
          },
          "tool_roles": {
            "items": {
              "type": "string"
            },
            "type": "array"
          }
        },
        "required": [
          "id",
          "stage",
          "action_type",
          "rationale",
          "consumes",
          "produces",
          "tool_roles",
          "acceptance_checkers",
          "on_failure",
          "requires_approval"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "observations": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "proposed_actions": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "ranked_candidate_ids": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "risks": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "sacg_focus": {
      "additionalProperties": true,
      "properties": {
        "artifacts": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "constraints": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "edges": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "nodes": {
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "required": [
        "nodes",
        "edges",
        "constraints",
        "artifacts"
      ],
      "type": "object"
    },
    "schema_version": {
      "type": "string"
    },
    "selected_candidate_id": {
      "type": "string"
    },
    "selection_rationale": {
      "type": "string"
    },
    "stage": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "summary": {
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "agent",
    "stage",
    "status",
    "summary",
    "sacg_focus",
    "observations",
    "risks",
    "proposed_actions",
    "executable_actions",
    "approval_required_for",
    "selected_candidate_id",
    "ranked_candidate_ids",
    "selection_rationale",
    "assumptions"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
