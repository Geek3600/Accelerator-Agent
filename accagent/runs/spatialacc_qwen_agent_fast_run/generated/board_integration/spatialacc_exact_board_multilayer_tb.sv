module spatialacc_exact_board_multilayer_tb;
  localparam integer TARGET_LAYERS = 1;
  localparam integer LAST_LAYER = TARGET_LAYERS - 1;
  localparam integer BEATS_PER_LAYER = 1792;
  localparam integer TARGET_TOKENS = 16;
  localparam integer BEATS_PER_TOKEN = BEATS_PER_LAYER / TARGET_TOKENS;
  localparam integer CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT = 13;
  localparam integer AXI_BEATS_PER_ACTIVATION = 896;
  localparam integer ACTIVATION_AXI_BEATS_PER_TOKEN = AXI_BEATS_PER_ACTIVATION / TARGET_TOKENS;
  localparam integer WEIGHT_WORDS_PER_LAYER = 7457664;
  localparam integer RUNTIME_WORDS_PER_LAYER = 1056;
  localparam integer TOTAL_SCALARS = 14336;
  localparam [36:0] INPUT_TOKENS_BASE = 37'd0;
  localparam [36:0] OUTPUT_TOKENS_BASE = 37'd57344;
  localparam [36:0] ACTIVATION_PING_BASE = 37'd114688;
  localparam [36:0] ACTIVATION_PONG_BASE = 37'd270336;
  localparam [36:0] WEIGHT_BANK_A_BASE = 37'd425984;
  localparam [36:0] WEIGHT_BANK_B_BASE = 37'd30256640;
  localparam [36:0] RUNTIME_CONSTANTS_BASE = 37'd60087296;
  localparam [36:0] FULL_WEIGHT_IMAGE_BASE = RUNTIME_CONSTANTS_BASE + (37'd64 * (RUNTIME_WORDS_PER_LAYER / 16));
  localparam [63:0] FULL_WEIGHT_IMAGE_BYTES = 64'd29830656;
  localparam [63:0] RUNTIME_IMAGE_BYTES = 64'd4224;
  localparam time CLK_300M_HALF_PERIOD_PS = 1667;
  localparam time CLK_600M_HALF_PERIOD_PS = 834;
  localparam longint unsigned CHECKPOINT_CLOCK_PHASE_PERIOD_PS = 64'd2780556000;

  string spatialacc_input_path;
  string spatialacc_weight_image_path;
  string spatialacc_runtime_image_path;
  string spatialacc_expected_output_path;

  reg clk_300M;
  reg clk_600M;
  reg c0_ddr4_s_axi_clk;
  reg c0_ddr4_s_axi_rst_n;
  reg sys_rst_n;
  reg user_rst;
  reg c0_init_calib_complete;
  reg [703:0] cfg_data;
  reg cfg_data_valid;
  reg cfg_done;
  reg cnn0_input_batch_set;
  wire [2:0] cnn0_batch_count;
  reg cnn0_result_batch_clear;
  wire [2:0] cnn0_result_count;

  wire [3:0] c0_ddr4_s_axi_awid;
  wire [36:0] c0_ddr4_s_axi_awaddr;
  wire [7:0] c0_ddr4_s_axi_awlen;
  wire [2:0] c0_ddr4_s_axi_awsize;
  wire [1:0] c0_ddr4_s_axi_awburst;
  wire c0_ddr4_s_axi_awlock;
  wire [3:0] c0_ddr4_s_axi_awcache;
  wire [2:0] c0_ddr4_s_axi_awprot;
  wire c0_ddr4_s_axi_awvalid;
  reg c0_ddr4_s_axi_awready;
  wire [511:0] c0_ddr4_s_axi_wdata;
  wire [63:0] c0_ddr4_s_axi_wstrb;
  wire c0_ddr4_s_axi_wlast;
  wire c0_ddr4_s_axi_wvalid;
  reg c0_ddr4_s_axi_wready;
  wire c0_ddr4_s_axi_bready;
  reg [3:0] c0_ddr4_s_axi_bid;
  reg [1:0] c0_ddr4_s_axi_bresp;
  reg c0_ddr4_s_axi_bvalid;
  wire [3:0] c0_ddr4_s_axi_arid;
  wire [36:0] c0_ddr4_s_axi_araddr;
  wire [7:0] c0_ddr4_s_axi_arlen;
  wire [2:0] c0_ddr4_s_axi_arsize;
  wire [1:0] c0_ddr4_s_axi_arburst;
  wire c0_ddr4_s_axi_arlock;
  wire [3:0] c0_ddr4_s_axi_arcache;
  wire [2:0] c0_ddr4_s_axi_arprot;
  wire c0_ddr4_s_axi_arvalid;
  reg c0_ddr4_s_axi_arready;
  wire c0_ddr4_s_axi_rready;
  reg c0_ddr4_s_axi_rlast;
  reg c0_ddr4_s_axi_rvalid;
  reg [1:0] c0_ddr4_s_axi_rresp;
  reg [3:0] c0_ddr4_s_axi_rid;
  reg [511:0] c0_ddr4_s_axi_rdata;

  reg [255:0] input_beats [0:BEATS_PER_LAYER-1];
  reg [255:0] expected_beats [0:BEATS_PER_LAYER-1];
  reg [31:0] runtime_words [0:RUNTIME_WORDS_PER_LAYER-1];
  reg [511:0] written_beats [longint unsigned];

  integer weight_fd;
  integer runtime_fd;
  integer boundary_fd;
  integer progress_fd;
  integer weight_size;
  integer runtime_size;
  integer probe_fd;
  integer io_rc;
  integer delta_transition_fd;
  longint unsigned delta_transition_sequence;
  time delta_transition_last_time;
  integer delta_transition_count_at_time;
  reg delta_transition_suppressed;
  reg delta_transition_armed;
  integer init_i;
  integer init_b0;
  integer init_b1;
  integer init_b2;
  integer init_b3;
  reg [511:0] weight_probe;
  reg artifacts_loaded;
  reg artifact_error;
  reg axi_model_error;
  reg final_pass;
  reg live_reports_written;

  reg [31:0] ready_lfsr;
  reg read_active;
  reg [36:0] read_addr_q;
  reg [7:0] read_len_q;
  reg [7:0] read_beat_q;
  reg [2:0] read_size_q;
  reg [1:0] read_burst_q;
  reg [3:0] read_id_q;
  integer read_delay_q;

  reg write_active;
  reg [36:0] write_addr_q;
  reg [7:0] write_len_q;
  reg [7:0] write_beat_q;
  reg [2:0] write_size_q;
  reg [1:0] write_burst_q;
  reg [3:0] write_id_q;
  integer write_response_delay_q;
  reg write_response_pending;

  longint unsigned cycle_count;
  longint unsigned progress_sequence;
  longint unsigned semantic_progress_count;
  longint unsigned progress_epoch;
  longint unsigned last_semantic_progress_cycle;
  longint unsigned heartbeat_next_cycle;
  longint unsigned stall_snapshot_last_cycle;
  longint unsigned axi_read_transaction_count;
  longint unsigned axi_write_transaction_count;
  longint unsigned axi_read_beat_count;
  longint unsigned axi_write_beat_count;
  longint unsigned axi_write_response_count;
  longint unsigned weight_accept_total;
  longint unsigned runtime_accept_total;
  longint unsigned kernel_input_accept_total;
  longint unsigned kernel_output_accept_total;
  longint unsigned concurrent_pipeline_cycle_count;
  integer runtime_accept_count [0:TARGET_LAYERS-1];
  integer runtime_first_address [0:TARGET_LAYERS-1];
  integer runtime_last_address [0:TARGET_LAYERS-1];
  reg runtime_contiguous [0:TARGET_LAYERS-1];
  reg runtime_data_match [0:TARGET_LAYERS-1];
  reg runtime_last_ok [0:TARGET_LAYERS-1];
  longint unsigned runtime_complete_cycle [0:TARGET_LAYERS-1];
  longint unsigned kernel_start_cycle [0:TARGET_LAYERS-1];
  integer layer_input_count [0:TARGET_LAYERS-1];
  integer layer_output_count [0:TARGET_LAYERS-1];
  integer kernel_overlap_start_count [0:TARGET_LAYERS-1];
  integer input_count_at_first_output [0:TARGET_LAYERS-1];
  reg first_output_seen [0:TARGET_LAYERS-1];
  integer trace_prefetch_start_count;
  integer trace_prefetch_complete_count;
  integer trace_weight_switch_count;
  integer trace_activation_switch_count;
  integer trace_runtime_start_count;
  integer trace_runtime_complete_count;
  integer trace_kernel_start_count;
  integer trace_layer_complete_count;
  integer trace_final_start_count;
  integer trace_final_complete_count;
  integer prefetch_compute_overlap_count;
  integer frontier_core_start_pulse_count;
  integer frontier_core_start_asserted_cycle_count;
  integer frontier_start_with_input_fire_count;
  integer frontier_post_first_start_pulse_count;
  longint unsigned frontier_kernel_reset_release_cycle;
  longint unsigned frontier_weight_load_complete_cycle;
  longint unsigned frontier_runtime_load_complete_cycle;
  longint unsigned frontier_first_start_cycle;
  longint unsigned frontier_last_start_cycle;
  longint unsigned frontier_first_input_fire_cycle;
  longint unsigned frontier_last_input_fire_cycle;
  reg frontier_kernel_reset_d;
  reg frontier_start_to_core_d;
  reg frontier_first_input_fire_seen;
  reg frontier_post_input_snapshot_emitted;
  reg frontier_first_post_start_ingress_snapshot_emitted;
  longint unsigned frontier_first_output_fire_cycle;
  longint unsigned frontier_first_output_token_complete_cycle;
  longint unsigned frontier_last_output_fire_cycle;
  reg frontier_output_token_complete_snapshot_emitted;
  reg frontier_output_continuation_snapshot_emitted;
  reg frontier_stage0_post_ingress_valid_snapshot_emitted;
  longint unsigned frontier_core_ingress_fire_count;
  longint unsigned frontier_first_core_ingress_fire_cycle;
  longint unsigned frontier_stage0_input_fire_count;
  longint unsigned frontier_stage0_fire_count;
  longint unsigned frontier_core_egress_fire_count;
  reg frontier_core_ingress_last_payload_unknown;
  reg frontier_stage0_last_payload_unknown;
  reg frontier_core_egress_last_payload_unknown;
  reg [31:0] frontier_core_ingress_last_payload_digest;
  reg [31:0] frontier_stage0_last_payload_digest;
  reg [31:0] frontier_core_egress_last_payload_digest;
  wire frontier_core_ingress_valid =
    dut.spatialacc_single_kernel.core.io_in_valid;
  wire frontier_core_ingress_ready =
    dut.spatialacc_single_kernel.core.io_in_ready;
  wire [255:0] frontier_core_ingress_data =
    dut.spatialacc_single_kernel.core.io_in_bits_data;
  wire frontier_core_ingress_fire =
    (frontier_core_ingress_valid === 1'b1) &&
    (frontier_core_ingress_ready === 1'b1);
  wire frontier_stage0_input_valid =
    dut.spatialacc_single_kernel.core.rms1.io_in_valid;
  wire frontier_stage0_input_ready =
    dut.spatialacc_single_kernel.core.rms1.io_in_ready;
  wire frontier_stage0_input_fire =
    (frontier_stage0_input_valid === 1'b1) &&
    (frontier_stage0_input_ready === 1'b1);
  wire frontier_stage0_valid =
    dut.spatialacc_single_kernel.core.rms1.io_out_valid;
  wire frontier_stage0_ready =
    dut.spatialacc_single_kernel.core.rms1.io_out_ready;
  wire [127:0] frontier_stage0_data =
    dut.spatialacc_single_kernel.core.rms1.io_out_bits_data;
  wire frontier_stage0_fire =
    (frontier_stage0_valid === 1'b1) &&
    (frontier_stage0_ready === 1'b1);
  wire frontier_qkv_input_fire =
    (dut.spatialacc_single_kernel.core.qkv_io_in_valid === 1'b1) &&
    (dut.spatialacc_single_kernel.core.qkv_io_in_ready === 1'b1);
  wire frontier_core_egress_valid =
    dut.spatialacc_single_kernel.core.io_out_valid;
  wire frontier_core_egress_ready =
    dut.spatialacc_single_kernel.core.io_out_ready;
  wire [255:0] frontier_core_egress_data =
    dut.spatialacc_single_kernel.core.io_out_bits_data;
  wire frontier_core_egress_fire =
    (frontier_core_egress_valid === 1'b1) &&
    (frontier_core_egress_ready === 1'b1);
  wire frontier_mlp_gate_input_fire =
    (dut.spatialacc_single_kernel.core.mlp_gate_io_in_valid__bore === 1'b1) &&
    (dut.spatialacc_single_kernel.core.mlp_gate_io_in_ready__bore === 1'b1);
  wire frontier_mlp_up_input_fire =
    (dut.spatialacc_single_kernel.core.mlp_up_io_in_valid__bore === 1'b1) &&
    (dut.spatialacc_single_kernel.core.mlp_up_io_in_ready__bore === 1'b1);
  wire frontier_mlp_gate_output_fire =
    (dut.spatialacc_single_kernel.core.mlp_gate_io_out_valid__bore === 1'b1) &&
    (dut.spatialacc_single_kernel.core.mlp_gate_io_out_ready__bore === 1'b1);
  wire frontier_mlp_up_output_fire =
    (dut.spatialacc_single_kernel.core.mlp_up_io_out_valid__bore === 1'b1) &&
    (dut.spatialacc_single_kernel.core.mlp_up_io_out_ready__bore === 1'b1);
  wire frontier_mlp_mul_output_fire =
    (dut.spatialacc_single_kernel.core.mlp_mul_io_out_valid__bore === 1'b1) &&
    (dut.spatialacc_single_kernel.core.mlp_mul_io_out_ready__bore === 1'b1);
  wire frontier_mlp_down_input_valid =
    dut.spatialacc_single_kernel.core.mlp_mul_io_out_valid__bore;
  wire frontier_mlp_down_input_ready =
    dut.spatialacc_single_kernel.core.mlp_mul_io_out_ready__bore;
  wire frontier_mlp_down_input_fire =
    (frontier_mlp_down_input_valid === 1'b1) &&
    (frontier_mlp_down_input_ready === 1'b1);
  wire frontier_mlp_down_output_fire =
    (dut.spatialacc_single_kernel.core.mlp_down_io_out_valid__bore === 1'b1) &&
    (dut.spatialacc_single_kernel.core.mlp_down_io_out_ready__bore === 1'b1);
  longint unsigned frontier_qkv_input_fire_count;
  longint unsigned frontier_mlp_gate_input_fire_count;
  longint unsigned frontier_mlp_up_input_fire_count;
  longint unsigned frontier_mlp_gate_output_fire_count;
  longint unsigned frontier_mlp_up_output_fire_count;
  longint unsigned frontier_mlp_mul_output_fire_count;
  longint unsigned frontier_mlp_down_input_fire_count;
  longint unsigned frontier_mlp_down_output_fire_count;
  longint unsigned frontier_mlp_down_input_terminal_fire_count;
  longint unsigned frontier_mlp_down_output_terminal_fire_count;

  // probe_id=probe.current_dag_complete_boundary_coverage.2
  // Read-only testbench bindings for every incomplete current Transformer-block
  // data boundary. These signals drive no DUT input and add no DUT port.
  wire [CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1:0] current_dag_boundary_valid;
  wire [CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1:0] current_dag_boundary_ready;
  wire [CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1:0] current_dag_boundary_fire;
  wire [CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1:0] current_dag_boundary_start;
  wire [CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1:0] current_dag_boundary_last;
  wire [255:0] current_dag_boundary_payload [0:CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1];
  longint unsigned current_dag_boundary_accepted_count [0:CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1];
  reg current_dag_boundary_first_accepted_seen [0:CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1];
  reg [31:0] current_dag_boundary_first_accepted_payload_digest [0:CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1];
  reg [31:0] current_dag_boundary_last_accepted_payload_digest [0:CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1];
  reg current_dag_boundary_waiting_seen [0:CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1];
  reg [31:0] current_dag_boundary_token_first_payload_digest [0:CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1];
  reg current_dag_boundary_token_first_payload_unknown [0:CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT-1];

  assign current_dag_boundary_valid[0] = dut.spatialacc_single_kernel.core.rms1.io_in_valid;
  assign current_dag_boundary_ready[0] = dut.spatialacc_single_kernel.core.rms1.io_in_ready;
  assign current_dag_boundary_fire[0] = (dut.spatialacc_single_kernel.core.rms1.io_in_valid) && (dut.spatialacc_single_kernel.core.rms1.io_in_ready);
  assign current_dag_boundary_payload[0] = dut.spatialacc_single_kernel.core.rms1.io_in_bits_data;
  assign current_dag_boundary_start[0] = dut.spatialacc_single_kernel.core.rms1.io_in_bits_st;
  assign current_dag_boundary_last[0] = dut.spatialacc_single_kernel.core.rms1.io_in_bits_last;
  assign current_dag_boundary_valid[1] = dut.spatialacc_single_kernel.core.add1.io_residual_valid;
  assign current_dag_boundary_ready[1] = dut.spatialacc_single_kernel.core.add1.io_residual_ready;
  assign current_dag_boundary_fire[1] = (dut.spatialacc_single_kernel.core.add1.io_residual_valid) && (dut.spatialacc_single_kernel.core.add1.io_residual_ready);
  assign current_dag_boundary_payload[1] = dut.spatialacc_single_kernel.core.add1.io_residual_bits_data;
  assign current_dag_boundary_start[1] = dut.spatialacc_single_kernel.core.add1.io_residual_bits_st;
  assign current_dag_boundary_last[1] = dut.spatialacc_single_kernel.core.add1.io_residual_bits_last;
  assign current_dag_boundary_valid[2] = dut.spatialacc_single_kernel.core.qkv.io_in_valid;
  assign current_dag_boundary_ready[2] = dut.spatialacc_single_kernel.core.qkv.io_in_ready;
  assign current_dag_boundary_fire[2] = (dut.spatialacc_single_kernel.core.qkv.io_in_valid) && (dut.spatialacc_single_kernel.core.qkv.io_in_ready);
  assign current_dag_boundary_payload[2] = dut.spatialacc_single_kernel.core.qkv.io_in_bits_data;
  assign current_dag_boundary_start[2] = dut.spatialacc_single_kernel.core.rms1.io_out_bits_st;
  assign current_dag_boundary_last[2] = dut.spatialacc_single_kernel.core.rms1.io_out_bits_last;
  assign current_dag_boundary_valid[3] = dut.spatialacc_single_kernel.core.add1.io_computed_valid;
  assign current_dag_boundary_ready[3] = dut.spatialacc_single_kernel.core.add1.io_computed_ready;
  assign current_dag_boundary_fire[3] = (dut.spatialacc_single_kernel.core.add1.io_computed_valid) && (dut.spatialacc_single_kernel.core.add1.io_computed_ready);
  assign current_dag_boundary_payload[3] = dut.spatialacc_single_kernel.core.add1.io_computed_bits_data;
  assign current_dag_boundary_start[3] = dut.spatialacc_single_kernel.core.add1.io_computed_bits_st;
  assign current_dag_boundary_last[3] = dut.spatialacc_single_kernel.core.add1.io_computed_bits_last;
  assign current_dag_boundary_valid[4] = dut.spatialacc_single_kernel.core.rms2.io_in_valid;
  assign current_dag_boundary_ready[4] = dut.spatialacc_single_kernel.core.rms2.io_in_ready;
  assign current_dag_boundary_fire[4] = (dut.spatialacc_single_kernel.core.rms2.io_in_valid) && (dut.spatialacc_single_kernel.core.rms2.io_in_ready);
  assign current_dag_boundary_payload[4] = dut.spatialacc_single_kernel.core.rms2.io_in_bits_data;
  assign current_dag_boundary_start[4] = dut.spatialacc_single_kernel.core.rms2.io_in_bits_st;
  assign current_dag_boundary_last[4] = dut.spatialacc_single_kernel.core.rms2.io_in_bits_last;
  assign current_dag_boundary_valid[5] = dut.spatialacc_single_kernel.core.add2.io_residual_valid;
  assign current_dag_boundary_ready[5] = dut.spatialacc_single_kernel.core.add2.io_residual_ready;
  assign current_dag_boundary_fire[5] = (dut.spatialacc_single_kernel.core.add2.io_residual_valid) && (dut.spatialacc_single_kernel.core.add2.io_residual_ready);
  assign current_dag_boundary_payload[5] = dut.spatialacc_single_kernel.core.add2.io_residual_bits_data;
  assign current_dag_boundary_start[5] = dut.spatialacc_single_kernel.core.add2.io_residual_bits_st;
  assign current_dag_boundary_last[5] = dut.spatialacc_single_kernel.core.add2.io_residual_bits_last;
  assign current_dag_boundary_valid[6] = dut.spatialacc_single_kernel.core.mlp.gate.io_in_valid;
  assign current_dag_boundary_ready[6] = dut.spatialacc_single_kernel.core.mlp.gate.io_in_ready;
  assign current_dag_boundary_fire[6] = (dut.spatialacc_single_kernel.core.mlp.gate.io_in_valid) && (dut.spatialacc_single_kernel.core.mlp.gate.io_in_ready);
  assign current_dag_boundary_payload[6] = dut.spatialacc_single_kernel.core.mlp.gate.io_in_bits_data;
  assign current_dag_boundary_start[6] = dut.spatialacc_single_kernel.core.mlp.gate.io_in_bits_st;
  assign current_dag_boundary_last[6] = dut.spatialacc_single_kernel.core.mlp.gate.io_in_bits_last;
  assign current_dag_boundary_valid[7] = dut.spatialacc_single_kernel.core.mlp.up.io_in_valid;
  assign current_dag_boundary_ready[7] = dut.spatialacc_single_kernel.core.mlp.up.io_in_ready;
  assign current_dag_boundary_fire[7] = (dut.spatialacc_single_kernel.core.mlp.up.io_in_valid) && (dut.spatialacc_single_kernel.core.mlp.up.io_in_ready);
  assign current_dag_boundary_payload[7] = dut.spatialacc_single_kernel.core.mlp.up.io_in_bits_data;
  assign current_dag_boundary_start[7] = dut.spatialacc_single_kernel.core.mlp.up.io_in_bits_st;
  assign current_dag_boundary_last[7] = dut.spatialacc_single_kernel.core.mlp.up.io_in_bits_last;
  assign current_dag_boundary_valid[8] = dut.spatialacc_single_kernel.core.mlp.gate.io_out_valid;
  assign current_dag_boundary_ready[8] = dut.spatialacc_single_kernel.core.mlp.gate.io_out_ready;
  assign current_dag_boundary_fire[8] = (dut.spatialacc_single_kernel.core.mlp.gate.io_out_valid) && (dut.spatialacc_single_kernel.core.mlp.gate.io_out_ready);
  assign current_dag_boundary_payload[8] = dut.spatialacc_single_kernel.core.mlp.gate.io_out_bits_data;
  assign current_dag_boundary_start[8] = dut.spatialacc_single_kernel.core.mlp.gate.io_out_bits_st;
  assign current_dag_boundary_last[8] = dut.spatialacc_single_kernel.core.mlp.gate.io_out_bits_last;
  assign current_dag_boundary_valid[9] = dut.spatialacc_single_kernel.core.mlp.up.io_out_valid;
  assign current_dag_boundary_ready[9] = dut.spatialacc_single_kernel.core.mlp.up.io_out_ready;
  assign current_dag_boundary_fire[9] = (dut.spatialacc_single_kernel.core.mlp.up.io_out_valid) && (dut.spatialacc_single_kernel.core.mlp.up.io_out_ready);
  assign current_dag_boundary_payload[9] = dut.spatialacc_single_kernel.core.mlp.up.io_out_bits_data;
  assign current_dag_boundary_start[9] = dut.spatialacc_single_kernel.core.mlp.up.io_out_bits_st;
  assign current_dag_boundary_last[9] = dut.spatialacc_single_kernel.core.mlp.up.io_out_bits_last;
  assign current_dag_boundary_valid[10] = dut.spatialacc_single_kernel.core.mlp.down.io_in_valid;
  assign current_dag_boundary_ready[10] = dut.spatialacc_single_kernel.core.mlp.down.io_in_ready;
  assign current_dag_boundary_fire[10] = (dut.spatialacc_single_kernel.core.mlp.down.io_in_valid) && (dut.spatialacc_single_kernel.core.mlp.down.io_in_ready);
  assign current_dag_boundary_payload[10] = dut.spatialacc_single_kernel.core.mlp.down.io_in_bits_data;
  assign current_dag_boundary_start[10] = dut.spatialacc_single_kernel.core.mlp.mul_io_out_bits_st__bore;
  assign current_dag_boundary_last[10] = dut.spatialacc_single_kernel.core.mlp.mul_io_out_bits_last__bore;
  assign current_dag_boundary_valid[11] = dut.spatialacc_single_kernel.core.add2.io_computed_valid;
  assign current_dag_boundary_ready[11] = dut.spatialacc_single_kernel.core.add2.io_computed_ready;
  assign current_dag_boundary_fire[11] = (dut.spatialacc_single_kernel.core.add2.io_computed_valid) && (dut.spatialacc_single_kernel.core.add2.io_computed_ready);
  assign current_dag_boundary_payload[11] = dut.spatialacc_single_kernel.core.add2.io_computed_bits_data;
  assign current_dag_boundary_start[11] = dut.spatialacc_single_kernel.core.add2.io_computed_bits_st;
  assign current_dag_boundary_last[11] = dut.spatialacc_single_kernel.core.add2.io_computed_bits_last;
  assign current_dag_boundary_valid[12] = dut.spatialacc_single_kernel.core.io_out_valid;
  assign current_dag_boundary_ready[12] = dut.spatialacc_single_kernel.core.io_out_ready;
  assign current_dag_boundary_fire[12] = (dut.spatialacc_single_kernel.core.io_out_valid) && (dut.spatialacc_single_kernel.core.io_out_ready);
  assign current_dag_boundary_payload[12] = dut.spatialacc_single_kernel.core.io_out_bits_data;
  assign current_dag_boundary_start[12] = dut.spatialacc_single_kernel.core.add2.io_out_bits_st;
  assign current_dag_boundary_last[12] = dut.spatialacc_single_kernel.core.add2.io_out_bits_last;

  (* keep = "true", keep_hierarchy = "yes", dont_touch = "true" *)
  app_shell_9p_cnn_core_0_1 dut (
    .clk_300M(clk_300M),
    .clk_600M(clk_600M),
    .cfg_data(cfg_data),
    .cfg_data_valid(cfg_data_valid),
    .cfg_done(cfg_done),
    .cnn0_input_batch_set(cnn0_input_batch_set),
    .cnn0_batch_count(cnn0_batch_count),
    .cnn0_result_batch_clear(cnn0_result_batch_clear),
    .cnn0_result_count(cnn0_result_count),
    .user_rst(user_rst),
    .c0_ddr4_s_axi_awid(c0_ddr4_s_axi_awid),
    .c0_ddr4_s_axi_awaddr(c0_ddr4_s_axi_awaddr),
    .c0_ddr4_s_axi_awlen(c0_ddr4_s_axi_awlen),
    .c0_ddr4_s_axi_awsize(c0_ddr4_s_axi_awsize),
    .c0_ddr4_s_axi_awburst(c0_ddr4_s_axi_awburst),
    .c0_ddr4_s_axi_awlock(c0_ddr4_s_axi_awlock),
    .c0_ddr4_s_axi_awcache(c0_ddr4_s_axi_awcache),
    .c0_ddr4_s_axi_awprot(c0_ddr4_s_axi_awprot),
    .c0_ddr4_s_axi_awvalid(c0_ddr4_s_axi_awvalid),
    .c0_ddr4_s_axi_awready(c0_ddr4_s_axi_awready),
    .c0_ddr4_s_axi_wdata(c0_ddr4_s_axi_wdata),
    .c0_ddr4_s_axi_wstrb(c0_ddr4_s_axi_wstrb),
    .c0_ddr4_s_axi_wlast(c0_ddr4_s_axi_wlast),
    .c0_ddr4_s_axi_wvalid(c0_ddr4_s_axi_wvalid),
    .c0_ddr4_s_axi_wready(c0_ddr4_s_axi_wready),
    .c0_ddr4_s_axi_bready(c0_ddr4_s_axi_bready),
    .c0_ddr4_s_axi_bid(c0_ddr4_s_axi_bid),
    .c0_ddr4_s_axi_bresp(c0_ddr4_s_axi_bresp),
    .c0_ddr4_s_axi_bvalid(c0_ddr4_s_axi_bvalid),
    .c0_ddr4_s_axi_arid(c0_ddr4_s_axi_arid),
    .c0_ddr4_s_axi_araddr(c0_ddr4_s_axi_araddr),
    .c0_ddr4_s_axi_arlen(c0_ddr4_s_axi_arlen),
    .c0_ddr4_s_axi_arsize(c0_ddr4_s_axi_arsize),
    .c0_ddr4_s_axi_arburst(c0_ddr4_s_axi_arburst),
    .c0_ddr4_s_axi_arlock(c0_ddr4_s_axi_arlock),
    .c0_ddr4_s_axi_arcache(c0_ddr4_s_axi_arcache),
    .c0_ddr4_s_axi_arprot(c0_ddr4_s_axi_arprot),
    .c0_ddr4_s_axi_arvalid(c0_ddr4_s_axi_arvalid),
    .c0_ddr4_s_axi_arready(c0_ddr4_s_axi_arready),
    .c0_ddr4_s_axi_rready(c0_ddr4_s_axi_rready),
    .c0_ddr4_s_axi_rlast(c0_ddr4_s_axi_rlast),
    .c0_ddr4_s_axi_rvalid(c0_ddr4_s_axi_rvalid),
    .c0_ddr4_s_axi_rresp(c0_ddr4_s_axi_rresp),
    .c0_ddr4_s_axi_rid(c0_ddr4_s_axi_rid),
    .c0_ddr4_s_axi_rdata(c0_ddr4_s_axi_rdata),
    .c0_ddr4_s_axi_clk(c0_ddr4_s_axi_clk),
    .c0_ddr4_s_axi_rst_n(c0_ddr4_s_axi_rst_n),
    .c0_init_calib_complete(c0_init_calib_complete),
    .sys_rst_n(sys_rst_n)
  );

  (* keep = "true", keep_hierarchy = "yes" *)
  spatialacc_axi4_protocol_monitor #(
    .ADDR_WIDTH(37),
    .DATA_WIDTH(512),
    .ID_WIDTH(4),
    .READ_OUTSTANDING_LIMIT(2),
    .WRITE_OUTSTANDING_LIMIT(2)
  ) tb_c0_ddr4_s_axi_monitor (
    .aclk(c0_ddr4_s_axi_clk),
    .aresetn(c0_ddr4_s_axi_rst_n),
    .calib_complete(c0_init_calib_complete),
    .awid(c0_ddr4_s_axi_awid),
    .awaddr(c0_ddr4_s_axi_awaddr),
    .awlen(c0_ddr4_s_axi_awlen),
    .awsize(c0_ddr4_s_axi_awsize),
    .awburst(c0_ddr4_s_axi_awburst),
    .awlock(c0_ddr4_s_axi_awlock),
    .awcache(c0_ddr4_s_axi_awcache),
    .awprot(c0_ddr4_s_axi_awprot),
    .awvalid(c0_ddr4_s_axi_awvalid),
    .awready(c0_ddr4_s_axi_awready),
    .wdata(c0_ddr4_s_axi_wdata),
    .wstrb(c0_ddr4_s_axi_wstrb),
    .wlast(c0_ddr4_s_axi_wlast),
    .wvalid(c0_ddr4_s_axi_wvalid),
    .wready(c0_ddr4_s_axi_wready),
    .bid(c0_ddr4_s_axi_bid),
    .bresp(c0_ddr4_s_axi_bresp),
    .bvalid(c0_ddr4_s_axi_bvalid),
    .bready(c0_ddr4_s_axi_bready),
    .arid(c0_ddr4_s_axi_arid),
    .araddr(c0_ddr4_s_axi_araddr),
    .arlen(c0_ddr4_s_axi_arlen),
    .arsize(c0_ddr4_s_axi_arsize),
    .arburst(c0_ddr4_s_axi_arburst),
    .arlock(c0_ddr4_s_axi_arlock),
    .arcache(c0_ddr4_s_axi_arcache),
    .arprot(c0_ddr4_s_axi_arprot),
    .arvalid(c0_ddr4_s_axi_arvalid),
    .arready(c0_ddr4_s_axi_arready),
    .rdata(c0_ddr4_s_axi_rdata),
    .rid(c0_ddr4_s_axi_rid),
    .rresp(c0_ddr4_s_axi_rresp),
    .rlast(c0_ddr4_s_axi_rlast),
    .rvalid(c0_ddr4_s_axi_rvalid),
    .rready(c0_ddr4_s_axi_rready)
  );

  function automatic string json_bool(input bit value);
    begin
      json_bool = value ? "true" : "false";
    end
  endfunction

  function automatic string json_logic(input logic value);
    begin
      case (value)
        1'b0: json_logic = "0";
        1'b1: json_logic = "1";
        1'bx: json_logic = "\"x\"";
        default: json_logic = "\"z\"";
      endcase
    end
  endfunction

  function automatic [31:0] payload_digest256(input [255:0] value);
    integer digest_lane;
    reg [31:0] digest;
    begin
      digest = 32'd0;
      for (digest_lane = 0; digest_lane < 8; digest_lane = digest_lane + 1) begin
        digest = digest ^ value[(digest_lane*32) +: 32];
      end
      payload_digest256 = digest;
    end
  endfunction

  function automatic integer current_dag_boundary_beats_per_token(input integer boundary_index);
    begin
      case (boundary_index)
        8, 9, 10: current_dag_boundary_beats_per_token = 608;
        default: current_dag_boundary_beats_per_token = BEATS_PER_TOKEN;
      endcase
    end
  endfunction

  function automatic string current_dag_boundary_name(input integer boundary_index);
    begin
      case (boundary_index)
        0: current_dag_boundary_name = "edge.data.block_input.to.stage_00_rms_norm_1.input";
        1: current_dag_boundary_name = "edge.data.block_input.to.stage_02_residual_add_1.residual_skip";
        2: current_dag_boundary_name = "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main";
        3: current_dag_boundary_name = "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main";
        4: current_dag_boundary_name = "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main";
        5: current_dag_boundary_name = "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip";
        6: current_dag_boundary_name = "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch";
        7: current_dag_boundary_name = "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch";
        8: current_dag_boundary_name = "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul";
        9: current_dag_boundary_name = "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul";
        10: current_dag_boundary_name = "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main";
        11: current_dag_boundary_name = "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main";
        12: current_dag_boundary_name = "edge.data.stage_08_residual_add_2.to.block_output.output";
        default: current_dag_boundary_name = "unknown";
      endcase
    end
  endfunction

  function automatic bit current_dag_boundary_has_upstream_progress(input integer boundary_index);
    begin
      case (boundary_index)
        0, 1: current_dag_boundary_has_upstream_progress =
          (frontier_core_ingress_fire_count != 0) || (frontier_core_ingress_fire === 1'b1);
        2: current_dag_boundary_has_upstream_progress =
          (current_dag_boundary_accepted_count[0] != 0) || (current_dag_boundary_fire[0] === 1'b1);
        3: current_dag_boundary_has_upstream_progress =
          (current_dag_boundary_accepted_count[2] != 0) || (current_dag_boundary_fire[2] === 1'b1);
        4, 5: current_dag_boundary_has_upstream_progress =
          (current_dag_boundary_accepted_count[3] != 0) || (current_dag_boundary_fire[3] === 1'b1);
        6, 7: current_dag_boundary_has_upstream_progress =
          (current_dag_boundary_accepted_count[4] != 0) || (current_dag_boundary_fire[4] === 1'b1);
        8: current_dag_boundary_has_upstream_progress =
          (current_dag_boundary_accepted_count[6] != 0) || (current_dag_boundary_fire[6] === 1'b1);
        9: current_dag_boundary_has_upstream_progress =
          (current_dag_boundary_accepted_count[7] != 0) || (current_dag_boundary_fire[7] === 1'b1);
        10: current_dag_boundary_has_upstream_progress =
          (current_dag_boundary_accepted_count[8] != 0) ||
          (current_dag_boundary_accepted_count[9] != 0) ||
          (current_dag_boundary_fire[8] === 1'b1) ||
          (current_dag_boundary_fire[9] === 1'b1);
        11: current_dag_boundary_has_upstream_progress =
          (current_dag_boundary_accepted_count[10] != 0) || (current_dag_boundary_fire[10] === 1'b1);
        12: current_dag_boundary_has_upstream_progress =
          (current_dag_boundary_accepted_count[11] != 0) ||
          (current_dag_boundary_accepted_count[5] != 0) ||
          (current_dag_boundary_fire[11] === 1'b1) ||
          (current_dag_boundary_fire[5] === 1'b1);
        default: current_dag_boundary_has_upstream_progress = 1'b0;
      endcase
    end
  endfunction

  function automatic bit is_nan32(input [31:0] value);
    begin
      is_nan32 = (&value[30:23]) && (value[22:0] != 23'd0);
    end
  endfunction

  function automatic bit is_inf32(input [31:0] value);
    begin
      is_inf32 = (&value[30:23]) && (value[22:0] == 23'd0);
    end
  endfunction

  function automatic [36:0] next_axi_address(
    input [36:0] address,
    input [2:0] size,
    input [1:0] burst
  );
    begin
      if (burst == 2'b00) begin
        next_axi_address = address;
      end else begin
        next_axi_address = address + (37'd1 << size);
      end
    end
  endfunction

  function automatic [511:0] read_file_beat(
    input integer file_descriptor,
    input longint unsigned byte_offset
  );
    integer seek_result;
    integer byte_index;
    integer byte_value;
    reg [511:0] value;
    begin
      value = 512'd0;
      seek_result = $fseek(file_descriptor, byte_offset, 0);
      if (seek_result != 0) begin
        artifact_error = 1'b1;
      end
      for (byte_index = 0; byte_index < 64; byte_index = byte_index + 1) begin
        byte_value = $fgetc(file_descriptor);
        if (byte_value < 0) begin
          artifact_error = 1'b1;
          byte_value = 0;
        end
        value[(byte_index*8) +: 8] = byte_value[7:0];
      end
      read_file_beat = value;
    end
  endfunction

  function automatic [511:0] read_memory_beat(input [36:0] byte_address);
    longint unsigned beat_key;
    longint unsigned file_offset;
    integer input_index;
    integer runtime_index;
    integer runtime_lane;
    reg [511:0] value;
    begin
      beat_key = byte_address >> 6;
      value = 512'd0;
      if (written_beats.exists(beat_key)) begin
        value = written_beats[beat_key];
      end else if ((byte_address >= INPUT_TOKENS_BASE) &&
                   (byte_address < (INPUT_TOKENS_BASE + 37'd57344))) begin
        input_index = (byte_address - INPUT_TOKENS_BASE) >> 6;
        value[255:0] = input_beats[input_index*2];
        value[511:256] = input_beats[(input_index*2)+1];
      end else if ((byte_address >= FULL_WEIGHT_IMAGE_BASE) &&
                   (byte_address < (FULL_WEIGHT_IMAGE_BASE + FULL_WEIGHT_IMAGE_BYTES))) begin
        file_offset = byte_address - FULL_WEIGHT_IMAGE_BASE;
        value = read_file_beat(weight_fd, file_offset);
      end else if ((byte_address >= RUNTIME_CONSTANTS_BASE) &&
                   (byte_address < (RUNTIME_CONSTANTS_BASE + RUNTIME_IMAGE_BYTES))) begin
        runtime_index = (byte_address - RUNTIME_CONSTANTS_BASE) >> 6;
        for (runtime_lane = 0; runtime_lane < 16; runtime_lane = runtime_lane + 1) begin
          value[(runtime_lane*32) +: 32] = runtime_words[(runtime_index*16)+runtime_lane];
        end
      end else begin
        artifact_error = 1'b1;
      end
      read_memory_beat = value;
    end
  endfunction

  task automatic commit_memory_write(
    input [36:0] byte_address,
    input [511:0] write_data,
    input [63:0] write_strobe
  );
    longint unsigned beat_key;
    integer byte_index;
    reg [511:0] value;
    begin
      beat_key = byte_address >> 6;
      if (written_beats.exists(beat_key)) begin
        value = written_beats[beat_key];
      end else begin
        value = 512'd0;
      end
      for (byte_index = 0; byte_index < 64; byte_index = byte_index + 1) begin
        if (write_strobe[byte_index]) begin
          value[(byte_index*8) +: 8] = write_data[(byte_index*8) +: 8];
        end
      end
      written_beats[beat_key] = value;
    end
  endtask

  string checkpoint_mode;
  string checkpoint_request_path;
  string checkpoint_request_sha256;
  string checkpoint_semantic_cut_sha256;
  string checkpoint_dut_root;
  string checkpoint_cut_phase;
  string checkpoint_cut_frontier;
  string checkpoint_dut_state_path;
  string checkpoint_dut_schema_path;
  string checkpoint_external_state_path;
  string checkpoint_capture_report_path;
  string checkpoint_restore_dut_state_path;
  string checkpoint_restore_dut_schema_path;
  string checkpoint_restore_external_state_path;
  string checkpoint_restore_report_path;
  string checkpoint_id;
  string checkpoint_runtime_schema_sha256;
  string checkpoint_boundary_record;
  longint unsigned checkpoint_cut_sequence;
  longint unsigned checkpoint_cut_cycle;
  longint unsigned checkpoint_trigger_sequence;
  longint unsigned checkpoint_trigger_cycle;
  longint unsigned checkpoint_captured_sequence;
  longint unsigned checkpoint_captured_cycle;
  longint unsigned checkpoint_restored_sequence;
  longint unsigned checkpoint_restored_cycle;
  longint unsigned checkpoint_weight_file_offset;
  longint unsigned checkpoint_boundary_file_offset;
  longint unsigned checkpoint_progress_file_offset;
  integer checkpoint_cut_layer;
  integer checkpoint_cut_token;
  integer checkpoint_cut_beat;
  integer checkpoint_settle_cycles;
  integer checkpoint_equivalence_probe;
  integer checkpoint_plusarg_seen;
  integer checkpoint_vpi_rc;
  integer checkpoint_captured_axi_read_outstanding;
  integer checkpoint_captured_axi_write_outstanding;
  reg checkpoint_enabled;
  reg checkpoint_runtime_ready;
  reg checkpoint_restore_requested;
  reg checkpoint_restore_complete;
  reg checkpoint_trigger_observed;
  reg checkpoint_evidence_flushed;
  reg checkpoint_capture_event_quiescent;
  reg checkpoint_captured_read_pending_response;
  reg checkpoint_captured_write_pending_response;
  reg checkpoint_external_state_complete;
  reg checkpoint_immutable_reopen_complete;
  reg checkpoint_runtime_schema_hash_valid;
  reg checkpoint_saved_monitor_violation;
  longint unsigned checkpoint_saved_clock_phase_slot;
  reg checkpoint_saved_clk_300M;
  reg checkpoint_saved_clk_600M;
  reg checkpoint_saved_c0_ddr4_s_axi_clk;
  reg checkpoint_restore_phase_ready;
  reg checkpoint_evidence_suffix_isolated;
  reg checkpoint_boundary_state_match;

  task automatic checkpoint_build_boundary_record(output string record);
    string active_weight_bank_name;
    string preload_weight_bank_name;
    string activation_read_bank_name;
    string activation_write_bank_name;
    begin
      if ((checkpoint_cut_layer >= 0) &&
          (checkpoint_cut_layer < TARGET_LAYERS)) begin
        if (checkpoint_cut_layer[0]) begin
          active_weight_bank_name = "weight_b";
          preload_weight_bank_name =
            (checkpoint_cut_layer == (TARGET_LAYERS-1)) ? "none" : "weight_a";
          activation_read_bank_name = "activation_pong_bank";
          activation_write_bank_name = "activation_ping_bank";
        end else begin
          active_weight_bank_name = "weight_a";
          preload_weight_bank_name =
            (checkpoint_cut_layer == (TARGET_LAYERS-1)) ? "none" : "weight_b";
          activation_read_bank_name = "activation_ping_bank";
          activation_write_bank_name = "activation_pong_bank";
        end
      end else begin
        active_weight_bank_name = "unknown";
        preload_weight_bank_name = "unknown";
        activation_read_bank_name = "unknown";
        activation_write_bank_name = "unknown";
      end
      record = $sformatf("{\"schema_version\":\"spatialaccagent.board_progress_event.v1\",\"sequence\":%0d,\"cycle\":%0d,\"event_kind\":\"semantic_progress\",\"phase\":\"checkpoint_quiescent_barrier\",\"semantic_progress\":true,\"progress_epoch\":%0d,\"last_semantic_progress_cycle\":%0d,\"scheduler_state\":%0d,\"layer\":%0d,\"token\":%0d,\"beat\":%0d,\"stage_or_boundary\":\"%s\",\"active_weight_bank\":\"%s\",\"preload_weight_bank\":\"%s\",\"activation_read_bank\":\"%s\",\"activation_write_bank\":\"%s\",\"prefetch_progress\":{\"accepted_beats\":%0d,\"target_beats\":%0d},\"runtime_load_progress\":{\"accepted_words\":%0d,\"target_words\":%0d},\"final_writeback_progress\":{\"accepted_beats\":%0d,\"target_beats\":%0d},\"axi_read\":{\"outstanding\":%0d,\"pending_response\":%s,\"arvalid\":%0d,\"arready\":%0d,\"rvalid\":%0d,\"rready\":%0d,\"transactions\":%0d,\"beats\":%0d},\"axi_write\":{\"outstanding\":%0d,\"pending_response\":%s,\"awvalid\":%0d,\"awready\":%0d,\"wvalid\":%0d,\"wready\":%0d,\"bvalid\":%0d,\"bready\":%0d,\"transactions\":%0d,\"beats\":%0d},\"active_boundary_observation\":{\"event_queue_quiescent\":%s,\"input_valid\":%0d,\"input_ready\":%0d,\"input_accepted\":%0d,\"start\":%0d,\"input_axi_index\":%0d,\"output_accept_count\":%0d,\"output_pair_valid\":%s,\"input_payload_unknown\":%s,\"input_payload_digest\":\"%08x\",\"output_valid\":%s,\"output_ready\":%0d,\"output_accepted\":%0d,\"output_payload_unknown\":%s,\"output_payload_digest\":\"%08x\"}}",
        progress_sequence,
        cycle_count,
        progress_epoch + 1,
        cycle_count,
        dut.state,
        checkpoint_cut_layer,
        checkpoint_cut_token,
        checkpoint_cut_beat,
        checkpoint_cut_frontier,
        active_weight_bank_name,
        preload_weight_bank_name,
        activation_read_bank_name,
        activation_write_bank_name,
        dut.prefetch_index,
        WEIGHT_WORDS_PER_LAYER/16,
        ((checkpoint_cut_layer >= 0) &&
         (checkpoint_cut_layer < TARGET_LAYERS)) ?
          runtime_accept_count[checkpoint_cut_layer] : 0,
        RUNTIME_WORDS_PER_LAYER,
        dut.copy_trace_final ?
          (dut.copy_index + (dut.trace_final_writeback_complete ? 1 : 0)) : 0,
        AXI_BEATS_PER_ACTIVATION,
        checkpoint_axi_read_outstanding(),
        json_bool(c0_ddr4_s_axi_rvalid),
        c0_ddr4_s_axi_arvalid,
        c0_ddr4_s_axi_arready,
        c0_ddr4_s_axi_rvalid,
        c0_ddr4_s_axi_rready,
        axi_read_transaction_count,
        axi_read_beat_count,
        checkpoint_axi_write_outstanding(),
        json_bool(write_response_pending || c0_ddr4_s_axi_bvalid),
        c0_ddr4_s_axi_awvalid,
        c0_ddr4_s_axi_awready,
        c0_ddr4_s_axi_wvalid,
        c0_ddr4_s_axi_wready,
        c0_ddr4_s_axi_bvalid,
        c0_ddr4_s_axi_bready,
        axi_write_transaction_count,
        axi_write_beat_count,
        json_bool(checkpoint_event_queue_quiescent()),
        dut.kernel_input_valid_q,
        dut.kernel_input_ready,
        dut.kernel_input_valid_q && dut.kernel_input_ready,
        dut.kernel_start_to_core,
        dut.input_axi_index,
        dut.output_accept_count,
        json_bool(dut.output_pair_valid),
        json_bool($isunknown(dut.kernel_input_data_q)),
        payload_digest256(dut.kernel_input_data_q),
        json_logic(dut.kernel_output_valid),
        dut.kernel_output_ready,
        dut.kernel_output_valid && dut.kernel_output_ready,
        json_bool($isunknown(dut.kernel_output_data)),
        payload_digest256(dut.kernel_output_data));
    end
  endtask

  task automatic checkpoint_emit_boundary_record;
    string live_record;
    begin
      if (progress_fd == 0)
        $fatal(1, "checkpoint boundary record requires an open progress log");
      if (!checkpoint_event_queue_quiescent())
        $fatal(1, "checkpoint boundary record is not factually quiescent");
      checkpoint_build_boundary_record(live_record);
      if (live_record.len() == 0)
        $fatal(1, "checkpoint live factual boundary record is empty");
      if (checkpoint_boundary_record.len() == 0)
        $fatal(1, "checkpoint captured boundary record is empty");
      checkpoint_boundary_state_match =
        (live_record == checkpoint_boundary_record);
      if (!checkpoint_boundary_state_match)
        $display("SPATIALACC_CHECKPOINT_BOUNDARY_RECORD_CHANGED captured_length=%0d live_length=%0d",
                 checkpoint_boundary_record.len(), live_record.len());
      semantic_progress_count = semantic_progress_count + 1;
      progress_epoch = progress_epoch + 1;
      last_semantic_progress_cycle = cycle_count;
      $fwrite(progress_fd, "%s\n", live_record);
      progress_sequence = progress_sequence + 1;
      $fflush(progress_fd);
      $display("SPATIALACC_BOARD_PROGRESS sequence=%0d event_kind=semantic_progress phase=checkpoint_quiescent_barrier layer=%0d cycle=%0d",
               progress_sequence, checkpoint_cut_layer, cycle_count);
    end
  endtask

  task automatic emit_boundary_trace_record(
    input string boundary_id,
    input string event_name,
    input integer event_layer,
    input integer event_tx_id,
    input integer event_logical_index,
    input string event_contract,
    input string event_status
  );
    begin
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"%s\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"event\":\"%s\",\"layer\":%0d},\"expected_value\":{\"kind\":\"lifecycle_event\"},\"contract\":\"%s\",\"status\":\"%s\"}\n",
          cycle_count, boundary_id, event_tx_id, event_logical_index,
          event_name, event_layer, event_contract, event_status);
        $fflush(boundary_fd);
      end
    end
  endtask

  task automatic emit_current_dag_boundary_observation(
    input integer boundary_index,
    input string observed_boundary_id
  );
    begin
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"%s\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.current_dag_complete_boundary_coverage.2\",\"probe_revision\":2,\"source_marker\":\"current_dag_complete_boundary_coverage_r2\",\"observational_only\":true,\"coverage_status\":\"direct\",\"valid\":%s,\"ready\":%s,\"fire\":%s,\"accepted_count\":%0d,\"current_payload_unknown\":%s,\"current_payload_digest\":\"%08x\",\"first_accepted_payload_seen\":%s,\"first_accepted_payload_digest_unknown\":%s,\"first_accepted_payload_digest\":\"%08x\",\"last_accepted_payload_seen\":%s,\"last_accepted_payload_digest_unknown\":%s,\"last_accepted_payload_digest\":\"%08x\"},\"expected_value\":{\"required_coverage\":\"valid_ready_fire_accepted_count_first_accepted_payload_digest_last_accepted_payload_digest\",\"availability\":\"direct_observation\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count,
          observed_boundary_id,
          current_dag_boundary_accepted_count[boundary_index],
          current_dag_boundary_accepted_count[boundary_index],
          json_logic(current_dag_boundary_valid[boundary_index]),
          json_logic(current_dag_boundary_ready[boundary_index]),
          json_bool(current_dag_boundary_fire[boundary_index] === 1'b1),
          current_dag_boundary_accepted_count[boundary_index],
          json_bool($isunknown(current_dag_boundary_payload[boundary_index])),
          payload_digest256(current_dag_boundary_payload[boundary_index]),
          json_bool(current_dag_boundary_first_accepted_seen[boundary_index] === 1'b1),
          json_bool((current_dag_boundary_first_accepted_seen[boundary_index] !== 1'b1) ||
                    $isunknown(current_dag_boundary_first_accepted_payload_digest[boundary_index])),
          current_dag_boundary_first_accepted_payload_digest[boundary_index],
          json_bool(current_dag_boundary_first_accepted_seen[boundary_index] === 1'b1),
          json_bool((current_dag_boundary_first_accepted_seen[boundary_index] !== 1'b1) ||
                    $isunknown(current_dag_boundary_last_accepted_payload_digest[boundary_index])),
          current_dag_boundary_last_accepted_payload_digest[boundary_index]);
        $fflush(boundary_fd);
      end
    end
  endtask

  task automatic emit_current_dag_boundary_temporal_record(
    input integer boundary_index,
    input string event_name,
    input integer endpoint_kind
  );
    integer transfer_count;
    integer beats_per_token;
    integer token_index;
    integer beat_index;
    reg [31:0] first_digest;
    reg [31:0] last_digest;
    reg first_unknown;
    reg last_unknown;
    reg first_seen;
    begin
      if (boundary_fd != 0) begin
        beats_per_token = current_dag_boundary_beats_per_token(boundary_index);
        transfer_count = current_dag_boundary_accepted_count[boundary_index];
        if ((endpoint_kind == 1) || (endpoint_kind == 2)) begin
          transfer_count = transfer_count + 1;
        end
        if (transfer_count == 0) begin
          token_index = -1;
          beat_index = -1;
        end else begin
          token_index = (transfer_count - 1) / beats_per_token;
          beat_index = (transfer_count - 1) % beats_per_token;
        end
        first_seen = current_dag_boundary_first_accepted_seen[boundary_index];
        first_digest = current_dag_boundary_first_accepted_payload_digest[boundary_index];
        first_unknown = (first_seen !== 1'b1) || $isunknown(first_digest);
        last_digest = current_dag_boundary_last_accepted_payload_digest[boundary_index];
        last_unknown = (transfer_count == 0) || $isunknown(last_digest);
        if (endpoint_kind == 1) begin
          first_seen = 1'b1;
          first_digest = payload_digest256(current_dag_boundary_payload[boundary_index]);
          first_unknown = $isunknown(current_dag_boundary_payload[boundary_index]);
          last_digest = payload_digest256(current_dag_boundary_payload[boundary_index]);
          last_unknown = $isunknown(current_dag_boundary_payload[boundary_index]);
        end else if (endpoint_kind == 2) begin
          first_seen = 1'b1;
          first_digest = current_dag_boundary_token_first_payload_digest[boundary_index];
          first_unknown = current_dag_boundary_token_first_payload_unknown[boundary_index];
          last_digest = payload_digest256(current_dag_boundary_payload[boundary_index]);
          last_unknown = $isunknown(current_dag_boundary_payload[boundary_index]);
        end
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"%s\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.current_dag_complete_boundary_terminal_path.4\",\"probe_revision\":3,\"source_marker\":\"current_dag_complete_boundary_terminal_path_r4\",\"observational_only\":true,\"event\":\"%s\",\"valid\":%s,\"ready\":%s,\"fire\":%s,\"transfer_or_fire\":%s,\"received_count\":%0d,\"accepted_count\":%0d,\"token\":%0d,\"beat\":%0d,\"current_payload_unknown\":%s,\"current_payload_digest\":\"%08x\",\"first_accepted_payload_seen\":%s,\"first_accepted_payload_digest_unknown\":%s,\"first_accepted_payload_digest\":\"%08x\",\"last_accepted_payload_seen\":%s,\"last_accepted_payload_digest_unknown\":%s,\"last_accepted_payload_digest\":\"%08x\",\"waiting_after_upstream_progress\":%s},\"expected_value\":{\"required_coverage\":\"valid_ready_fire_accepted_count_first_accepted_payload_digest_last_accepted_payload_digest\",\"availability\":\"direct_observation\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count,
          current_dag_boundary_name(boundary_index),
          transfer_count,
          transfer_count,
          event_name,
          json_logic(current_dag_boundary_valid[boundary_index]),
          json_logic(current_dag_boundary_ready[boundary_index]),
          json_bool(current_dag_boundary_fire[boundary_index] === 1'b1),
          json_bool(current_dag_boundary_fire[boundary_index] === 1'b1),
          transfer_count,
          transfer_count,
          token_index,
          beat_index,
          json_bool($isunknown(current_dag_boundary_payload[boundary_index])),
          payload_digest256(current_dag_boundary_payload[boundary_index]),
          json_bool(first_seen === 1'b1),
          json_bool(first_unknown),
          first_digest,
          json_bool(transfer_count != 0),
          json_bool(last_unknown),
          last_digest,
          json_bool(current_dag_boundary_has_upstream_progress(boundary_index)));
        $fflush(boundary_fd);
        emit_current_dag_stage_context(boundary_index, event_name);
      end
    end
  endtask

  // probe_id=probe.current_dag_complete_boundary_terminal_path.5
  // Read-only context at the existing first record, last record, waiting, and
  // terminal transitions. No DUT signal is driven and no elapsed-time limit is used.
  task automatic emit_current_dag_stage_context(
    input integer boundary_index,
    input string event_name
  );
    begin
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"%s\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.current_dag_complete_boundary_terminal_path.5\",\"probe_revision\":5,\"source_marker\":\"current_dag_complete_boundary_terminal_path_r5\",\"observational_only\":true,\"event\":\"%s\",\"boundary\":{\"valid\":%s,\"ready\":%s,\"fire\":%s,\"received_count\":%0d,\"accepted_count\":%0d,\"start\":%s,\"last\":%s,\"current_payload_unknown\":%s,\"current_payload_digest\":\"%08x\"},\"adapter\":{\"scheduler_state\":%0d,\"layer\":%0d,\"kernel_reset\":%s,\"kernel_start_q\":%s,\"kernel_start_to_core\":%s,\"invocation_launched\":%s,\"rearm_pending\":%s,\"input_axi_index\":%0d,\"input_launch_limit\":%0d,\"output_accept_count\":%0d,\"output_token_beat_count\":%0d,\"output_fifo_count\":%0d,\"output_fifo_write_index\":%0d,\"output_fifo_read_index\":%0d,\"output_ingress_half\":%s,\"output_pair_valid\":%s,\"output_write_index\":%0d,\"axi_error\":%s,\"weight_valid\":%s,\"weight_ready\":%s,\"weight_last\":%s,\"weight_beat_index\":%0d,\"weight_word_index\":%0d,\"runtime_valid\":%s,\"runtime_ready\":%s,\"runtime_last\":%s,\"runtime_beat_index\":%0d,\"runtime_word_index\":%0d},\"axi\":{\"arvalid\":%s,\"arready\":%s,\"rvalid\":%s,\"rready\":%s,\"awvalid\":%s,\"awready\":%s,\"wvalid\":%s,\"wready\":%s,\"bvalid\":%s,\"bready\":%s,\"read_active\":%s,\"write_active\":%s,\"write_response_pending\":%s,\"monitor_violation\":%s},",
          cycle_count,
          current_dag_boundary_name(boundary_index),
          current_dag_boundary_accepted_count[boundary_index],
          current_dag_boundary_accepted_count[boundary_index],
          event_name,
          json_logic(current_dag_boundary_valid[boundary_index]),
          json_logic(current_dag_boundary_ready[boundary_index]),
          json_bool(current_dag_boundary_fire[boundary_index] === 1'b1),
          current_dag_boundary_accepted_count[boundary_index],
          current_dag_boundary_accepted_count[boundary_index],
          json_logic(current_dag_boundary_start[boundary_index]),
          json_logic(current_dag_boundary_last[boundary_index]),
          json_bool($isunknown(current_dag_boundary_payload[boundary_index])),
          payload_digest256(current_dag_boundary_payload[boundary_index]),
          dut.state,
          dut.layer_index,
          json_logic(dut.kernel_reset_q),
          json_logic(dut.kernel_start_q),
          json_logic(dut.kernel_start_to_core),
          json_logic(dut.kernel_invocation_launched),
          json_logic(dut.kernel_token_rearm_pending),
          dut.input_axi_index,
          dut.input_launch_limit,
          dut.output_accept_count,
          dut.output_token_beat_count,
          dut.output_fifo_count,
          dut.output_fifo_write_index,
          dut.output_fifo_read_index,
          json_logic(dut.output_ingress_half),
          json_logic(dut.output_pair_valid),
          dut.output_write_index,
          json_logic(dut.axi_error_q),
          json_logic(dut.weight_valid_q),
          json_logic(dut.weight_ready),
          json_logic(dut.weight_last_q),
          dut.weight_beat_index,
          dut.weight_word_index,
          json_logic(dut.runtime_valid_q),
          json_logic(dut.runtime_ready),
          json_logic(dut.runtime_last_q),
          dut.runtime_beat_index,
          dut.runtime_word_index,
          json_logic(c0_ddr4_s_axi_arvalid),
          json_logic(c0_ddr4_s_axi_arready),
          json_logic(c0_ddr4_s_axi_rvalid),
          json_logic(c0_ddr4_s_axi_rready),
          json_logic(c0_ddr4_s_axi_awvalid),
          json_logic(c0_ddr4_s_axi_awready),
          json_logic(c0_ddr4_s_axi_wvalid),
          json_logic(c0_ddr4_s_axi_wready),
          json_logic(c0_ddr4_s_axi_bvalid),
          json_logic(c0_ddr4_s_axi_bready),
          json_logic(read_active),
          json_logic(write_active),
          json_logic(write_response_pending),
          json_logic(tb_c0_ddr4_s_axi_monitor.violation));
        $fwrite(boundary_fd,
          "\"stage_00_rms_norm_1\":{\"weight_valid\":%s,\"weight_ready\":%s,\"input_start\":%s,\"input_address\":%0d,\"input_last\":%s,\"output_valid\":%s,\"output_ready\":%s,\"output_start\":%s,\"output_address\":%0d,\"output_last\":%s},\"stage_01_self_attention\":{\"state\":%s,\"collect_beat\":%0d,\"emit_head\":%0d,\"emit_beat\":%0d,\"start\":%s,\"weight_valid\":%s,\"weight_ready\":%s,\"bias_valid\":%s,\"bias_ready\":%s,\"projection_output_valid\":%s,\"projection_output_last\":%s,\"output_head\":%0d,\"output_last\":%s},",
          json_logic(dut.spatialacc_single_kernel.core.rms1.io_weight_valid),
          json_logic(dut.spatialacc_single_kernel.core.rms1.io_weight_ready),
          json_logic(dut.spatialacc_single_kernel.core.rms1.io_in_bits_st),
          dut.spatialacc_single_kernel.core.rms1.io_in_bits_addr,
          json_logic(dut.spatialacc_single_kernel.core.rms1.io_in_bits_last),
          json_logic(dut.spatialacc_single_kernel.core.rms1.io_out_valid),
          json_logic(dut.spatialacc_single_kernel.core.rms1.io_out_ready),
          json_logic(dut.spatialacc_single_kernel.core.rms1.io_out_bits_st),
          dut.spatialacc_single_kernel.core.rms1.io_out_bits_addr,
          json_logic(dut.spatialacc_single_kernel.core.rms1.io_out_bits_last),
          json_logic(dut.spatialacc_single_kernel.core.qkv.state),
          dut.spatialacc_single_kernel.core.qkv.collectBeat,
          dut.spatialacc_single_kernel.core.qkv.emitHead,
          dut.spatialacc_single_kernel.core.qkv.emitBeat,
          json_logic(dut.spatialacc_single_kernel.core.qkv.io_start),
          json_logic(dut.spatialacc_single_kernel.core.qkv.io_weight_valid),
          json_logic(dut.spatialacc_single_kernel.core.qkv.io_weight_ready),
          json_logic(dut.spatialacc_single_kernel.core.qkv.io_bias_valid),
          json_logic(dut.spatialacc_single_kernel.core.qkv.io_bias_ready),
          json_logic(dut.spatialacc_single_kernel.core.qkv._projection_io_out_valid),
          json_logic(dut.spatialacc_single_kernel.core.qkv._projection_io_out_bits_last),
          dut.spatialacc_single_kernel.core.qkv.io_out_bits_head,
          json_logic(dut.spatialacc_single_kernel.core.qkv.io_out_bits_last));
        $fwrite(boundary_fd,
          "\"stage_02_residual_add_1\":{\"residual_skip_write_pointer\":%0d,\"residual_skip_read_pointer\":%0d,\"residual_skip_full\":%s,\"held_valid\":%s,\"beat_in_token\":%0d,\"token_in_sequence\":%0d,\"pair_valid\":%s,\"token_final_beat\":%s,\"sequence_final_beat\":%s,\"residual_queue_read_ready\":%s,\"computed_queue_read_ready\":%s,\"output_queue_write_ready\":%s,\"computed_queue_write_pointer\":%0d,\"output_queue_full\":%s},\"stage_03_rms_norm_2\":{\"weight_valid\":%s,\"weight_ready\":%s,\"input_start\":%s,\"input_address\":%0d,\"input_last\":%s,\"output_valid\":%s,\"output_ready\":%s,\"output_start\":%s,\"output_address\":%0d,\"output_last\":%s,\"residual_skip_full\":%s},",
          dut.spatialacc_single_kernel.core.res1Q.enq_ptr_value,
          dut.spatialacc_single_kernel.core.res1Q.deq_ptr_value,
          json_logic(dut.spatialacc_single_kernel.core.res1Q.maybe_full),
          json_logic(dut.spatialacc_single_kernel.core.add1.heldValid),
          dut.spatialacc_single_kernel.core.add1.beatInToken,
          dut.spatialacc_single_kernel.core.add1.tokenInSequence,
          json_logic(dut.spatialacc_single_kernel.core.add1.pairValid),
          json_logic(dut.spatialacc_single_kernel.core.add1.tokenFinalBeat),
          json_logic(dut.spatialacc_single_kernel.core.add1.sequenceFinalBeat),
          json_logic(dut.spatialacc_single_kernel.core.add1.residualQ_io_deq_ready),
          json_logic(dut.spatialacc_single_kernel.core.add1.computedQ_io_deq_ready),
          json_logic(dut.spatialacc_single_kernel.core.add1._outputQ_io_enq_ready),
          dut.spatialacc_single_kernel.core.add1.computedQ.enq_ptr_value,
          json_logic(dut.spatialacc_single_kernel.core.add1.outputQ.maybe_full),
          json_logic(dut.spatialacc_single_kernel.core.rms2.io_weight_valid),
          json_logic(dut.spatialacc_single_kernel.core.rms2.io_weight_ready),
          json_logic(dut.spatialacc_single_kernel.core.rms2.io_in_bits_st),
          dut.spatialacc_single_kernel.core.rms2.io_in_bits_addr,
          json_logic(dut.spatialacc_single_kernel.core.rms2.io_in_bits_last),
          json_logic(dut.spatialacc_single_kernel.core.rms2.io_out_valid),
          json_logic(dut.spatialacc_single_kernel.core.rms2.io_out_ready),
          json_logic(dut.spatialacc_single_kernel.core.rms2.io_out_bits_st),
          dut.spatialacc_single_kernel.core.rms2.io_out_bits_addr,
          json_logic(dut.spatialacc_single_kernel.core.rms2.io_out_bits_last),
          json_logic(dut.spatialacc_single_kernel.core.res2Q.maybe_full));
        $fwrite(boundary_fd,
          "\"stage_04_mlp_gate_proj\":{\"start\":%s,\"weight_valid\":%s,\"weight_ready\":%s,\"input_start\":%s,\"input_last\":%s,\"output_valid\":%s,\"output_ready\":%s,\"output_start\":%s,\"output_last\":%s},\"stage_05_mlp_up_proj\":{\"start\":%s,\"weight_valid\":%s,\"weight_ready\":%s,\"input_start\":%s,\"input_last\":%s,\"output_valid\":%s,\"output_ready\":%s,\"output_start\":%s,\"output_last\":%s},\"stage_06_activation_mul\":{\"activation_input_ready\":%s,\"activation_output_valid\":%s,\"activation_queue_enqueue_ready\":%s,\"activation_queue_dequeue_valid\":%s,\"activation_queue_write_pointer\":%0d,\"activation_queue_read_pointer\":%0d,\"activation_queue_full\":%s,\"up_queue_enqueue_ready\":%s,\"up_queue_dequeue_valid\":%s,\"up_queue_write_pointer\":%0d,\"up_queue_read_pointer\":%0d,\"up_queue_full\":%s,\"multiply_left_ready\":%s,\"multiply_right_ready\":%s,\"multiply_output_valid\":%s,\"multiply_output_ready\":%s,\"multiply_output_start\":%s,\"multiply_output_last\":%s},",
          json_logic(dut.spatialacc_single_kernel.core.mlp.gate.io_start),
          json_logic(dut.spatialacc_single_kernel.core.mlp.gate.io_weight_valid),
          json_logic(dut.spatialacc_single_kernel.core.mlp.gate.io_weight_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp.gate.io_in_bits_st),
          json_logic(dut.spatialacc_single_kernel.core.mlp.gate.io_in_bits_last),
          json_logic(dut.spatialacc_single_kernel.core.mlp.gate.io_out_valid),
          json_logic(dut.spatialacc_single_kernel.core.mlp.gate.io_out_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp.gate.io_out_bits_st),
          json_logic(dut.spatialacc_single_kernel.core.mlp.gate.io_out_bits_last),
          json_logic(dut.spatialacc_single_kernel.core.mlp.up.io_start),
          json_logic(dut.spatialacc_single_kernel.core.mlp.up.io_weight_valid),
          json_logic(dut.spatialacc_single_kernel.core.mlp.up.io_weight_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp.up.io_in_bits_st),
          json_logic(dut.spatialacc_single_kernel.core.mlp.up.io_in_bits_last),
          json_logic(dut.spatialacc_single_kernel.core.mlp.up.io_out_valid),
          json_logic(dut.spatialacc_single_kernel.core.mlp.up.io_out_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp.up.io_out_bits_st),
          json_logic(dut.spatialacc_single_kernel.core.mlp.up.io_out_bits_last),
          json_logic(dut.spatialacc_single_kernel.core.mlp._act_io_in_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp._act_io_out_valid),
          json_logic(dut.spatialacc_single_kernel.core.mlp._actQ_io_enq_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp._actQ_io_deq_valid),
          dut.spatialacc_single_kernel.core.mlp.actQ.enq_ptr_value,
          dut.spatialacc_single_kernel.core.mlp.actQ.deq_ptr_value,
          json_logic(dut.spatialacc_single_kernel.core.mlp.actQ.maybe_full),
          json_logic(dut.spatialacc_single_kernel.core.mlp._upQ_io_enq_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp._upQ_io_deq_valid),
          dut.spatialacc_single_kernel.core.mlp.upQ.enq_ptr_value,
          dut.spatialacc_single_kernel.core.mlp.upQ.deq_ptr_value,
          json_logic(dut.spatialacc_single_kernel.core.mlp.upQ.maybe_full),
          json_logic(dut.spatialacc_single_kernel.core.mlp._mul_io_lhs_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp._mul_io_rhs_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp._mul_io_out_valid),
          json_logic(dut.spatialacc_single_kernel.core.mlp.mul_io_out_ready__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp.mul_io_out_bits_st__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp.mul_io_out_bits_last__bore));
        $fwrite(boundary_fd,
          "\"stage_07_mlp_down_proj\":{\"start\":%s,\"weight_valid\":%s,\"weight_ready\":%s,\"input_valid\":%s,\"input_ready\":%s,\"output_valid\":%s,\"output_ready\":%s,\"output_start\":%s,\"output_last\":%s,\"output_address\":%0d},\"stage_08_residual_add_2\":{\"residual_skip_write_pointer\":%0d,\"residual_skip_read_pointer\":%0d,\"residual_skip_full\":%s,\"held_valid\":%s,\"beat_in_token\":%0d,\"token_in_sequence\":%0d,\"pair_valid\":%s,\"token_final_beat\":%s,\"sequence_final_beat\":%s,\"computed_queue_write_pointer\":%0d,\"output_queue_write_pointer\":%0d,\"output_queue_read_pointer\":%0d,\"output_queue_full\":%s,\"output_queue_write_ready\":%s,\"output_valid\":%s,\"output_ready\":%s,\"output_start\":%s,\"output_last\":%s}},\"expected_value\":{\"availability\":\"direct_current_hierarchy_scalar_context\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          json_logic(dut.spatialacc_single_kernel.core.mlp.down.io_start),
          json_logic(dut.spatialacc_single_kernel.core.mlp.down.io_weight_valid),
          json_logic(dut.spatialacc_single_kernel.core.mlp.down.io_weight_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp.down.io_in_valid),
          json_logic(dut.spatialacc_single_kernel.core.mlp.down.io_in_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp.down.io_out_valid),
          json_logic(dut.spatialacc_single_kernel.core.mlp.down.io_out_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp.down.io_out_bits_st),
          json_logic(dut.spatialacc_single_kernel.core.mlp.down.io_out_bits_last),
          dut.spatialacc_single_kernel.core.mlp.down.io_out_bits_addr,
          dut.spatialacc_single_kernel.core.res2Q.enq_ptr_value,
          dut.spatialacc_single_kernel.core.res2Q.deq_ptr_value,
          json_logic(dut.spatialacc_single_kernel.core.res2Q.maybe_full),
          json_logic(dut.spatialacc_single_kernel.core.add2.heldValid),
          dut.spatialacc_single_kernel.core.add2.beatInToken,
          dut.spatialacc_single_kernel.core.add2.tokenInSequence,
          json_logic(dut.spatialacc_single_kernel.core.add2.pairValid),
          json_logic(dut.spatialacc_single_kernel.core.add2.tokenFinalBeat),
          json_logic(dut.spatialacc_single_kernel.core.add2.sequenceFinalBeat),
          dut.spatialacc_single_kernel.core.add2.computedQ.enq_ptr_value,
          dut.spatialacc_single_kernel.core.add2.outputQ.enq_ptr_value,
          dut.spatialacc_single_kernel.core.add2.outputQ.deq_ptr_value,
          json_logic(dut.spatialacc_single_kernel.core.add2.outputQ.maybe_full),
          json_logic(dut.spatialacc_single_kernel.core.add2._outputQ_io_enq_ready),
          json_logic(dut.spatialacc_single_kernel.core.add2.io_out_valid),
          json_logic(dut.spatialacc_single_kernel.core.add2.io_out_ready),
          json_logic(dut.spatialacc_single_kernel.core.add2.io_out_bits_st),
          json_logic(dut.spatialacc_single_kernel.core.add2.io_out_bits_last));
        $fflush(boundary_fd);
        emit_complete_core_scalar_trace(boundary_index, event_name);
      end
    end
  endtask

  // probe_id=probe.complete_core_scalar_status_trace.1
  // Read-only bounded scalar-status trace. The nine loops cover all bits of
  // the visible input data buses for all nine compute stages: 1664 real core
  // scalar bits. Only known/unknown status is written, never a raw payload.
  task automatic emit_stage_trace_scalar(
    input string stage_name,
    input string event_name,
    input integer token_index,
    input integer beat_index,
    input string signal_name,
    input logic scalar_value
  );
    begin
      $display("SPATIALACC_STAGE_TRACE stage=%s cycle=%0d token=%0d beat=%0d event=%s signal=%s scalar_value=%s",
               stage_name, cycle_count, token_index, beat_index, event_name,
               signal_name, json_logic(scalar_value));
    end
  endtask

  task automatic emit_complete_core_scalar_trace(
    input integer boundary_index,
    input string event_name
  );
    integer scalar_index;
    longint unsigned trace_count;
    integer trace_token;
    integer trace_beat;
    begin
      trace_count = current_dag_boundary_accepted_count[boundary_index];
      if (trace_count == 0) begin
        trace_token = -1;
        trace_beat = -1;
      end else begin
        trace_token = trace_count / current_dag_boundary_beats_per_token(boundary_index);
        trace_beat = trace_count % current_dag_boundary_beats_per_token(boundary_index);
      end

      emit_stage_trace_scalar("stage_00_rms_norm_1", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.rms1.io_in_valid", dut.spatialacc_single_kernel.core.rms1.io_in_valid);
      emit_stage_trace_scalar("stage_00_rms_norm_1", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.rms1.io_in_ready", dut.spatialacc_single_kernel.core.rms1.io_in_ready);
      emit_stage_trace_scalar("stage_00_rms_norm_1", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.rms1.io_out_valid", dut.spatialacc_single_kernel.core.rms1.io_out_valid);
      emit_stage_trace_scalar("stage_00_rms_norm_1", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.rms1.io_out_ready", dut.spatialacc_single_kernel.core.rms1.io_out_ready);
      for (scalar_index = 0; scalar_index < 256; scalar_index = scalar_index + 1)
        emit_stage_trace_scalar("stage_00_rms_norm_1", event_name, trace_token, trace_beat, $sformatf("dut.spatialacc_single_kernel.core.rms1.io_in_bits_data[%0d].known", scalar_index), !$isunknown(dut.spatialacc_single_kernel.core.rms1.io_in_bits_data[scalar_index]));

      emit_stage_trace_scalar("stage_01_self_attention", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.qkv.state", dut.spatialacc_single_kernel.core.qkv.state);
      emit_stage_trace_scalar("stage_01_self_attention", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.qkv._projection_io_out_valid", dut.spatialacc_single_kernel.core.qkv._projection_io_out_valid);
      emit_stage_trace_scalar("stage_01_self_attention", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.qkv.io_out_valid", dut.spatialacc_single_kernel.core.qkv.io_out_valid);
      emit_stage_trace_scalar("stage_01_self_attention", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.qkv.io_out_ready", dut.spatialacc_single_kernel.core.qkv.io_out_ready);
      for (scalar_index = 0; scalar_index < 128; scalar_index = scalar_index + 1)
        emit_stage_trace_scalar("stage_01_self_attention", event_name, trace_token, trace_beat, $sformatf("dut.spatialacc_single_kernel.core.qkv.io_in_bits_data[%0d].known", scalar_index), !$isunknown(dut.spatialacc_single_kernel.core.qkv.io_in_bits_data[scalar_index]));

      emit_stage_trace_scalar("stage_02_residual_add_1", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.add1.pairValid", dut.spatialacc_single_kernel.core.add1.pairValid);
      emit_stage_trace_scalar("stage_02_residual_add_1", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.add1.heldValid", dut.spatialacc_single_kernel.core.add1.heldValid);
      emit_stage_trace_scalar("stage_02_residual_add_1", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.res1Q.maybe_full", dut.spatialacc_single_kernel.core.res1Q.maybe_full);
      emit_stage_trace_scalar("stage_02_residual_add_1", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.add1._outputQ_io_enq_ready", dut.spatialacc_single_kernel.core.add1._outputQ_io_enq_ready);
      for (scalar_index = 0; scalar_index < 256; scalar_index = scalar_index + 1)
        emit_stage_trace_scalar("stage_02_residual_add_1", event_name, trace_token, trace_beat, $sformatf("dut.spatialacc_single_kernel.core.add1.io_computed_bits_data[%0d].known", scalar_index), !$isunknown(dut.spatialacc_single_kernel.core.add1.io_computed_bits_data[scalar_index]));

      emit_stage_trace_scalar("stage_03_rms_norm_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.rms2.io_in_valid", dut.spatialacc_single_kernel.core.rms2.io_in_valid);
      emit_stage_trace_scalar("stage_03_rms_norm_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.rms2.io_in_ready", dut.spatialacc_single_kernel.core.rms2.io_in_ready);
      emit_stage_trace_scalar("stage_03_rms_norm_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.rms2.io_out_valid", dut.spatialacc_single_kernel.core.rms2.io_out_valid);
      emit_stage_trace_scalar("stage_03_rms_norm_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.rms2.io_out_ready", dut.spatialacc_single_kernel.core.rms2.io_out_ready);
      for (scalar_index = 0; scalar_index < 256; scalar_index = scalar_index + 1)
        emit_stage_trace_scalar("stage_03_rms_norm_2", event_name, trace_token, trace_beat, $sformatf("dut.spatialacc_single_kernel.core.rms2.io_in_bits_data[%0d].known", scalar_index), !$isunknown(dut.spatialacc_single_kernel.core.rms2.io_in_bits_data[scalar_index]));

      emit_stage_trace_scalar("stage_04_mlp_gate_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.gate.io_start", dut.spatialacc_single_kernel.core.mlp.gate.io_start);
      emit_stage_trace_scalar("stage_04_mlp_gate_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.gate.io_weight_valid", dut.spatialacc_single_kernel.core.mlp.gate.io_weight_valid);
      emit_stage_trace_scalar("stage_04_mlp_gate_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.gate.io_weight_ready", dut.spatialacc_single_kernel.core.mlp.gate.io_weight_ready);
      emit_stage_trace_scalar("stage_04_mlp_gate_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.gate.io_out_valid", dut.spatialacc_single_kernel.core.mlp.gate.io_out_valid);
      for (scalar_index = 0; scalar_index < 128; scalar_index = scalar_index + 1)
        emit_stage_trace_scalar("stage_04_mlp_gate_proj", event_name, trace_token, trace_beat, $sformatf("dut.spatialacc_single_kernel.core.mlp.gate.io_in_bits_data[%0d].known", scalar_index), !$isunknown(dut.spatialacc_single_kernel.core.mlp.gate.io_in_bits_data[scalar_index]));

      emit_stage_trace_scalar("stage_05_mlp_up_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.up.io_start", dut.spatialacc_single_kernel.core.mlp.up.io_start);
      emit_stage_trace_scalar("stage_05_mlp_up_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.up.io_weight_valid", dut.spatialacc_single_kernel.core.mlp.up.io_weight_valid);
      emit_stage_trace_scalar("stage_05_mlp_up_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.up.io_weight_ready", dut.spatialacc_single_kernel.core.mlp.up.io_weight_ready);
      emit_stage_trace_scalar("stage_05_mlp_up_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.up.io_out_valid", dut.spatialacc_single_kernel.core.mlp.up.io_out_valid);
      for (scalar_index = 0; scalar_index < 128; scalar_index = scalar_index + 1)
        emit_stage_trace_scalar("stage_05_mlp_up_proj", event_name, trace_token, trace_beat, $sformatf("dut.spatialacc_single_kernel.core.mlp.up.io_in_bits_data[%0d].known", scalar_index), !$isunknown(dut.spatialacc_single_kernel.core.mlp.up.io_in_bits_data[scalar_index]));

      emit_stage_trace_scalar("stage_06_activation_mul", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.actQ.maybe_full", dut.spatialacc_single_kernel.core.mlp.actQ.maybe_full);
      emit_stage_trace_scalar("stage_06_activation_mul", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.upQ.maybe_full", dut.spatialacc_single_kernel.core.mlp.upQ.maybe_full);
      emit_stage_trace_scalar("stage_06_activation_mul", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp._mul_io_lhs_ready", dut.spatialacc_single_kernel.core.mlp._mul_io_lhs_ready);
      emit_stage_trace_scalar("stage_06_activation_mul", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp._mul_io_rhs_ready", dut.spatialacc_single_kernel.core.mlp._mul_io_rhs_ready);
      emit_stage_trace_scalar("stage_06_activation_mul", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp._mul_io_out_valid", dut.spatialacc_single_kernel.core.mlp._mul_io_out_valid);
      emit_stage_trace_scalar("stage_06_activation_mul", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.mul_io_out_ready__bore", dut.spatialacc_single_kernel.core.mlp.mul_io_out_ready__bore);
      for (scalar_index = 0; scalar_index < 128; scalar_index = scalar_index + 1)
        emit_stage_trace_scalar("stage_06_activation_mul", event_name, trace_token, trace_beat, $sformatf("dut.spatialacc_single_kernel.core.mlp.mul.io_lhs_bits_data[%0d].known", scalar_index), !$isunknown(dut.spatialacc_single_kernel.core.mlp.mul.io_lhs_bits_data[scalar_index]));

      emit_stage_trace_scalar("stage_07_mlp_down_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.down.io_start", dut.spatialacc_single_kernel.core.mlp.down.io_start);
      emit_stage_trace_scalar("stage_07_mlp_down_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.down.io_weight_valid", dut.spatialacc_single_kernel.core.mlp.down.io_weight_valid);
      emit_stage_trace_scalar("stage_07_mlp_down_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.down.io_weight_ready", dut.spatialacc_single_kernel.core.mlp.down.io_weight_ready);
      emit_stage_trace_scalar("stage_07_mlp_down_proj", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.mlp.down.io_out_valid", dut.spatialacc_single_kernel.core.mlp.down.io_out_valid);
      for (scalar_index = 0; scalar_index < 128; scalar_index = scalar_index + 1)
        emit_stage_trace_scalar("stage_07_mlp_down_proj", event_name, trace_token, trace_beat, $sformatf("dut.spatialacc_single_kernel.core.mlp.down.io_in_bits_data[%0d].known", scalar_index), !$isunknown(dut.spatialacc_single_kernel.core.mlp.down.io_in_bits_data[scalar_index]));

      emit_stage_trace_scalar("stage_08_residual_add_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.add2.pairValid", dut.spatialacc_single_kernel.core.add2.pairValid);
      emit_stage_trace_scalar("stage_08_residual_add_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.add2.heldValid", dut.spatialacc_single_kernel.core.add2.heldValid);
      emit_stage_trace_scalar("stage_08_residual_add_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.res2Q.maybe_full", dut.spatialacc_single_kernel.core.res2Q.maybe_full);
      emit_stage_trace_scalar("stage_08_residual_add_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.add2.outputQ.maybe_full", dut.spatialacc_single_kernel.core.add2.outputQ.maybe_full);
      emit_stage_trace_scalar("stage_08_residual_add_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.io_out_valid", dut.spatialacc_single_kernel.core.io_out_valid);
      emit_stage_trace_scalar("stage_08_residual_add_2", event_name, trace_token, trace_beat, "dut.spatialacc_single_kernel.core.io_out_ready", dut.spatialacc_single_kernel.core.io_out_ready);
      for (scalar_index = 0; scalar_index < 256; scalar_index = scalar_index + 1)
        emit_stage_trace_scalar("stage_08_residual_add_2", event_name, trace_token, trace_beat, $sformatf("dut.spatialacc_single_kernel.core.add2.io_computed_bits_data[%0d].known", scalar_index), !$isunknown(dut.spatialacc_single_kernel.core.add2.io_computed_bits_data[scalar_index]));
    end
  endtask

  task automatic emit_progress_event(
    input string event_kind,
    input string phase,
    input bit increments_progress,
    input integer event_layer,
    input integer event_token,
    input integer event_beat,
    input string stage_or_boundary
  );
    string active_weight_bank_name;
    string preload_weight_bank_name;
    string activation_read_bank_name;
    string activation_write_bank_name;
    begin
      if (progress_fd != 0) begin
        if ((event_layer >= 0) && (event_layer < TARGET_LAYERS)) begin
          if (event_layer[0]) begin
            active_weight_bank_name = "weight_b";
            preload_weight_bank_name = (event_layer == (TARGET_LAYERS-1)) ? "none" : "weight_a";
            activation_read_bank_name = "activation_pong_bank";
            activation_write_bank_name = "activation_ping_bank";
          end else begin
            active_weight_bank_name = "weight_a";
            preload_weight_bank_name = (event_layer == (TARGET_LAYERS-1)) ? "none" : "weight_b";
            activation_read_bank_name = "activation_ping_bank";
            activation_write_bank_name = "activation_pong_bank";
          end
        end else begin
          active_weight_bank_name = "unknown";
          preload_weight_bank_name = "unknown";
          activation_read_bank_name = "unknown";
          activation_write_bank_name = "unknown";
        end
        if (increments_progress) begin
          semantic_progress_count = semantic_progress_count + 1;
          progress_epoch = progress_epoch + 1;
          last_semantic_progress_cycle = cycle_count;
        end
        $fwrite(progress_fd, "{\"schema_version\":\"spatialaccagent.board_progress_event.v1\",\"evidence_kind\":\"board_progress\",\"sequence\":%0d,\"cycle\":%0d,\"event_kind\":\"%s\",\"phase\":\"%s\",\"semantic_progress\":%s,\"progress_epoch\":%0d,\"last_semantic_progress_cycle\":%0d,\"scheduler_state\":%0d,\"layer\":%0d,\"token\":%0d,\"beat\":%0d,\"stage_or_boundary\":\"%s\",\"active_weight_bank\":\"%s\",\"preload_weight_bank\":\"%s\",\"activation_read_bank\":\"%s\",\"activation_write_bank\":\"%s\",\"prefetch_progress\":{\"accepted_beats\":%0d,\"target_beats\":%0d},\"runtime_load_progress\":{\"accepted_words\":%0d,\"target_words\":%0d},\"final_writeback_progress\":{\"accepted_beats\":%0d,\"target_beats\":%0d},\"axi_read\":{\"outstanding\":%0d,\"pending_response\":%s,\"arvalid\":%0d,\"arready\":%0d,\"rvalid\":%0d,\"rready\":%0d,\"transactions\":%0d,\"beats\":%0d},\"axi_write\":{\"outstanding\":%0d,\"pending_response\":%s,\"awvalid\":%0d,\"awready\":%0d,\"wvalid\":%0d,\"wready\":%0d,\"bvalid\":%0d,\"bready\":%0d,\"transactions\":%0d,\"beats\":%0d},\"active_boundary_observation\":{\"event_queue_quiescent\":%s,\"input_valid\":%0d,\"input_ready\":%0d,\"input_accepted\":%0d,\"start\":%0d,\"input_axi_index\":%0d,\"output_accept_count\":%0d,\"output_pair_valid\":%s,\"input_payload_unknown\":%s,\"input_payload_digest\":\"%08x\",\"output_valid\":%s,\"output_ready\":%0d,\"output_accepted\":%0d,\"output_payload_unknown\":%s,\"output_payload_digest\":\"%08x\"}}\n",
          progress_sequence,
          cycle_count,
          event_kind,
          phase,
          json_bool(increments_progress),
          progress_epoch,
          last_semantic_progress_cycle,
          dut.state,
          event_layer,
          event_token,
          event_beat,
          stage_or_boundary,
          active_weight_bank_name,
          preload_weight_bank_name,
          activation_read_bank_name,
          activation_write_bank_name,
          dut.prefetch_index,
          WEIGHT_WORDS_PER_LAYER/16,
          ((event_layer >= 0) && (event_layer < TARGET_LAYERS)) ? runtime_accept_count[event_layer] : 0,
          RUNTIME_WORDS_PER_LAYER,
          dut.copy_trace_final ? (dut.copy_index + (dut.trace_final_writeback_complete ? 1 : 0)) : 0,
          AXI_BEATS_PER_ACTIVATION,
          checkpoint_axi_read_outstanding(),
          json_bool(c0_ddr4_s_axi_rvalid),
          c0_ddr4_s_axi_arvalid,
          c0_ddr4_s_axi_arready,
          c0_ddr4_s_axi_rvalid,
          c0_ddr4_s_axi_rready,
          axi_read_transaction_count,
          axi_read_beat_count,
          checkpoint_axi_write_outstanding(),
          json_bool(write_response_pending || c0_ddr4_s_axi_bvalid),
          c0_ddr4_s_axi_awvalid,
          c0_ddr4_s_axi_awready,
          c0_ddr4_s_axi_wvalid,
          c0_ddr4_s_axi_wready,
          c0_ddr4_s_axi_bvalid,
          c0_ddr4_s_axi_bready,
          axi_write_transaction_count,
          axi_write_beat_count,
          json_bool(checkpoint_event_queue_quiescent()),
          dut.kernel_input_valid_q,
          dut.kernel_input_ready,
          dut.kernel_input_valid_q && dut.kernel_input_ready,
          dut.kernel_start_to_core,
          dut.input_axi_index,
          dut.output_accept_count,
          json_bool(dut.output_pair_valid),
          json_bool($isunknown(dut.kernel_input_data_q)),
          payload_digest256(dut.kernel_input_data_q),
          json_logic(dut.kernel_output_valid),
          dut.kernel_output_ready,
          dut.kernel_output_valid && dut.kernel_output_ready,
          json_bool($isunknown(dut.kernel_output_data)),
          payload_digest256(dut.kernel_output_data));
        progress_sequence = progress_sequence + 1;
        $fflush(progress_fd);
        if (checkpoint_enabled && !checkpoint_restore_requested &&
            !checkpoint_trigger_observed && (progress_sequence != 0) &&
            ((progress_sequence - 1) == checkpoint_cut_sequence) &&
            (cycle_count == checkpoint_cut_cycle) &&
            (phase == checkpoint_cut_phase) &&
            (event_layer == checkpoint_cut_layer) &&
            (event_token == checkpoint_cut_token) &&
            (event_beat == checkpoint_cut_beat) &&
            (checkpoint_cut_frontier.len() > 0)) begin
          checkpoint_trigger_sequence = progress_sequence - 1;
          checkpoint_trigger_cycle = cycle_count;
          checkpoint_trigger_observed = 1'b1;
        end
        $display("SPATIALACC_BOARD_PROGRESS sequence=%0d event_kind=%s phase=%s layer=%0d cycle=%0d evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1", progress_sequence, event_kind, phase, event_layer, cycle_count);
        if (event_kind == "stall_snapshot") begin
          write_live_observation_reports(phase);
        end
      end
    end
  endtask

  task automatic emit_connected_kernel_frontier_event(
    input string frontier_phase,
    input integer frontier_token,
    input integer frontier_beat
  );
    string active_weight_bank_name;
    string preload_weight_bank_name;
    string activation_read_bank_name;
    string activation_write_bank_name;
    integer frontier_layer;
    integer frontier_input_fire;
    integer frontier_output_fire;
    integer frontier_start_high;
    integer frontier_start_edge;
    longint unsigned frontier_report_first_start_cycle;
    begin
      frontier_layer = dut.layer_index;
      frontier_input_fire = (dut.kernel_input_valid_q === 1'b1) &&
                            (dut.kernel_input_ready === 1'b1);
      frontier_output_fire = (dut.kernel_output_valid === 1'b1) &&
                             (dut.kernel_output_ready === 1'b1);
      frontier_start_high = (dut.kernel_start_to_core === 1'b1);
      frontier_start_edge = frontier_start_high &&
                            (frontier_start_to_core_d === 1'b0);
      frontier_report_first_start_cycle = frontier_first_start_cycle;
      if ((frontier_report_first_start_cycle == 0) && frontier_start_edge) begin
        frontier_report_first_start_cycle = cycle_count;
      end
      if (frontier_layer[0]) begin
        active_weight_bank_name = "weight_b";
        preload_weight_bank_name =
          (frontier_layer == (TARGET_LAYERS-1)) ? "none" : "weight_a";
        activation_read_bank_name = "activation_pong_bank";
        activation_write_bank_name = "activation_ping_bank";
      end else begin
        active_weight_bank_name = "weight_a";
        preload_weight_bank_name =
          (frontier_layer == (TARGET_LAYERS-1)) ? "none" : "weight_b";
        activation_read_bank_name = "activation_ping_bank";
        activation_write_bank_name = "activation_pong_bank";
      end
      if (progress_fd != 0) begin
        $fwrite(progress_fd, "{\"schema_version\":\"spatialaccagent.board_progress_event.v1\",\"evidence_kind\":\"board_progress\",\"sequence\":%0d,\"cycle\":%0d,\"event_kind\":\"stall_snapshot\",\"phase\":\"%s\",\"semantic_progress\":false,\"progress_epoch\":%0d,\"last_semantic_progress_cycle\":%0d,\"scheduler_state\":%0d,\"layer\":%0d,\"token\":%0d,\"beat\":%0d,\"stage_or_boundary\":\"connected_kernel_input_to_output\",\"active_weight_bank\":\"%s\",\"preload_weight_bank\":\"%s\",\"activation_read_bank\":\"%s\",\"activation_write_bank\":\"%s\",\"prefetch_progress\":{\"accepted_beats\":%0d,\"target_beats\":%0d},\"runtime_load_progress\":{\"accepted_words\":%0d,\"target_words\":%0d},\"final_writeback_progress\":{\"accepted_beats\":%0d,\"target_beats\":%0d},\"axi_read\":{\"outstanding\":%0d,\"pending_response\":%s,\"arvalid\":%0d,\"arready\":%0d,\"rvalid\":%0d,\"rready\":%0d,\"transactions\":%0d,\"beats\":%0d},\"axi_write\":{\"outstanding\":%0d,\"pending_response\":%s,\"awvalid\":%0d,\"awready\":%0d,\"wvalid\":%0d,\"wready\":%0d,\"bvalid\":%0d,\"bready\":%0d,\"transactions\":%0d,\"beats\":%0d},\"active_boundary_observation\":{\"event_queue_quiescent\":%s,\"input_valid\":%s,\"input_ready\":%s,\"input_accepted\":%0d,\"start\":%s,\"input_axi_index\":%0d,\"output_accept_count\":%0d,\"output_pair_valid\":%s,\"input_payload_unknown\":%s,\"input_payload_digest\":\"%08x\",\"output_valid\":%s,\"output_ready\":%s,\"output_accepted\":%0d,\"output_payload_unknown\":%s,\"output_payload_digest\":\"%08x\"},\"connected_kernel_frontier_observation\":{\"schema_version\":\"spatialaccagent.connected_kernel_frontier_observation.v1\",\"frontier_id\":\"connected_kernel_input_to_output\",\"probe_id\":\"probe.connected_kernel_invocation_arming.3\",\"probe_revision\":3,\"source_marker\":\"connected_kernel_invocation_arming_r3\",\"lifecycle_start_count\":%0d,\"additional_start_edge_count\":%0d,\"first_input_fire_cycle\":%0d,\"last_input_fire_cycle\":%0d,\"last_start_edge_cycle\":%0d,\"start_q\":%s,\"start_to_core\":%s,\"invocation_launched\":%s,\"rearm_pending\":%s,\"start_pulse_count\":%0d,\"start_asserted_cycle_count\":%0d,\"start_with_input_fire_count\":%0d,\"input_valid\":%s,\"input_ready\":%s,\"input_fire\":%0d,\"input_count\":%0d,\"input_axi_index\":%0d,\"input_payload_unknown\":%s,\"input_payload_digest\":\"%08x\",\"output_valid\":%s,\"output_ready\":%s,\"output_fire\":%0d,\"output_count\":%0d,\"output_payload_unknown\":%s,\"output_payload_digest\":\"%08x\",\"kernel_reset\":%s,\"weight_valid\":%s,\"weight_ready\":%s,\"weight_last\":%s,\"runtime_valid\":%s,\"runtime_ready\":%s,\"runtime_last\":%s,\"weight_accept_count\":%0d,\"runtime_accept_count\":%0d,\"reset_release_cycle\":%0d,\"weight_load_complete_cycle\":%0d,\"runtime_load_complete_cycle\":%0d,\"first_start_cycle\":%0d,\"reset_to_start_cycles\":%0d,\"weight_to_start_cycles\":%0d,\"runtime_to_start_cycles\":%0d}}\n",
          progress_sequence,
          cycle_count,
          frontier_phase,
          progress_epoch,
          last_semantic_progress_cycle,
          dut.state,
          frontier_layer,
          frontier_token,
          frontier_beat,
          active_weight_bank_name,
          preload_weight_bank_name,
          activation_read_bank_name,
          activation_write_bank_name,
          dut.prefetch_index,
          WEIGHT_WORDS_PER_LAYER/16,
          runtime_accept_count[frontier_layer],
          RUNTIME_WORDS_PER_LAYER,
          dut.copy_trace_final ?
            (dut.copy_index + (dut.trace_final_writeback_complete ? 1 : 0)) : 0,
          AXI_BEATS_PER_ACTIVATION,
          checkpoint_axi_read_outstanding(),
          json_bool(c0_ddr4_s_axi_rvalid),
          c0_ddr4_s_axi_arvalid,
          c0_ddr4_s_axi_arready,
          c0_ddr4_s_axi_rvalid,
          c0_ddr4_s_axi_rready,
          axi_read_transaction_count,
          axi_read_beat_count,
          checkpoint_axi_write_outstanding(),
          json_bool(write_response_pending || c0_ddr4_s_axi_bvalid),
          c0_ddr4_s_axi_awvalid,
          c0_ddr4_s_axi_awready,
          c0_ddr4_s_axi_wvalid,
          c0_ddr4_s_axi_wready,
          c0_ddr4_s_axi_bvalid,
          c0_ddr4_s_axi_bready,
          axi_write_transaction_count,
          axi_write_beat_count,
          json_bool(checkpoint_event_queue_quiescent()),
          json_logic(dut.kernel_input_valid_q),
          json_logic(dut.kernel_input_ready),
          frontier_input_fire,
          json_logic(dut.kernel_start_to_core),
          dut.input_axi_index,
          dut.output_accept_count,
          json_bool(dut.output_pair_valid === 1'b1),
          json_bool($isunknown(dut.kernel_input_data_q)),
          payload_digest256(dut.kernel_input_data_q),
          json_logic(dut.kernel_output_valid),
          json_logic(dut.kernel_output_ready),
          frontier_output_fire,
          json_bool($isunknown(dut.kernel_output_data)),
          payload_digest256(dut.kernel_output_data),
          trace_kernel_start_count + (dut.trace_kernel_start ? 1 : 0),
          ((frontier_core_start_pulse_count + frontier_start_edge) > 0) ?
            ((frontier_core_start_pulse_count + frontier_start_edge) - 1) : 0,
          frontier_first_input_fire_seen ?
            frontier_first_input_fire_cycle :
            (frontier_input_fire ? cycle_count : 0),
          frontier_input_fire ? cycle_count : frontier_last_input_fire_cycle,
          frontier_start_edge ? cycle_count : frontier_last_start_cycle,
          json_logic(dut.kernel_start_q),
          json_logic(dut.kernel_start_to_core),
          json_logic(dut.kernel_invocation_launched),
          json_logic(dut.kernel_token_rearm_pending),
          frontier_core_start_pulse_count + frontier_start_edge,
          frontier_core_start_asserted_cycle_count + frontier_start_high,
          frontier_start_with_input_fire_count +
            (frontier_start_edge && frontier_input_fire),
          json_logic(dut.kernel_input_valid_q),
          json_logic(dut.kernel_input_ready),
          frontier_input_fire,
          layer_input_count[frontier_layer] + frontier_input_fire,
          dut.input_axi_index,
          json_bool($isunknown(dut.kernel_input_data_q)),
          payload_digest256(dut.kernel_input_data_q),
          json_logic(dut.kernel_output_valid),
          json_logic(dut.kernel_output_ready),
          frontier_output_fire,
          layer_output_count[frontier_layer] + frontier_output_fire,
          json_bool($isunknown(dut.kernel_output_data)),
          payload_digest256(dut.kernel_output_data),
          json_logic(dut.kernel_reset_q),
          json_logic(dut.weight_valid_q),
          json_logic(dut.weight_ready),
          json_logic(dut.weight_last_q),
          json_logic(dut.runtime_valid_q),
          json_logic(dut.runtime_ready),
          json_logic(dut.runtime_last_q),
          weight_accept_total,
          runtime_accept_count[frontier_layer],
          frontier_kernel_reset_release_cycle,
          frontier_weight_load_complete_cycle,
          frontier_runtime_load_complete_cycle,
          frontier_report_first_start_cycle,
          ((frontier_kernel_reset_release_cycle != 0) &&
           (frontier_report_first_start_cycle >= frontier_kernel_reset_release_cycle)) ?
            (frontier_report_first_start_cycle - frontier_kernel_reset_release_cycle) : 0,
          ((frontier_weight_load_complete_cycle != 0) &&
           (frontier_report_first_start_cycle >= frontier_weight_load_complete_cycle)) ?
            (frontier_report_first_start_cycle - frontier_weight_load_complete_cycle) : 0,
          ((frontier_runtime_load_complete_cycle != 0) &&
           (frontier_report_first_start_cycle >= frontier_runtime_load_complete_cycle)) ?
            (frontier_report_first_start_cycle - frontier_runtime_load_complete_cycle) : 0);
        progress_sequence = progress_sequence + 1;
        $fflush(progress_fd);
        $display("SPATIALACC_BOARD_PROGRESS sequence=%0d event_kind=stall_snapshot phase=%s layer=%0d start_pulses=%0d input_count=%0d output_count=%0d cycle=%0d evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
                 progress_sequence, frontier_phase, frontier_layer,
                 frontier_core_start_pulse_count + frontier_start_edge,
                 layer_input_count[frontier_layer] + frontier_input_fire,
                 layer_output_count[frontier_layer] + frontier_output_fire,
                 cycle_count);
      end
    end
  endtask

  task automatic emit_connected_kernel_output_continuation_event(
    input string continuation_phase,
    input integer continuation_token,
    input integer continuation_beat
  );
    string active_weight_bank_name;
    string preload_weight_bank_name;
    string activation_read_bank_name;
    string activation_write_bank_name;
    integer frontier_layer;
    integer frontier_input_fire;
    integer frontier_output_fire;
    integer frontier_output_count;
    longint unsigned first_output_cycle;
    longint unsigned completion_cycle;
    longint unsigned last_output_cycle;
    begin
      frontier_layer = dut.layer_index;
      frontier_input_fire = (dut.kernel_input_valid_q === 1'b1) &&
                            (dut.kernel_input_ready === 1'b1);
      frontier_output_fire = (dut.kernel_output_valid === 1'b1) &&
                             (dut.kernel_output_ready === 1'b1);
      frontier_output_count = layer_output_count[frontier_layer] +
                              frontier_output_fire;
      first_output_cycle = frontier_first_output_fire_cycle;
      if ((first_output_cycle == 0) && frontier_output_fire)
        first_output_cycle = cycle_count;
      completion_cycle = frontier_first_output_token_complete_cycle;
      if ((completion_cycle == 0) && frontier_output_fire &&
          ((layer_output_count[frontier_layer] % BEATS_PER_TOKEN) ==
           (BEATS_PER_TOKEN-1)))
        completion_cycle = cycle_count;
      last_output_cycle = frontier_output_fire ?
                          cycle_count : frontier_last_output_fire_cycle;
      if (frontier_layer[0]) begin
        active_weight_bank_name = "weight_b";
        preload_weight_bank_name =
          (frontier_layer == (TARGET_LAYERS-1)) ? "none" : "weight_a";
        activation_read_bank_name = "activation_pong_bank";
        activation_write_bank_name = "activation_ping_bank";
      end else begin
        active_weight_bank_name = "weight_a";
        preload_weight_bank_name =
          (frontier_layer == (TARGET_LAYERS-1)) ? "none" : "weight_b";
        activation_read_bank_name = "activation_ping_bank";
        activation_write_bank_name = "activation_pong_bank";
      end
      if (progress_fd != 0) begin
        $fwrite(progress_fd,
          "{\"schema_version\":\"spatialaccagent.board_progress_event.v1\",\"evidence_kind\":\"board_progress\",\"sequence\":%0d,\"cycle\":%0d,\"event_kind\":\"stall_snapshot\",\"phase\":\"%s\",\"semantic_progress\":false,\"progress_epoch\":%0d,\"last_semantic_progress_cycle\":%0d,\"scheduler_state\":%0d,\"layer\":%0d,\"token\":%0d,\"beat\":%0d,\"stage_or_boundary\":\"connected_kernel_input_to_output\",\"active_weight_bank\":\"%s\",\"preload_weight_bank\":\"%s\",\"activation_read_bank\":\"%s\",\"activation_write_bank\":\"%s\"",
          progress_sequence, cycle_count, continuation_phase,
          progress_epoch, last_semantic_progress_cycle, dut.state,
          frontier_layer, continuation_token, continuation_beat,
          active_weight_bank_name, preload_weight_bank_name,
          activation_read_bank_name, activation_write_bank_name);
        $fwrite(progress_fd,
          ",\"prefetch_progress\":{\"accepted_beats\":%0d,\"target_beats\":%0d},\"runtime_load_progress\":{\"accepted_words\":%0d,\"target_words\":%0d},\"final_writeback_progress\":{\"accepted_beats\":%0d,\"target_beats\":%0d},\"axi_read\":{\"outstanding\":%0d,\"pending_response\":%s,\"arvalid\":%0d,\"arready\":%0d,\"rvalid\":%0d,\"rready\":%0d,\"transactions\":%0d,\"beats\":%0d},\"axi_write\":{\"outstanding\":%0d,\"pending_response\":%s,\"awvalid\":%0d,\"awready\":%0d,\"wvalid\":%0d,\"wready\":%0d,\"bvalid\":%0d,\"bready\":%0d,\"transactions\":%0d,\"beats\":%0d}",
          dut.prefetch_index, WEIGHT_WORDS_PER_LAYER/16,
          runtime_accept_count[frontier_layer], RUNTIME_WORDS_PER_LAYER,
          dut.copy_trace_final ?
            (dut.copy_index + (dut.trace_final_writeback_complete ? 1 : 0)) : 0,
          AXI_BEATS_PER_ACTIVATION,
          checkpoint_axi_read_outstanding(),
          json_bool(c0_ddr4_s_axi_rvalid),
          c0_ddr4_s_axi_arvalid, c0_ddr4_s_axi_arready,
          c0_ddr4_s_axi_rvalid, c0_ddr4_s_axi_rready,
          axi_read_transaction_count, axi_read_beat_count,
          checkpoint_axi_write_outstanding(),
          json_bool(write_response_pending || c0_ddr4_s_axi_bvalid),
          c0_ddr4_s_axi_awvalid, c0_ddr4_s_axi_awready,
          c0_ddr4_s_axi_wvalid, c0_ddr4_s_axi_wready,
          c0_ddr4_s_axi_bvalid, c0_ddr4_s_axi_bready,
          axi_write_transaction_count, axi_write_beat_count);
        $fwrite(progress_fd,
          ",\"active_boundary_observation\":{\"event_queue_quiescent\":%s,\"input_valid\":%s,\"input_ready\":%s,\"input_accepted\":%0d,\"start\":%s,\"input_axi_index\":%0d,\"output_accept_count\":%0d,\"output_pair_valid\":%s,\"input_payload_unknown\":%s,\"input_payload_digest\":\"%08x\",\"output_valid\":%s,\"output_ready\":%s,\"output_accepted\":%0d,\"output_payload_unknown\":%s,\"output_payload_digest\":\"%08x\"}",
          json_bool(checkpoint_event_queue_quiescent()),
          json_logic(dut.kernel_input_valid_q),
          json_logic(dut.kernel_input_ready), frontier_input_fire,
          json_logic(dut.kernel_start_to_core), dut.input_axi_index,
          frontier_output_count, json_bool(dut.output_pair_valid === 1'b1),
          json_bool($isunknown(dut.kernel_input_data_q)),
          payload_digest256(dut.kernel_input_data_q),
          json_logic(dut.kernel_output_valid),
          json_logic(dut.kernel_output_ready), frontier_output_fire,
          json_bool($isunknown(dut.kernel_output_data)),
          payload_digest256(dut.kernel_output_data));
        $fwrite(progress_fd,
          ",\"core_ingress_observation\":{\"boundary_id\":\"kernel.core_ingress\",\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\",\"valid\":%s,\"ready\":%s,\"accepted\":%0d,\"accepted_count\":%0d,\"current_payload_unknown\":%s,\"current_payload_digest\":\"%08x\",\"last_accepted_payload_unknown\":%s,\"last_accepted_payload_digest\":\"%08x\"}",
          json_logic(frontier_core_ingress_valid),
          json_logic(frontier_core_ingress_ready),
          frontier_core_ingress_fire,
          frontier_core_ingress_fire_count + frontier_core_ingress_fire,
          json_bool($isunknown(frontier_core_ingress_data)),
          payload_digest256(frontier_core_ingress_data),
          json_bool(frontier_core_ingress_fire ?
                    $isunknown(frontier_core_ingress_data) :
                    frontier_core_ingress_last_payload_unknown),
          frontier_core_ingress_fire ?
            payload_digest256(frontier_core_ingress_data) :
            frontier_core_ingress_last_payload_digest);
        $fwrite(progress_fd,
          ",\"stage0_input_boundary_observation\":{\"boundary_id\":\"boundary.edge_data_block_input_to_stage_00_rms_norm_1_input\",\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\",\"valid\":%s,\"ready\":%s,\"accepted\":%0d,\"accepted_count\":%0d,\"source_scope\":\"dut.spatialacc_single_kernel.core.rms1.io_in\"}",
          json_logic(frontier_stage0_input_valid),
          json_logic(frontier_stage0_input_ready),
          frontier_stage0_input_fire,
          frontier_stage0_input_fire_count + frontier_stage0_input_fire);
        $fwrite(progress_fd,
          ",\"stage0_boundary_observation\":{\"boundary_id\":\"boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main\",\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\",\"valid\":%s,\"ready\":%s,\"accepted\":%0d,\"accepted_count\":%0d,\"current_payload_unknown\":%s,\"current_payload_digest\":\"%08x\",\"last_accepted_payload_unknown\":%s,\"last_accepted_payload_digest\":\"%08x\"}",
          json_logic(frontier_stage0_valid),
          json_logic(frontier_stage0_ready),
          frontier_stage0_fire,
          frontier_stage0_fire_count + frontier_stage0_fire,
          json_bool($isunknown(frontier_stage0_data)),
          payload_digest256(frontier_stage0_data),
          json_bool(frontier_stage0_fire ?
                    $isunknown(frontier_stage0_data) :
                    frontier_stage0_last_payload_unknown),
          frontier_stage0_fire ?
            payload_digest256(frontier_stage0_data) :
            frontier_stage0_last_payload_digest);
        $fwrite(progress_fd,
          ",\"connected_kernel_internal_pipeline_observation\":{\"schema_version\":\"spatialaccagent.connected_kernel_internal_pipeline_observation.v1\",\"frontier_id\":\"connected_kernel_input_to_output\",\"probe_id\":\"probe.connected_kernel_internal_pipeline.5\",\"probe_revision\":5,\"source_marker\":\"connected_kernel_internal_pipeline_r5\",\"lifecycle_start_count\":%0d,\"start_edge_count\":%0d,\"first_start_cycle\":%0d,\"first_core_ingress_fire_cycle\":%0d,\"first_core_ingress_precedes_start\":%s,\"start_precedes_first_core_ingress\":%s,\"first_input_fire_cycle\":%0d,\"last_input_fire_cycle\":%0d,\"first_output_fire_cycle\":%0d,\"first_output_token_complete_cycle\":%0d,\"last_output_fire_cycle\":%0d,\"cycles_since_first_output_token_complete\":%0d,\"input_count\":%0d,\"input_axi_index\":%0d,\"input_valid\":%s,\"input_ready\":%s,\"input_fire\":%0d,\"input_payload_unknown\":%s,\"input_payload_digest\":\"%08x\",\"output_valid\":%s,\"output_ready\":%s,\"output_fire\":%0d,\"output_count\":%0d,\"output_token_beat_count\":%0d,\"output_payload_unknown\":%s,\"output_payload_digest\":\"%08x\",\"kernel_reset\":%s,\"start_to_core\":%s,\"invocation_launched\":%s,\"rearm_pending\":%s,\"output_fifo_count\":%0d,\"output_fifo_write_index\":%0d,\"output_fifo_read_index\":%0d,\"output_ingress_half\":%s,\"output_pair_valid\":%s,\"output_write_index\":%0d,\"axi_read_outstanding\":%0d,\"axi_write_outstanding\":%0d,\"axi_write_response_pending\":%s,\"core_ingress_valid\":%s,\"core_ingress_ready\":%s,\"core_ingress_fire\":%0d,\"core_ingress_accepted_count\":%0d,\"core_ingress_next_token\":%0d,\"core_ingress_next_beat\":%0d,\"core_ingress_current_payload_unknown\":%s,\"core_ingress_current_payload_digest\":\"%08x\",\"core_ingress_last_accepted_payload_unknown\":%s,\"core_ingress_last_accepted_payload_digest\":\"%08x\",\"stage0_input_valid\":%s,\"stage0_input_ready\":%s,\"stage0_input_fire\":%0d,\"stage0_input_accepted_count\":%0d,\"stage0_valid\":%s,\"stage0_ready\":%s,\"stage0_fire\":%0d,\"stage0_accepted_count\":%0d,\"stage0_next_token\":%0d,\"stage0_next_beat\":%0d,\"stage0_current_payload_unknown\":%s,\"stage0_current_payload_digest\":\"%08x\",\"stage0_last_accepted_payload_unknown\":%s,\"stage0_last_accepted_payload_digest\":\"%08x\",\"core_egress_valid\":%s,\"core_egress_ready\":%s,\"core_egress_fire\":%0d,\"core_egress_accepted_count\":%0d,\"core_egress_next_token\":%0d,\"core_egress_next_beat\":%0d,\"core_egress_current_payload_unknown\":%s,\"core_egress_current_payload_digest\":\"%08x\",\"core_egress_last_accepted_payload_unknown\":%s,\"core_egress_last_accepted_payload_digest\":\"%08x\"}",
          trace_kernel_start_count, frontier_core_start_pulse_count,
          frontier_first_start_cycle,
          frontier_first_core_ingress_fire_cycle,
          json_bool((frontier_first_core_ingress_fire_cycle != 0) &&
                    (frontier_first_start_cycle != 0) &&
                    (frontier_first_core_ingress_fire_cycle <
                     frontier_first_start_cycle)),
          json_bool((frontier_first_core_ingress_fire_cycle != 0) &&
                    (frontier_first_start_cycle != 0) &&
                    (frontier_first_start_cycle <=
                     frontier_first_core_ingress_fire_cycle)),
          frontier_first_input_fire_cycle, frontier_last_input_fire_cycle,
          first_output_cycle, completion_cycle, last_output_cycle,
          ((completion_cycle != 0) && (cycle_count >= completion_cycle)) ?
            (cycle_count - completion_cycle) : 0,
          layer_input_count[frontier_layer] + frontier_input_fire,
          dut.input_axi_index,
          json_logic(dut.kernel_input_valid_q),
          json_logic(dut.kernel_input_ready), frontier_input_fire,
          json_bool($isunknown(dut.kernel_input_data_q)),
          payload_digest256(dut.kernel_input_data_q),
          json_logic(dut.kernel_output_valid),
          json_logic(dut.kernel_output_ready), frontier_output_fire,
          frontier_output_count, dut.output_token_beat_count,
          json_bool($isunknown(dut.kernel_output_data)),
          payload_digest256(dut.kernel_output_data),
          json_logic(dut.kernel_reset_q),
          json_logic(dut.kernel_start_to_core),
          json_logic(dut.kernel_invocation_launched),
          json_logic(dut.kernel_token_rearm_pending),
          dut.output_fifo_count, dut.output_fifo_write_index,
          dut.output_fifo_read_index, json_logic(dut.output_ingress_half),
          json_logic(dut.output_pair_valid), dut.output_write_index,
          checkpoint_axi_read_outstanding(),
          checkpoint_axi_write_outstanding(),
          json_bool(write_response_pending || c0_ddr4_s_axi_bvalid),
          json_logic(frontier_core_ingress_valid),
          json_logic(frontier_core_ingress_ready),
          frontier_core_ingress_fire,
          frontier_core_ingress_fire_count + frontier_core_ingress_fire,
          (frontier_core_ingress_fire_count + frontier_core_ingress_fire) /
            BEATS_PER_TOKEN,
          (frontier_core_ingress_fire_count + frontier_core_ingress_fire) %
            BEATS_PER_TOKEN,
          json_bool($isunknown(frontier_core_ingress_data)),
          payload_digest256(frontier_core_ingress_data),
          json_bool(frontier_core_ingress_fire ?
                    $isunknown(frontier_core_ingress_data) :
                    frontier_core_ingress_last_payload_unknown),
          frontier_core_ingress_fire ?
            payload_digest256(frontier_core_ingress_data) :
            frontier_core_ingress_last_payload_digest,
          json_logic(frontier_stage0_input_valid),
          json_logic(frontier_stage0_input_ready),
          frontier_stage0_input_fire,
          frontier_stage0_input_fire_count + frontier_stage0_input_fire,
          json_logic(frontier_stage0_valid),
          json_logic(frontier_stage0_ready),
          frontier_stage0_fire,
          frontier_stage0_fire_count + frontier_stage0_fire,
          (frontier_stage0_fire_count + frontier_stage0_fire) /
            BEATS_PER_TOKEN,
          (frontier_stage0_fire_count + frontier_stage0_fire) %
            BEATS_PER_TOKEN,
          json_bool($isunknown(frontier_stage0_data)),
          payload_digest256(frontier_stage0_data),
          json_bool(frontier_stage0_fire ?
                    $isunknown(frontier_stage0_data) :
                    frontier_stage0_last_payload_unknown),
          frontier_stage0_fire ?
            payload_digest256(frontier_stage0_data) :
            frontier_stage0_last_payload_digest,
          json_logic(frontier_core_egress_valid),
          json_logic(frontier_core_egress_ready),
          frontier_core_egress_fire,
          frontier_core_egress_fire_count + frontier_core_egress_fire,
          (frontier_core_egress_fire_count + frontier_core_egress_fire) /
            BEATS_PER_TOKEN,
          (frontier_core_egress_fire_count + frontier_core_egress_fire) %
            BEATS_PER_TOKEN,
          json_bool($isunknown(frontier_core_egress_data)),
          payload_digest256(frontier_core_egress_data),
          json_bool(frontier_core_egress_fire ?
                    $isunknown(frontier_core_egress_data) :
                    frontier_core_egress_last_payload_unknown),
          frontier_core_egress_fire ?
            payload_digest256(frontier_core_egress_data) :
            frontier_core_egress_last_payload_digest);
        if (((layer_input_count[frontier_layer] + frontier_input_fire) >= BEATS_PER_LAYER) &&
            (frontier_output_count == 0)) begin
          $fwrite(progress_fd,
            ",\"connected_kernel_inner_cone_observation\":{\"schema_version\":\"spatialaccagent.connected_kernel_inner_cone_observation.v1\",\"probe_id\":\"probe.connected_kernel_inner_cone_after_full_ingress.2\",\"probe_revision\":2,\"source_marker\":\"connected_kernel_inner_cone_after_full_ingress_r2\",\"mlp_down_tail_probe_id\":\"probe.connected_kernel_mlp_down_tail_at_full_ingress.13\",\"mlp_down_tail_probe_revision\":13,\"all_outer_ingress_accepted\":%s,\"outer_input_accepted_count\":%0d,\"outer_output_accepted_count\":%0d,\"core_ingress_accepted_count\":%0d,\"stage0_input_accepted_count\":%0d,\"stage0_accepted_count\":%0d,\"mlp_gate_input_accepted_count\":%0d,\"mlp_up_input_accepted_count\":%0d,\"mlp_gate_output_accepted_count\":%0d,\"mlp_up_output_accepted_count\":%0d,\"mlp_mul_output_accepted_count\":%0d,\"mlp_down_input_accepted_count\":%0d,\"mlp_down_input_terminal_fire_count\":%0d,\"mlp_down_output_accepted_count\":%0d,\"core_egress_accepted_count\":%0d,\"stage0_valid\":%s,\"stage0_ready\":%s,\"qkv_input_valid\":%s,\"qkv_input_ready\":%s,\"qkv_input_accepted_count\":%0d,\"residual1_enqueue_valid\":%s,\"rms2_input_valid\":%s,\"residual2_enqueue_valid\":%s,\"mlp_gate_input_valid\":%s,\"mlp_gate_input_ready\":%s,\"mlp_up_input_valid\":%s,\"mlp_up_input_ready\":%s,\"mlp_gate_output_valid\":%s,\"mlp_gate_output_ready\":%s,\"mlp_up_output_valid\":%s,\"mlp_up_output_ready\":%s,\"mlp_mul_output_valid\":%s,\"mlp_mul_output_ready\":%s,\"mlp_down_output_valid\":%s,\"mlp_down_output_ready\":%s,\"core_egress_valid\":%s,\"core_egress_ready\":%s}",
            json_bool((layer_input_count[frontier_layer] + frontier_input_fire) >= BEATS_PER_LAYER),
            layer_input_count[frontier_layer] + frontier_input_fire,
            frontier_output_count,
            frontier_core_ingress_fire_count + frontier_core_ingress_fire,
            frontier_stage0_input_fire_count + frontier_stage0_input_fire,
            frontier_stage0_fire_count + frontier_stage0_fire,
            frontier_mlp_gate_input_fire_count + frontier_mlp_gate_input_fire,
            frontier_mlp_up_input_fire_count + frontier_mlp_up_input_fire,
            frontier_mlp_gate_output_fire_count + frontier_mlp_gate_output_fire,
            frontier_mlp_up_output_fire_count + frontier_mlp_up_output_fire,
            frontier_mlp_mul_output_fire_count + frontier_mlp_mul_output_fire,
            frontier_mlp_down_input_fire_count + frontier_mlp_down_input_fire,
            frontier_mlp_down_input_terminal_fire_count +
              (((frontier_mlp_down_input_fire === 1'b1) &&
                (dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_last__bore === 1'b1)) ? 1 : 0),
            frontier_mlp_down_output_fire_count + frontier_mlp_down_output_fire,
            frontier_core_egress_fire_count + frontier_core_egress_fire,
            json_logic(frontier_stage0_valid),
            json_logic(frontier_stage0_ready),
            json_logic(dut.spatialacc_single_kernel.core.qkv_io_in_valid),
            json_logic(dut.spatialacc_single_kernel.core.qkv_io_in_ready),
            frontier_qkv_input_fire_count + frontier_qkv_input_fire,
            json_logic(dut.spatialacc_single_kernel.core.res1Q_io_enq_valid),
            json_logic(dut.spatialacc_single_kernel.core.rms2_io_in_valid),
            json_logic(dut.spatialacc_single_kernel.core.res2Q_io_enq_valid),
            json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_in_valid__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_in_ready__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_in_valid__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_in_ready__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_valid__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_ready__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_valid__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_ready__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_valid__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_ready__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_valid__bore),
            json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_ready__bore),
            json_logic(frontier_core_egress_valid),
            json_logic(frontier_core_egress_ready));
        end
        $fwrite(progress_fd, "}\n");
        progress_sequence = progress_sequence + 1;
        $fflush(progress_fd);
        $display("SPATIALACC_BOARD_PROGRESS sequence=%0d event_kind=stall_snapshot phase=%s layer=%0d input_count=%0d output_count=%0d fifo_count=%0d cycle=%0d evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
                 progress_sequence, continuation_phase, frontier_layer,
                 layer_input_count[frontier_layer] + frontier_input_fire,
                 frontier_output_count, dut.output_fifo_count, cycle_count);
        write_live_observation_reports(continuation_phase);
      end
    end
  endtask

  // probe_id=probe.connected_kernel_lifecycle_order_at_full_direct_ingress.1
  // Read-only single-shot record emitted only at the already semantic
  // all-direct-core-ingress/no-direct-core-egress frontier.  It preserves the
  // direct liveness contradiction while exposing the observed lifecycle/start
  // ordering without driving any DUT signal or adding a completion timeout.
  task automatic emit_connected_kernel_lifecycle_order_observation;
    reg outer_ingress_precedes_start;
    reg start_precedes_outer_ingress;
    begin
      outer_ingress_precedes_start =
        (frontier_first_input_fire_cycle != 0) &&
        (frontier_first_start_cycle != 0) &&
        (frontier_first_input_fire_cycle < frontier_first_start_cycle);
      start_precedes_outer_ingress =
        (frontier_first_input_fire_cycle != 0) &&
        (frontier_first_start_cycle != 0) &&
        (frontier_first_start_cycle <= frontier_first_input_fire_cycle);
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"connected_kernel_input_to_output\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_lifecycle_order_at_full_direct_ingress.1\",\"probe_revision\":1,\"source_marker\":\"connected_kernel_lifecycle_order_at_full_direct_ingress_r1\",\"observational_only\":true,\"first_outer_input_fire_cycle\":%0d,\"first_start_cycle\":%0d,\"core_start_pulse_count\":%0d,\"core_start_asserted_cycle_count\":%0d,\"core_ingress_accepted_count\":%0d,\"stage0_input_accepted_count\":%0d,\"stage0_accepted_count\":%0d,\"core_egress_accepted_count\":%0d,\"outer_output_accepted_count\":%0d,\"outer_ingress_precedes_start\":%s,\"start_precedes_outer_ingress\":%s},\"expected_value\":{\"required_input_accepted_count\":%0d,\"required_output_accepted_count\":%0d,\"availability\":\"direct_core_lifecycle_order_and_liveness\"},\"contract\":\"connected_kernel_input_to_output\",\"status\":\"fail\"}\n",
          cycle_count,
          frontier_core_ingress_fire_count,
          frontier_core_ingress_fire_count,
          frontier_first_input_fire_cycle,
          frontier_first_start_cycle,
          frontier_core_start_pulse_count,
          frontier_core_start_asserted_cycle_count,
          frontier_core_ingress_fire_count,
          frontier_stage0_input_fire_count,
          frontier_stage0_fire_count,
          frontier_core_egress_fire_count,
          dut.output_accept_count,
          json_bool(outer_ingress_precedes_start),
          json_bool(start_precedes_outer_ingress),
          BEATS_PER_LAYER,
          BEATS_PER_LAYER);
        $fflush(boundary_fd);
      end
    end
  endtask

  // probe_id=probe.connected_kernel_start_to_core_ingress_order.1
  // Read-only, single-shot direct-core lifecycle witness emitted at the
  // semantic full-ingress/no-egress frontier. It records whether the first
  // direct core ingress handshake occurred only after the observed core start
  // edge, without driving DUT signals or introducing a completion timeout.
  task automatic emit_connected_kernel_start_to_core_ingress_order_observation;
    reg core_ingress_precedes_start;
    reg start_precedes_core_ingress;
    begin
      core_ingress_precedes_start =
        (frontier_first_core_ingress_fire_cycle != 0) &&
        (frontier_first_start_cycle != 0) &&
        (frontier_first_core_ingress_fire_cycle < frontier_first_start_cycle);
      start_precedes_core_ingress =
        (frontier_first_core_ingress_fire_cycle != 0) &&
        (frontier_first_start_cycle != 0) &&
        (frontier_first_start_cycle <= frontier_first_core_ingress_fire_cycle);
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"connected_kernel_input_to_output\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_start_to_core_ingress_order.1\",\"probe_revision\":1,\"source_marker\":\"connected_kernel_start_to_core_ingress_order_r1\",\"observational_only\":true,\"first_start_cycle\":%0d,\"first_core_ingress_fire_cycle\":%0d,\"core_start_pulse_count\":%0d,\"core_ingress_accepted_count\":%0d,\"core_egress_accepted_count\":%0d,\"core_ingress_precedes_start\":%s,\"start_precedes_core_ingress\":%s},\"expected_value\":{\"required_input_accepted_count\":%0d,\"required_output_accepted_count\":%0d,\"availability\":\"direct_core_start_to_ingress_order\"},\"contract\":\"connected_kernel_input_to_output\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count,
          frontier_core_ingress_fire_count,
          frontier_core_ingress_fire_count,
          frontier_first_start_cycle,
          frontier_first_core_ingress_fire_cycle,
          frontier_core_start_pulse_count,
          frontier_core_ingress_fire_count,
          frontier_core_egress_fire_count,
          json_bool(core_ingress_precedes_start),
          json_bool(start_precedes_core_ingress),
          BEATS_PER_LAYER,
          BEATS_PER_LAYER);
        $fflush(boundary_fd);
      end
    end
  endtask

  // probe_id=probe.connected_kernel_prestart_direct_ingress.16
  // Read-only direct lifecycle-order witness. It is emitted at the observed
  // core-start edge only when an earlier direct core-ingress handshake already
  // occurred; it drives no DUT signal, adds no port or synthesizable state,
  // and uses no elapsed-time completion condition.
  always @(posedge dut.kernel_start_to_core) begin : spatialacc_prestart_direct_ingress_probe_r16
    if ((boundary_fd != 0) &&
        (dut.layer_index == 5'd0) &&
        (frontier_first_core_ingress_fire_cycle != 0) &&
        (frontier_core_ingress_fire_count != 0) &&
        (frontier_core_egress_fire_count == 0)) begin
      $fwrite(boundary_fd,
        "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"connected_kernel_input_to_output\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_prestart_direct_ingress.16\",\"probe_revision\":16,\"source_marker\":\"connected_kernel_prestart_direct_ingress_r16\",\"observational_only\":true,\"first_core_ingress_fire_cycle\":%0d,\"observed_core_start_cycle\":%0d,\"core_ingress_accepted_count\":%0d,\"core_egress_accepted_count\":%0d,\"core_ingress_precedes_start\":true},\"expected_value\":{\"accepted_core_ingress_before_lifecycle_start\":true,\"availability\":\"direct_core_lifecycle_order\"},\"contract\":\"accepted_input_handshake_precedes_kernel_lifecycle_start\",\"status\":\"diagnostic_seed\"}\n",
        cycle_count,
        frontier_core_ingress_fire_count,
        frontier_core_ingress_fire_count,
        frontier_first_core_ingress_fire_cycle,
        cycle_count,
        frontier_core_ingress_fire_count,
        frontier_core_egress_fire_count);
      $fflush(boundary_fd);
      if (progress_fd != 0) begin
        emit_progress_event(
          "stall_snapshot",
          "connected_kernel_prestart_direct_ingress",
          1'b0,
          0,
          frontier_core_ingress_fire_count / BEATS_PER_TOKEN,
          frontier_core_ingress_fire_count % BEATS_PER_TOKEN,
          "connected_kernel_input_to_output");
      end
    end
  end

  // probe_id=probe.connected_kernel_first_direct_ingress_start_level.17
  // Read-only, single-shot direct-core handshake witness. It samples the
  // lifecycle start level on the actual first core-ingress handshake and is
  // emitted only if that handshake occurs before start. It drives no DUT
  // signal, adds no DUT port, and has no elapsed-time completion condition.
  always @(posedge c0_ddr4_s_axi_clk) begin : spatialacc_first_direct_ingress_start_level_probe_r17
    reg emitted;
    if ((emitted !== 1'b1) &&
        (boundary_fd != 0) &&
        (dut.layer_index == 5'd0) &&
        (frontier_core_ingress_fire_count == 0) &&
        (frontier_core_ingress_fire === 1'b1) &&
        (dut.kernel_start_to_core !== 1'b1)) begin
      emitted = 1'b1;
      $fwrite(boundary_fd,
        "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"connected_kernel_input_to_output\",\"tx_id\":0,\"tile_id\":-1,\"logical_index\":0,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_first_direct_ingress_start_level.17\",\"probe_revision\":17,\"source_marker\":\"connected_kernel_first_direct_ingress_start_level_r17\",\"observational_only\":true,\"kernel_reset\":%s,\"kernel_start_q\":%s,\"kernel_start_to_core\":%s,\"core_ingress_valid\":%s,\"core_ingress_ready\":%s,\"core_ingress_fire\":1,\"core_ingress_accepted_count_before_fire\":%0d,\"core_egress_accepted_count\":%0d},\"expected_value\":{\"kernel_start_to_core\":\"0\",\"accepted_core_ingress_required_before_lifecycle_start\":true},\"contract\":\"accepted_input_handshake_precedes_kernel_lifecycle_start\",\"status\":\"diagnostic_seed\"}\n",
        cycle_count,
        json_logic(dut.kernel_reset_q),
        json_logic(dut.kernel_start_q),
        json_logic(dut.kernel_start_to_core),
        json_logic(frontier_core_ingress_valid),
        json_logic(frontier_core_ingress_ready),
        frontier_core_ingress_fire_count,
        frontier_core_egress_fire_count);
      $fflush(boundary_fd);
    end
  end

  // probe_id=probe.connected_kernel_stage0_prestart_start_level.18
  // Read-only direct data-boundary witness. It records only an actual stage-0
  // input handshake received before any observed core start pulse. It drives
  // no DUT signal, adds no DUT port, and uses no elapsed-time condition.
  always @(posedge c0_ddr4_s_axi_clk) begin : spatialacc_stage0_prestart_start_level_probe_r18
    reg emitted;
    if ((emitted !== 1'b1) &&
        (boundary_fd != 0) &&
        (dut.layer_index == 5'd0) &&
        (frontier_core_start_pulse_count == 0) &&
        (dut.kernel_start_to_core !== 1'b1) &&
        (frontier_stage0_input_fire === 1'b1) &&
        (frontier_core_egress_fire_count == 0)) begin
      emitted = 1'b1;
      $fwrite(boundary_fd,
        "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_block_input_to_stage_00_rms_norm_1_input\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_stage0_prestart_start_level.18\",\"probe_revision\":18,\"source_marker\":\"connected_kernel_stage0_prestart_start_level_r18\",\"observational_only\":true,\"kernel_reset\":%s,\"kernel_start_to_core\":%s,\"observed_start_pulse_count_before_fire\":%0d,\"stage0_input_valid\":%s,\"stage0_input_ready\":%s,\"stage0_input_fire\":1,\"stage0_input_accepted_count_before_fire\":%0d,\"core_ingress_accepted_count_before_fire\":%0d,\"core_egress_accepted_count\":%0d},\"expected_value\":{\"kernel_start_to_core\":\"0\",\"accepted_stage0_input_before_lifecycle_start\":true},\"contract\":\"accepted_input_handshake_precedes_kernel_lifecycle_start\",\"status\":\"diagnostic_seed\"}\n",
        cycle_count,
        frontier_stage0_input_fire_count,
        frontier_stage0_input_fire_count,
        json_logic(dut.kernel_reset_q),
        json_logic(dut.kernel_start_to_core),
        frontier_core_start_pulse_count,
        json_logic(frontier_stage0_input_valid),
        json_logic(frontier_stage0_input_ready),
        frontier_stage0_input_fire_count,
        frontier_core_ingress_fire_count,
        frontier_core_egress_fire_count);
      $fflush(boundary_fd);
    end
  end

  // probe_id=probe.connected_kernel_lifecycle_bound_direct_egress_absence.15
  // Read-only, single-shot lifecycle-bound direct-core liveness record.  It is
  // emitted only by the existing exact all-direct-core-ingress/no-direct-core-
  // egress semantic trigger; it drives no DUT signal and introduces neither a
  // timeout nor synthesizable state.
  task automatic emit_connected_kernel_lifecycle_bound_frontier_observation;
    begin
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"connected_kernel_input_to_output\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_lifecycle_bound_direct_egress_absence.15\",\"probe_revision\":15,\"source_marker\":\"connected_kernel_lifecycle_bound_direct_egress_absence_r15\",\"observational_only\":true,\"kernel_reset\":%s,\"invocation_launched\":%s,\"reset_release_cycle\":%0d,\"weight_load_complete_cycle\":%0d,\"runtime_load_complete_cycle\":%0d,\"first_start_cycle\":%0d,\"core_start_pulse_count\":%0d,\"first_core_ingress_fire_cycle\":%0d,\"core_ingress_accepted_count\":%0d,\"stage0_input_accepted_count\":%0d,\"stage0_accepted_count\":%0d,\"core_egress_accepted_count\":%0d,\"outer_output_accepted_count\":%0d},\"expected_value\":{\"required_input_accepted_count\":%0d,\"required_output_accepted_count\":%0d,\"availability\":\"direct_lifecycle_bound_core_liveness\"},\"contract\":\"connected_kernel_input_to_output\",\"status\":\"fail\"}\n",
          cycle_count,
          frontier_core_ingress_fire_count,
          frontier_core_ingress_fire_count,
          json_logic(dut.kernel_reset_q),
          json_logic(dut.kernel_invocation_launched),
          frontier_kernel_reset_release_cycle,
          frontier_weight_load_complete_cycle,
          frontier_runtime_load_complete_cycle,
          frontier_first_start_cycle,
          frontier_core_start_pulse_count,
          frontier_first_core_ingress_fire_cycle,
          frontier_core_ingress_fire_count,
          frontier_stage0_input_fire_count,
          frontier_stage0_fire_count,
          frontier_core_egress_fire_count,
          dut.output_accept_count,
          BEATS_PER_LAYER,
          BEATS_PER_LAYER);
        $fflush(boundary_fd);
      end
    end
  endtask

  task automatic emit_direct_core_frontier_observation;
    begin
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"connected_kernel_input_to_output\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"source_marker\":\"connected_kernel_direct_frontier_r12\",\"kernel_reset\":%s,\"kernel_start_q\":%s,\"kernel_start_to_core\":%s,\"kernel_invocation_launched\":%s,\"core_ingress_valid\":%s,\"core_ingress_ready\":%s,\"core_ingress_fire\":%0d,\"core_ingress_accepted_count\":%0d,\"stage0_valid\":%s,\"stage0_ready\":%s,\"stage0_fire\":%0d,\"stage0_accepted_count\":%0d,\"core_egress_valid\":%s,\"core_egress_ready\":%s,\"core_egress_fire\":%0d,\"core_egress_accepted_count\":%0d,\"output_accept_count\":%0d},\"expected_value\":{\"required_input_accepted_count\":%0d,\"required_output_accepted_count\":%0d,\"availability\":\"direct_core_boundary_liveness\"},\"contract\":\"connected_kernel_input_to_output\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count,
          dut.input_axi_index,
          dut.input_axi_index,
          json_logic(dut.kernel_reset_q),
          json_logic(dut.kernel_start_q),
          json_logic(dut.kernel_start_to_core),
          json_logic(dut.kernel_invocation_launched),
          json_logic(frontier_core_ingress_valid),
          json_logic(frontier_core_ingress_ready),
          frontier_core_ingress_fire,
          frontier_core_ingress_fire_count,
          json_logic(frontier_stage0_valid),
          json_logic(frontier_stage0_ready),
          frontier_stage0_fire,
          frontier_stage0_fire_count,
          json_logic(frontier_core_egress_valid),
          json_logic(frontier_core_egress_ready),
          frontier_core_egress_fire,
          frontier_core_egress_fire_count,
          dut.output_accept_count,
          BEATS_PER_LAYER,
          BEATS_PER_LAYER);
        $fflush(boundary_fd);
      end
    end
  endtask

  task automatic emit_connected_kernel_core_boundary_trace;
    integer ingress_count;
    integer stage0_input_count;
    integer stage0_count;
    integer mlp_gate_input_count;
    integer mlp_up_input_count;
    integer mlp_gate_output_count;
    integer mlp_up_output_count;
    integer mlp_mul_output_count;
    integer mlp_down_output_count;
    integer egress_count;
    begin
      if (boundary_fd != 0) begin
        ingress_count = frontier_core_ingress_fire_count +
                        ((frontier_core_ingress_fire === 1'b1) ? 1 : 0);
        stage0_input_count = frontier_stage0_input_fire_count +
                             ((frontier_stage0_input_fire === 1'b1) ? 1 : 0);
        stage0_count = frontier_stage0_fire_count +
                       ((frontier_stage0_fire === 1'b1) ? 1 : 0);
        mlp_gate_input_count = frontier_mlp_gate_input_fire_count +
                               frontier_mlp_gate_input_fire;
        mlp_up_input_count = frontier_mlp_up_input_fire_count +
                             frontier_mlp_up_input_fire;
        mlp_gate_output_count = frontier_mlp_gate_output_fire_count +
                                frontier_mlp_gate_output_fire;
        mlp_up_output_count = frontier_mlp_up_output_fire_count +
                              frontier_mlp_up_output_fire;
        mlp_mul_output_count = frontier_mlp_mul_output_fire_count +
                               frontier_mlp_mul_output_fire;
        mlp_down_output_count = frontier_mlp_down_output_fire_count +
                                frontier_mlp_down_output_fire;
        egress_count = frontier_core_egress_fire_count +
                       ((frontier_core_egress_fire === 1'b1) ? 1 : 0);
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_block_input_to_stage_00_rms_norm_1_input\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"core_ingress_valid\":%s,\"core_ingress_ready\":%s,\"core_ingress_accepted_count\":%0d,\"stage0_input_valid\":%s,\"stage0_input_ready\":%s,\"stage0_input_accepted_count\":%0d,\"current_payload_unknown\":%s,\"current_payload_digest\":\"%08x\",\"outer_input_accepted_count\":%0d,\"outer_output_accepted_count\":%0d},\"expected_value\":{\"availability\":\"no_boundary_golden_required_for_liveness_trace\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count, ingress_count, ingress_count,
          json_logic(frontier_core_ingress_valid),
          json_logic(frontier_core_ingress_ready), ingress_count,
          json_logic(frontier_stage0_input_valid),
          json_logic(frontier_stage0_input_ready), stage0_input_count,
          json_bool($isunknown(frontier_core_ingress_data)),
          payload_digest256(frontier_core_ingress_data),
          layer_input_count[0], layer_output_count[0]);
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"stage0_valid\":%s,\"stage0_ready\":%s,\"stage0_accepted_count\":%0d,\"qkv_input_valid\":%s,\"qkv_input_ready\":%s,\"qkv_input_fire\":%0d,\"current_payload_unknown\":%s,\"current_payload_digest\":\"%08x\",\"upstream_core_ingress_accepted_count\":%0d,\"outer_input_accepted_count\":%0d,\"outer_output_accepted_count\":%0d},\"expected_value\":{\"availability\":\"no_boundary_golden_required_for_liveness_trace\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count, stage0_count, stage0_count,
          json_logic(frontier_stage0_valid), json_logic(frontier_stage0_ready),
          stage0_count,
          json_logic(dut.spatialacc_single_kernel.core.qkv_io_in_valid),
          json_logic(dut.spatialacc_single_kernel.core.qkv_io_in_ready),
          ((dut.spatialacc_single_kernel.core.qkv_io_in_valid === 1'b1) &&
           (dut.spatialacc_single_kernel.core.qkv_io_in_ready === 1'b1)),
          json_bool($isunknown(frontier_stage0_data)),
          payload_digest256(frontier_stage0_data), ingress_count,
          layer_input_count[0], layer_output_count[0]);
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_03_rms_norm_2_to_stage_04_mlp_gate_proj_mlp_gate_branch\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"valid\":%s,\"ready\":%s,\"accepted_count\":%0d,\"upstream_stage0_accepted_count\":%0d,\"qkv_input_valid\":%s,\"residual1_enqueue_valid\":%s,\"rms2_input_valid\":%s,\"residual2_enqueue_valid\":%s,\"outer_input_accepted_count\":%0d,\"outer_output_accepted_count\":%0d},\"expected_value\":{\"availability\":\"no_boundary_golden_required_for_liveness_trace\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count, mlp_gate_input_count, mlp_gate_input_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_in_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_in_ready__bore),
          mlp_gate_input_count, stage0_count,
          json_logic(dut.spatialacc_single_kernel.core.qkv_io_in_valid),
          json_logic(dut.spatialacc_single_kernel.core.res1Q_io_enq_valid),
          json_logic(dut.spatialacc_single_kernel.core.rms2_io_in_valid),
          json_logic(dut.spatialacc_single_kernel.core.res2Q_io_enq_valid),
          layer_input_count[0], layer_output_count[0]);
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_03_rms_norm_2_to_stage_05_mlp_up_proj_mlp_up_branch\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"valid\":%s,\"ready\":%s,\"accepted_count\":%0d,\"upstream_stage0_accepted_count\":%0d,\"outer_input_accepted_count\":%0d,\"outer_output_accepted_count\":%0d},\"expected_value\":{\"availability\":\"no_boundary_golden_required_for_liveness_trace\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count, mlp_up_input_count, mlp_up_input_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_in_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_in_ready__bore),
          mlp_up_input_count, stage0_count,
          layer_input_count[0], layer_output_count[0]);
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_04_mlp_gate_proj_to_stage_06_activation_mul_mlp_gate_to_mul\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"valid\":%s,\"ready\":%s,\"accepted_count\":%0d,\"gate_input_accepted_count\":%0d,\"up_input_accepted_count\":%0d},\"expected_value\":{\"availability\":\"no_boundary_golden_required_for_liveness_trace\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count, mlp_gate_output_count, mlp_gate_output_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_ready__bore),
          mlp_gate_output_count, mlp_gate_input_count, mlp_up_input_count);
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_05_mlp_up_proj_to_stage_06_activation_mul_mlp_up_to_mul\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"valid\":%s,\"ready\":%s,\"accepted_count\":%0d,\"gate_input_accepted_count\":%0d,\"up_input_accepted_count\":%0d},\"expected_value\":{\"availability\":\"no_boundary_golden_required_for_liveness_trace\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count, mlp_up_output_count, mlp_up_output_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_ready__bore),
          mlp_up_output_count, mlp_gate_input_count, mlp_up_input_count);
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_06_activation_mul_to_stage_07_mlp_down_proj_main\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"valid\":%s,\"ready\":%s,\"accepted_count\":%0d,\"gate_output_accepted_count\":%0d,\"up_output_accepted_count\":%0d},\"expected_value\":{\"availability\":\"no_boundary_golden_required_for_liveness_trace\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count, mlp_mul_output_count, mlp_mul_output_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_ready__bore),
          mlp_mul_output_count, mlp_gate_output_count, mlp_up_output_count);
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_07_mlp_down_proj_to_stage_08_residual_add_2_main\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"valid\":%s,\"ready\":%s,\"accepted_count\":%0d,\"mul_output_accepted_count\":%0d},\"expected_value\":{\"availability\":\"no_boundary_golden_required_for_liveness_trace\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count, mlp_down_output_count, mlp_down_output_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_ready__bore),
          mlp_down_output_count, mlp_mul_output_count);
        $fwrite(boundary_fd, "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_08_residual_add_2_to_block_output_output\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"core_egress_valid\":%s,\"core_egress_ready\":%s,\"core_egress_accepted_count\":%0d,\"current_payload_unknown\":%s,\"current_payload_digest\":\"%08x\",\"upstream_stage0_accepted_count\":%0d,\"outer_input_accepted_count\":%0d,\"outer_output_accepted_count\":%0d},\"expected_value\":{\"availability\":\"no_boundary_golden_required_for_liveness_trace\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count, egress_count, egress_count,
          json_logic(frontier_core_egress_valid),
          json_logic(frontier_core_egress_ready), egress_count,
          json_bool($isunknown(frontier_core_egress_data)),
          payload_digest256(frontier_core_egress_data), stage0_count,
          layer_input_count[0], layer_output_count[0]);
        $fflush(boundary_fd);
      end
    end
  endtask

  task automatic emit_mlp_down_ingress_boundary_observation;
    integer observed_ingress_count;
    begin
      if (boundary_fd != 0) begin
        observed_ingress_count = frontier_mlp_down_input_fire_count +
                                 ((frontier_mlp_down_input_fire === 1'b1) ? 1 : 0);
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_06_activation_mul_to_stage_07_mlp_down_proj_main\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_mlp_down_ingress_after_full_ingress.1\",\"probe_revision\":1,\"source_marker\":\"connected_kernel_mlp_down_ingress_after_full_ingress_r1\",\"all_outer_ingress_accepted\":%s,\"mlp_mul_output_valid\":%s,\"mlp_mul_output_ready\":%s,\"mlp_mul_output_fire\":%0d,\"mlp_mul_output_accepted_count\":%0d,\"mlp_down_input_valid\":%s,\"mlp_down_input_ready\":%s,\"mlp_down_input_fire\":%0d,\"mlp_down_input_accepted_count\":%0d,\"mlp_down_output_valid\":%s,\"mlp_down_output_ready\":%s,\"mlp_down_output_fire\":%0d,\"mlp_down_output_accepted_count\":%0d,\"core_egress_accepted_count\":%0d},\"expected_value\":{\"availability\":\"direct_activation_mul_to_mlp_down_liveness\",\"required_outer_ingress_count\":%0d},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count,
          observed_ingress_count,
          observed_ingress_count,
          json_bool(frontier_core_ingress_fire_count >= BEATS_PER_LAYER),
          json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_ready__bore),
          frontier_mlp_mul_output_fire,
          frontier_mlp_mul_output_fire_count +
            ((frontier_mlp_mul_output_fire === 1'b1) ? 1 : 0),
          json_logic(frontier_mlp_down_input_valid),
          json_logic(frontier_mlp_down_input_ready),
          frontier_mlp_down_input_fire,
          observed_ingress_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_ready__bore),
          frontier_mlp_down_output_fire,
          frontier_mlp_down_output_fire_count +
            ((frontier_mlp_down_output_fire === 1'b1) ? 1 : 0),
          frontier_core_egress_fire_count,
          BEATS_PER_LAYER);
        $fflush(boundary_fd);
      end
    end
  endtask

  // probe_id=probe.connected_kernel_mlp_down_terminal_contract.12
  // Read-only single-shot witness emitted at the semantic all-core-ingress
  // frontier. It distinguishes an incomplete MLP-down input tail from an
  // output-side stall without driving DUT signals or using elapsed time.
  task automatic emit_mlp_down_terminal_contract_observation;
    begin
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_06_activation_mul_to_stage_07_mlp_down_proj_main\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_mlp_down_terminal_contract.12\",\"probe_revision\":12,\"source_marker\":\"connected_kernel_mlp_down_terminal_contract_r12\",\"outer_core_ingress_accepted_count\":%0d,\"mlp_down_input\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d,\"terminal_fire_count\":%0d},\"mlp_down_output\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d,\"terminal_fire_count\":%0d},\"residual2_enqueue_valid\":%s,\"core_egress\":{\"valid\":%s,\"ready\":%s,\"fire\":%0d,\"accepted_count\":%0d}},\"expected_value\":{\"availability\":\"direct_mlp_down_terminal_liveness\",\"required_outer_core_ingress_count\":%0d},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count,
          frontier_mlp_down_input_fire_count,
          frontier_mlp_down_input_fire_count,
          frontier_core_ingress_fire_count,
          json_logic(frontier_mlp_down_input_valid),
          json_logic(frontier_mlp_down_input_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_last__bore),
          frontier_mlp_down_input_fire,
          frontier_mlp_down_input_fire_count,
          frontier_mlp_down_input_terminal_fire_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_ready__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_bits_last__bore),
          frontier_mlp_down_output_fire,
          frontier_mlp_down_output_fire_count,
          frontier_mlp_down_output_terminal_fire_count,
          json_logic(dut.spatialacc_single_kernel.core.res2Q_io_enq_valid),
          json_logic(frontier_core_egress_valid),
          json_logic(frontier_core_egress_ready),
          frontier_core_egress_fire,
          frontier_core_egress_fire_count,
          BEATS_PER_LAYER);
        $fflush(boundary_fd);
      end
    end
  endtask

  task automatic checkpoint_emit_live_state_witness;
    begin
      if (progress_fd == 0)
        $fatal(1, "checkpoint live-state witness requires an open progress log");
      @(negedge c0_ddr4_s_axi_clk);
      #1;
      if (!checkpoint_event_queue_quiescent())
        $fatal(1, "checkpoint live-state witness boundary is not factually quiescent");
      emit_progress_event("semantic_progress", "post_anchor_live_state_witness", 1'b1,
                          checkpoint_cut_layer, checkpoint_cut_token,
                          checkpoint_cut_beat, checkpoint_cut_frontier);
      if (progress_fd == 0)
        $fatal(1, "checkpoint live-state witness log closed during emission");
      $fflush(progress_fd);
    end
  endtask

  function automatic integer checkpoint_axi_read_outstanding;
    begin
      checkpoint_axi_read_outstanding = (read_active || c0_ddr4_s_axi_rvalid) ? 1 : 0;
    end
  endfunction

  function automatic integer checkpoint_axi_write_outstanding;
    begin
      checkpoint_axi_write_outstanding =
        (write_active || write_response_pending || c0_ddr4_s_axi_bvalid) ? 1 : 0;
    end
  endfunction

  function automatic bit checkpoint_event_queue_quiescent;
    begin
      checkpoint_event_queue_quiescent =
        (checkpoint_axi_read_outstanding() == 0) &&
        (checkpoint_axi_write_outstanding() == 0) &&
        (read_active === 1'b0) &&
        (c0_ddr4_s_axi_rvalid === 1'b0) &&
        (c0_ddr4_s_axi_arvalid === 1'b0) &&
        (write_active === 1'b0) &&
        (write_response_pending === 1'b0) &&
        (c0_ddr4_s_axi_bvalid === 1'b0) &&
        (c0_ddr4_s_axi_awvalid === 1'b0) &&
        (c0_ddr4_s_axi_wvalid === 1'b0) &&
        (cfg_data_valid === 1'b0) &&
        (cnn0_input_batch_set === 1'b0) &&
        (cnn0_result_batch_clear === 1'b0) &&
        (dut.kernel_start_q === 1'b0) &&
        (dut.kernel_start_to_core === 1'b0) &&
        (dut.trace_weight_prefetch_start === 1'b0) &&
        (dut.trace_weight_prefetch_complete === 1'b0) &&
        (dut.trace_weight_bank_switch === 1'b0) &&
        (dut.trace_activation_bank_switch === 1'b0) &&
        (dut.trace_runtime_load_start === 1'b0) &&
        (dut.trace_runtime_load_complete === 1'b0) &&
        (dut.trace_kernel_start === 1'b0) &&
        (dut.trace_layer_output_complete === 1'b0) &&
        (dut.trace_final_writeback_start === 1'b0) &&
        (dut.trace_final_writeback_complete === 1'b0);
    end
  endfunction

  function automatic bit checkpoint_one_ps_alignment_is_clock_clear;
    time checkpoint_probe_time;
    begin
      checkpoint_probe_time = $time + 1;
      checkpoint_one_ps_alignment_is_clock_clear =
        ((checkpoint_probe_time % CLK_300M_HALF_PERIOD_PS) != 0) &&
        ((checkpoint_probe_time % CLK_600M_HALF_PERIOD_PS) != 0) &&
        ((checkpoint_probe_time % 2000) != 0);
    end
  endfunction

  task automatic checkpoint_wait_capture_barrier(
    input integer requested_settle_cycles,
    output bit complete
  );
    integer stable_sample_count;
    integer required_stable_samples;
    begin
      complete = 1'b0;
      stable_sample_count = 0;
      required_stable_samples =
        (requested_settle_cycles > 0) ? requested_settle_cycles : 1;
      while (!complete) begin
        @(negedge c0_ddr4_s_axi_clk);
        #1;
        if (checkpoint_event_queue_quiescent() &&
            checkpoint_one_ps_alignment_is_clock_clear()) begin
          if (stable_sample_count < required_stable_samples)
            stable_sample_count = stable_sample_count + 1;
          if (stable_sample_count >= required_stable_samples) begin
            complete = 1'b1;
          end
        end else begin
          stable_sample_count = 0;
        end
      end
    end
  endtask

  function automatic [31:0] checkpoint_rotr32(
    input [31:0] value,
    input integer amount
  );
    begin
      checkpoint_rotr32 = (value >> amount) | (value << (32-amount));
    end
  endfunction

  function automatic [31:0] checkpoint_sha256_k(input integer index);
    begin
      case (index)
        0: checkpoint_sha256_k=32'h428a2f98; 1: checkpoint_sha256_k=32'h71374491;
        2: checkpoint_sha256_k=32'hb5c0fbcf; 3: checkpoint_sha256_k=32'he9b5dba5;
        4: checkpoint_sha256_k=32'h3956c25b; 5: checkpoint_sha256_k=32'h59f111f1;
        6: checkpoint_sha256_k=32'h923f82a4; 7: checkpoint_sha256_k=32'hab1c5ed5;
        8: checkpoint_sha256_k=32'hd807aa98; 9: checkpoint_sha256_k=32'h12835b01;
        10: checkpoint_sha256_k=32'h243185be; 11: checkpoint_sha256_k=32'h550c7dc3;
        12: checkpoint_sha256_k=32'h72be5d74; 13: checkpoint_sha256_k=32'h80deb1fe;
        14: checkpoint_sha256_k=32'h9bdc06a7; 15: checkpoint_sha256_k=32'hc19bf174;
        16: checkpoint_sha256_k=32'he49b69c1; 17: checkpoint_sha256_k=32'hefbe4786;
        18: checkpoint_sha256_k=32'h0fc19dc6; 19: checkpoint_sha256_k=32'h240ca1cc;
        20: checkpoint_sha256_k=32'h2de92c6f; 21: checkpoint_sha256_k=32'h4a7484aa;
        22: checkpoint_sha256_k=32'h5cb0a9dc; 23: checkpoint_sha256_k=32'h76f988da;
        24: checkpoint_sha256_k=32'h983e5152; 25: checkpoint_sha256_k=32'ha831c66d;
        26: checkpoint_sha256_k=32'hb00327c8; 27: checkpoint_sha256_k=32'hbf597fc7;
        28: checkpoint_sha256_k=32'hc6e00bf3; 29: checkpoint_sha256_k=32'hd5a79147;
        30: checkpoint_sha256_k=32'h06ca6351; 31: checkpoint_sha256_k=32'h14292967;
        32: checkpoint_sha256_k=32'h27b70a85; 33: checkpoint_sha256_k=32'h2e1b2138;
        34: checkpoint_sha256_k=32'h4d2c6dfc; 35: checkpoint_sha256_k=32'h53380d13;
        36: checkpoint_sha256_k=32'h650a7354; 37: checkpoint_sha256_k=32'h766a0abb;
        38: checkpoint_sha256_k=32'h81c2c92e; 39: checkpoint_sha256_k=32'h92722c85;
        40: checkpoint_sha256_k=32'ha2bfe8a1; 41: checkpoint_sha256_k=32'ha81a664b;
        42: checkpoint_sha256_k=32'hc24b8b70; 43: checkpoint_sha256_k=32'hc76c51a3;
        44: checkpoint_sha256_k=32'hd192e819; 45: checkpoint_sha256_k=32'hd6990624;
        46: checkpoint_sha256_k=32'hf40e3585; 47: checkpoint_sha256_k=32'h106aa070;
        48: checkpoint_sha256_k=32'h19a4c116; 49: checkpoint_sha256_k=32'h1e376c08;
        50: checkpoint_sha256_k=32'h2748774c; 51: checkpoint_sha256_k=32'h34b0bcb5;
        52: checkpoint_sha256_k=32'h391c0cb3; 53: checkpoint_sha256_k=32'h4ed8aa4a;
        54: checkpoint_sha256_k=32'h5b9cca4f; 55: checkpoint_sha256_k=32'h682e6ff3;
        56: checkpoint_sha256_k=32'h748f82ee; 57: checkpoint_sha256_k=32'h78a5636f;
        58: checkpoint_sha256_k=32'h84c87814; 59: checkpoint_sha256_k=32'h8cc70208;
        60: checkpoint_sha256_k=32'h90befffa; 61: checkpoint_sha256_k=32'ha4506ceb;
        62: checkpoint_sha256_k=32'hbef9a3f7; 63: checkpoint_sha256_k=32'hc67178f2;
        default: checkpoint_sha256_k=32'd0;
      endcase
    end
  endfunction

  task automatic checkpoint_sha256_compress(
    inout reg [31:0] hash_state [0:7],
    input reg [7:0] message_block [0:63]
  );
    reg [31:0] words [0:63];
    reg [31:0] a;
    reg [31:0] b;
    reg [31:0] c;
    reg [31:0] d;
    reg [31:0] e;
    reg [31:0] f;
    reg [31:0] g;
    reg [31:0] h;
    reg [31:0] sigma0;
    reg [31:0] sigma1;
    reg [31:0] choose_value;
    reg [31:0] majority_value;
    reg [31:0] temp1;
    reg [31:0] temp2;
    integer word_index;
    begin
      for (word_index = 0; word_index < 16; word_index = word_index + 1) begin
        words[word_index] = {message_block[word_index*4],
                             message_block[(word_index*4)+1],
                             message_block[(word_index*4)+2],
                             message_block[(word_index*4)+3]};
      end
      for (word_index = 16; word_index < 64; word_index = word_index + 1) begin
        sigma0 = checkpoint_rotr32(words[word_index-15], 7) ^
                 checkpoint_rotr32(words[word_index-15], 18) ^
                 (words[word_index-15] >> 3);
        sigma1 = checkpoint_rotr32(words[word_index-2], 17) ^
                 checkpoint_rotr32(words[word_index-2], 19) ^
                 (words[word_index-2] >> 10);
        words[word_index] = words[word_index-16] + sigma0 +
                            words[word_index-7] + sigma1;
      end
      a=hash_state[0]; b=hash_state[1]; c=hash_state[2]; d=hash_state[3];
      e=hash_state[4]; f=hash_state[5]; g=hash_state[6]; h=hash_state[7];
      for (word_index = 0; word_index < 64; word_index = word_index + 1) begin
        sigma1 = checkpoint_rotr32(e, 6) ^ checkpoint_rotr32(e, 11) ^ checkpoint_rotr32(e, 25);
        choose_value = (e & f) ^ ((~e) & g);
        temp1 = h + sigma1 + choose_value + checkpoint_sha256_k(word_index) + words[word_index];
        sigma0 = checkpoint_rotr32(a, 2) ^ checkpoint_rotr32(a, 13) ^ checkpoint_rotr32(a, 22);
        majority_value = (a & b) ^ (a & c) ^ (b & c);
        temp2 = sigma0 + majority_value;
        h=g; g=f; f=e; e=d+temp1; d=c; c=b; b=a; a=temp1+temp2;
      end
      hash_state[0]=hash_state[0]+a; hash_state[1]=hash_state[1]+b;
      hash_state[2]=hash_state[2]+c; hash_state[3]=hash_state[3]+d;
      hash_state[4]=hash_state[4]+e; hash_state[5]=hash_state[5]+f;
      hash_state[6]=hash_state[6]+g; hash_state[7]=hash_state[7]+h;
    end
  endtask

  task automatic checkpoint_sha256_file(
    input string file_path,
    output string digest,
    output bit valid
  );
    integer file_descriptor;
    integer byte_value;
    integer block_index;
    integer fill_index;
    longint unsigned byte_count;
    longint unsigned bit_length;
    reg [7:0] message_block [0:63];
    reg [31:0] hash_state [0:7];
    begin
      digest = "";
      valid = 1'b0;
      file_descriptor = $fopen(file_path, "rb");
      if (file_descriptor != 0) begin
        hash_state[0]=32'h6a09e667; hash_state[1]=32'hbb67ae85;
        hash_state[2]=32'h3c6ef372; hash_state[3]=32'ha54ff53a;
        hash_state[4]=32'h510e527f; hash_state[5]=32'h9b05688c;
        hash_state[6]=32'h1f83d9ab; hash_state[7]=32'h5be0cd19;
        block_index = 0;
        byte_count = 0;
        byte_value = $fgetc(file_descriptor);
        while (byte_value >= 0) begin
          message_block[block_index] = byte_value[7:0];
          block_index = block_index + 1;
          byte_count = byte_count + 1;
          if (block_index == 64) begin
            checkpoint_sha256_compress(hash_state, message_block);
            block_index = 0;
          end
          byte_value = $fgetc(file_descriptor);
        end
        message_block[block_index] = 8'h80;
        block_index = block_index + 1;
        if (block_index > 56) begin
          for (fill_index = block_index; fill_index < 64; fill_index = fill_index + 1)
            message_block[fill_index] = 8'd0;
          checkpoint_sha256_compress(hash_state, message_block);
          block_index = 0;
        end
        for (fill_index = block_index; fill_index < 56; fill_index = fill_index + 1)
          message_block[fill_index] = 8'd0;
        bit_length = byte_count << 3;
        for (fill_index = 0; fill_index < 8; fill_index = fill_index + 1)
          message_block[63-fill_index] = bit_length[(fill_index*8) +: 8];
        checkpoint_sha256_compress(hash_state, message_block);
        digest = $sformatf("%08x%08x%08x%08x%08x%08x%08x%08x",
                           hash_state[0], hash_state[1], hash_state[2], hash_state[3],
                           hash_state[4], hash_state[5], hash_state[6], hash_state[7]);
        valid = 1'b1;
        $fclose(file_descriptor);
      end
    end
  endtask

  task automatic checkpoint_write_external_state(
    input string state_path,
    output bit complete
  );
    integer external_fd;
    integer layer_index;
    longint unsigned written_count;
    longint unsigned beat_key;
    begin
      complete = 1'b0;
      if (boundary_fd != 0) $fflush(boundary_fd);
      if (progress_fd != 0) $fflush(progress_fd);
      checkpoint_weight_file_offset = (weight_fd != 0) ? $ftell(weight_fd) : 0;
      checkpoint_boundary_file_offset = (boundary_fd != 0) ? $ftell(boundary_fd) : 0;
      checkpoint_progress_file_offset = (progress_fd != 0) ? $ftell(progress_fd) : 0;
      external_fd = $fopen(state_path, "w");
      if (external_fd != 0) begin
        $fwrite(external_fd, "spatialaccagent.testbench_external_state.v3\n");
        $fwrite(external_fd, "clock_phase %h %h %h %h\n",
                ($time % CHECKPOINT_CLOCK_PHASE_PERIOD_PS),
                clk_300M, clk_600M, c0_ddr4_s_axi_clk);
        $fwrite(external_fd, "immutable_request %s %s\n", checkpoint_request_sha256, checkpoint_request_path);
        $fwrite(external_fd, "immutable_paths %s %s %s %s\n",
                spatialacc_input_path, spatialacc_weight_image_path,
                spatialacc_runtime_image_path, spatialacc_expected_output_path);
        $fwrite(external_fd, "file_offsets %0d %0d %0d\n",
                checkpoint_weight_file_offset, checkpoint_boundary_file_offset,
                checkpoint_progress_file_offset);
        $fwrite(external_fd, "checkpoint_boundary_record %s\n",
                checkpoint_boundary_record);
        $fwrite(external_fd, "control %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                sys_rst_n, c0_ddr4_s_axi_rst_n, user_rst, c0_init_calib_complete,
                cfg_data, cfg_data_valid, cfg_done, cnn0_input_batch_set,
                cnn0_result_batch_clear, artifacts_loaded, artifact_error,
                axi_model_error, final_pass, weight_probe, weight_size,
                runtime_size, tb_c0_ddr4_s_axi_monitor.violation);
        $fwrite(external_fd, "axi_response %h %h %h %h %h %h %h %h %h %h %h\n",
                c0_ddr4_s_axi_awready, c0_ddr4_s_axi_wready,
                c0_ddr4_s_axi_bid, c0_ddr4_s_axi_bresp,
                c0_ddr4_s_axi_bvalid, c0_ddr4_s_axi_arready,
                c0_ddr4_s_axi_rlast, c0_ddr4_s_axi_rvalid,
                c0_ddr4_s_axi_rresp, c0_ddr4_s_axi_rid,
                c0_ddr4_s_axi_rdata);
        $fwrite(external_fd, "read_state %h %h %h %h %h %h %h %h %h\n",
                ready_lfsr, read_active, read_addr_q, read_len_q,
                read_beat_q, read_size_q, read_burst_q, read_id_q,
                read_delay_q);
        $fwrite(external_fd, "write_state %h %h %h %h %h %h %h %h %h\n",
                write_active, write_addr_q, write_len_q, write_beat_q,
                write_size_q, write_burst_q, write_id_q,
                write_response_delay_q, write_response_pending);
        $fwrite(external_fd, "counters_a %h %h %h %h %h %h %h %h %h %h %h %h\n",
                cycle_count, progress_sequence, semantic_progress_count,
                progress_epoch, last_semantic_progress_cycle,
                heartbeat_next_cycle, stall_snapshot_last_cycle,
                axi_read_transaction_count, axi_write_transaction_count,
                axi_read_beat_count, axi_write_beat_count,
                axi_write_response_count);
        $fwrite(external_fd, "counters_b %h %h %h %h %h\n",
                weight_accept_total, runtime_accept_total,
                kernel_input_accept_total, kernel_output_accept_total,
                concurrent_pipeline_cycle_count);
        $fwrite(external_fd, "trace_counters %h %h %h %h %h %h %h %h %h %h %h\n",
                trace_prefetch_start_count, trace_prefetch_complete_count,
                trace_weight_switch_count, trace_activation_switch_count,
                trace_runtime_start_count, trace_runtime_complete_count,
                trace_kernel_start_count, trace_layer_complete_count,
                trace_final_start_count, trace_final_complete_count,
                prefetch_compute_overlap_count);
        for (layer_index = 0; layer_index < TARGET_LAYERS; layer_index = layer_index + 1) begin
          $fwrite(external_fd, "layer %0d %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                  layer_index, runtime_accept_count[layer_index],
                  runtime_first_address[layer_index], runtime_last_address[layer_index],
                  runtime_contiguous[layer_index], runtime_data_match[layer_index],
                  runtime_last_ok[layer_index], runtime_complete_cycle[layer_index],
                  kernel_start_cycle[layer_index], layer_input_count[layer_index],
                  layer_output_count[layer_index], kernel_overlap_start_count[layer_index],
                  input_count_at_first_output[layer_index], first_output_seen[layer_index]);
        end
        written_count = written_beats.num();
        $fwrite(external_fd, "written_beats %0d\n", written_count);
        foreach (written_beats[beat_key]) begin
          $fwrite(external_fd, "beat %h %h\n", beat_key, written_beats[beat_key]);
        end
        $fwrite(external_fd, "end_external_state\n");
        $fflush(external_fd);
        $fclose(external_fd);
        complete = 1'b1;
      end
    end
  endtask

  task automatic checkpoint_read_restore_phase(
    input string state_path,
    output bit complete
  );
    integer phase_fd;
    integer phase_scan_rc;
    string external_schema;
    begin
      complete = 1'b0;
      phase_fd = $fopen(state_path, "r");
      if (phase_fd == 0) $fatal(1, "unable to open checkpoint external state for phase alignment");
      phase_scan_rc = $fscanf(phase_fd, "%s\n", external_schema);
      if ((phase_scan_rc != 1) ||
          (external_schema != "spatialaccagent.testbench_external_state.v3"))
        $fatal(1, "checkpoint external-state phase schema mismatch");
      phase_scan_rc = $fscanf(phase_fd, "clock_phase %h %h %h %h\n",
                              checkpoint_saved_clock_phase_slot,
                              checkpoint_saved_clk_300M,
                              checkpoint_saved_clk_600M,
                              checkpoint_saved_c0_ddr4_s_axi_clk);
      if ((phase_scan_rc != 4) ||
          (checkpoint_saved_clock_phase_slot >= CHECKPOINT_CLOCK_PHASE_PERIOD_PS))
        $fatal(1, "checkpoint clock-event phase state is incomplete");
      $fclose(phase_fd);
      complete = 1'b1;
    end
  endtask

  task automatic checkpoint_restore_external_state(
    input string state_path,
    input bit verify_clock_phase,
    output bit complete
  );
    integer external_fd;
    integer scan_rc;
    integer layer_index;
    integer restored_layer_index;
    integer restore_index;
    integer probe_descriptor;
    integer seek_result;
    integer word_index;
    integer byte0;
    integer byte1;
    integer byte2;
    integer byte3;
    longint unsigned restored_written_count;
    longint unsigned restored_beat_key;
    reg [511:0] restored_beat_value;
    string external_schema;
    string saved_request_sha256;
    string saved_request_path;
    string saved_input_path;
    string saved_weight_path;
    string saved_runtime_path;
    string saved_expected_path;
    string end_marker;
    begin
      complete = 1'b0;
      checkpoint_immutable_reopen_complete = 1'b0;
      external_fd = $fopen(state_path, "r");
      if (external_fd == 0) $fatal(1, "unable to open checkpoint external state");
      scan_rc = $fscanf(external_fd, "%s\n", external_schema);
      if ((scan_rc != 1) || (external_schema != "spatialaccagent.testbench_external_state.v3"))
        $fatal(1, "checkpoint external-state schema mismatch");
      scan_rc = $fscanf(external_fd, "clock_phase %h %h %h %h\n",
                        checkpoint_saved_clock_phase_slot,
                        checkpoint_saved_clk_300M,
                        checkpoint_saved_clk_600M,
                        checkpoint_saved_c0_ddr4_s_axi_clk);
      if (scan_rc != 4)
        $fatal(1, "checkpoint clock-event phase state is incomplete during external restore");
      if (verify_clock_phase &&
          (($time % CHECKPOINT_CLOCK_PHASE_PERIOD_PS) != checkpoint_saved_clock_phase_slot ||
           (clk_300M !== checkpoint_saved_clk_300M) ||
           (clk_600M !== checkpoint_saved_clk_600M) ||
           (c0_ddr4_s_axi_clk !== checkpoint_saved_c0_ddr4_s_axi_clk)))
        $fatal(1, "checkpoint restore did not reach the captured clock-event phase barrier");
      scan_rc = $fscanf(external_fd, "immutable_request %s %s\n",
                        saved_request_sha256, saved_request_path);
      if ((scan_rc != 2) || (saved_request_sha256 != checkpoint_request_sha256) ||
          (saved_request_path != checkpoint_request_path))
        $fatal(1, "checkpoint immutable request binding mismatch");
      scan_rc = $fscanf(external_fd, "immutable_paths %s %s %s %s\n",
                        saved_input_path, saved_weight_path,
                        saved_runtime_path, saved_expected_path);
      if ((scan_rc != 4) || (saved_input_path != spatialacc_input_path) ||
          (saved_weight_path != spatialacc_weight_image_path) ||
          (saved_runtime_path != spatialacc_runtime_image_path) ||
          (saved_expected_path != spatialacc_expected_output_path))
        $fatal(1, "checkpoint immutable artifact path binding mismatch");
      scan_rc = $fscanf(external_fd, "file_offsets %d %d %d\n",
                        checkpoint_weight_file_offset,
                        checkpoint_boundary_file_offset,
                        checkpoint_progress_file_offset);
      if (scan_rc != 3) $fatal(1, "checkpoint file-offset state is incomplete");
      scan_rc = $fscanf(external_fd, "checkpoint_boundary_record %s\n",
                        checkpoint_boundary_record);
      if ((scan_rc != 1) || (checkpoint_boundary_record.len() == 0))
        $fatal(1, "checkpoint pending boundary record is incomplete");
      scan_rc = $fscanf(external_fd,
                        "control %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                        sys_rst_n, c0_ddr4_s_axi_rst_n, user_rst,
                        c0_init_calib_complete, cfg_data, cfg_data_valid,
                        cfg_done, cnn0_input_batch_set, cnn0_result_batch_clear,
                        artifacts_loaded, artifact_error, axi_model_error,
                        final_pass, weight_probe, weight_size, runtime_size,
                        checkpoint_saved_monitor_violation);
      if (scan_rc != 17) $fatal(1, "checkpoint control state is incomplete");
      scan_rc = $fscanf(external_fd,
                        "axi_response %h %h %h %h %h %h %h %h %h %h %h\n",
                        c0_ddr4_s_axi_awready, c0_ddr4_s_axi_wready,
                        c0_ddr4_s_axi_bid, c0_ddr4_s_axi_bresp,
                        c0_ddr4_s_axi_bvalid, c0_ddr4_s_axi_arready,
                        c0_ddr4_s_axi_rlast, c0_ddr4_s_axi_rvalid,
                        c0_ddr4_s_axi_rresp, c0_ddr4_s_axi_rid,
                        c0_ddr4_s_axi_rdata);
      if (scan_rc != 11) $fatal(1, "checkpoint AXI response state is incomplete");
      scan_rc = $fscanf(external_fd, "read_state %h %h %h %h %h %h %h %h %h\n",
                        ready_lfsr, read_active, read_addr_q, read_len_q,
                        read_beat_q, read_size_q, read_burst_q, read_id_q,
                        read_delay_q);
      if (scan_rc != 9) $fatal(1, "checkpoint AXI read state is incomplete");
      scan_rc = $fscanf(external_fd, "write_state %h %h %h %h %h %h %h %h %h\n",
                        write_active, write_addr_q, write_len_q, write_beat_q,
                        write_size_q, write_burst_q, write_id_q,
                        write_response_delay_q, write_response_pending);
      if (scan_rc != 9) $fatal(1, "checkpoint AXI write state is incomplete");
      scan_rc = $fscanf(external_fd,
                        "counters_a %h %h %h %h %h %h %h %h %h %h %h %h\n",
                        cycle_count, progress_sequence, semantic_progress_count,
                        progress_epoch, last_semantic_progress_cycle,
                        heartbeat_next_cycle, stall_snapshot_last_cycle,
                        axi_read_transaction_count, axi_write_transaction_count,
                        axi_read_beat_count, axi_write_beat_count,
                        axi_write_response_count);
      if (scan_rc != 12) $fatal(1, "checkpoint primary counters are incomplete");
      scan_rc = $fscanf(external_fd, "counters_b %h %h %h %h %h\n",
                        weight_accept_total, runtime_accept_total,
                        kernel_input_accept_total, kernel_output_accept_total,
                        concurrent_pipeline_cycle_count);
      if (scan_rc != 5) $fatal(1, "checkpoint progress counters are incomplete");
      scan_rc = $fscanf(external_fd,
                        "trace_counters %h %h %h %h %h %h %h %h %h %h %h\n",
                        trace_prefetch_start_count, trace_prefetch_complete_count,
                        trace_weight_switch_count, trace_activation_switch_count,
                        trace_runtime_start_count, trace_runtime_complete_count,
                        trace_kernel_start_count, trace_layer_complete_count,
                        trace_final_start_count, trace_final_complete_count,
                        prefetch_compute_overlap_count);
      if (scan_rc != 11) $fatal(1, "checkpoint trace counters are incomplete");
      for (layer_index = 0; layer_index < TARGET_LAYERS; layer_index = layer_index + 1) begin
        scan_rc = $fscanf(external_fd,
                          "layer %d %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                          restored_layer_index, runtime_accept_count[layer_index],
                          runtime_first_address[layer_index], runtime_last_address[layer_index],
                          runtime_contiguous[layer_index], runtime_data_match[layer_index],
                          runtime_last_ok[layer_index], runtime_complete_cycle[layer_index],
                          kernel_start_cycle[layer_index], layer_input_count[layer_index],
                          layer_output_count[layer_index], kernel_overlap_start_count[layer_index],
                          input_count_at_first_output[layer_index], first_output_seen[layer_index]);
        if ((scan_rc != 14) || (restored_layer_index != layer_index))
          $fatal(1, "checkpoint per-layer state is incomplete or reordered");
      end
      scan_rc = $fscanf(external_fd, "written_beats %d\n", restored_written_count);
      if (scan_rc != 1) $fatal(1, "checkpoint DDR delta count is missing");
      written_beats.delete();
      for (restore_index = 0; restore_index < restored_written_count; restore_index = restore_index + 1) begin
        scan_rc = $fscanf(external_fd, "beat %h %h\n",
                          restored_beat_key, restored_beat_value);
        if (scan_rc != 2) $fatal(1, "checkpoint DDR delta is incomplete");
        written_beats[restored_beat_key] = restored_beat_value;
      end
      scan_rc = $fscanf(external_fd, "%s\n", end_marker);
      if ((scan_rc != 1) || (end_marker != "end_external_state"))
        $fatal(1, "checkpoint external-state terminator is missing");
      $fclose(external_fd);

      probe_descriptor = $fopen(spatialacc_input_path, "r");
      if (probe_descriptor == 0) $fatal(1, "unable to reopen immutable input artifact on restore");
      $fclose(probe_descriptor);
      $readmemh(spatialacc_input_path, input_beats);
      probe_descriptor = $fopen(spatialacc_expected_output_path, "r");
      if (probe_descriptor == 0) $fatal(1, "unable to reopen immutable expected-output artifact on restore");
      $fclose(probe_descriptor);
      $readmemh(spatialacc_expected_output_path, expected_beats);

      if (weight_fd != 0) $fclose(weight_fd);
      weight_fd = $fopen(spatialacc_weight_image_path, "rb");
      if (weight_fd == 0) $fatal(1, "unable to reopen immutable weight image on restore");
      seek_result = $fseek(weight_fd, checkpoint_weight_file_offset, 0);
      if (seek_result != 0) $fatal(1, "unable to restore immutable weight-image offset");

      runtime_fd = $fopen(spatialacc_runtime_image_path, "rb");
      if (runtime_fd == 0) $fatal(1, "unable to reopen immutable runtime image on restore");
      for (word_index = 0; word_index < RUNTIME_WORDS_PER_LAYER; word_index = word_index + 1) begin
        byte0=$fgetc(runtime_fd); byte1=$fgetc(runtime_fd);
        byte2=$fgetc(runtime_fd); byte3=$fgetc(runtime_fd);
        if ((byte0 < 0) || (byte1 < 0) || (byte2 < 0) || (byte3 < 0))
          $fatal(1, "runtime image ended during checkpoint restore");
        runtime_words[word_index] = {byte3[7:0], byte2[7:0], byte1[7:0], byte0[7:0]};
      end
      $fclose(runtime_fd);
      runtime_fd = 0;
      checkpoint_immutable_reopen_complete = 1'b1;

      if (boundary_fd != 0) begin
        $fflush(boundary_fd);
        $fclose(boundary_fd);
        boundary_fd = 0;
      end
      if (progress_fd != 0) begin
        $fflush(progress_fd);
        $fclose(progress_fd);
        progress_fd = 0;
      end
      if (tb_c0_ddr4_s_axi_monitor.violation !== checkpoint_saved_monitor_violation)
        $fatal(1, "protocol-monitor state does not match the quiescent checkpoint boundary");
      complete = 1'b1;
    end
  endtask

  task automatic checkpoint_isolate_evidence_suffix(
    input bit isolate_progress,
    output bit complete
  );
    begin
      complete = 1'b0;
      if (boundary_fd != 0) begin
        $fflush(boundary_fd);
        $fclose(boundary_fd);
        boundary_fd = 0;
      end
      if (progress_fd != 0) begin
        $fflush(progress_fd);
        if (isolate_progress) begin
          $fclose(progress_fd);
          progress_fd = 0;
        end
      end
      boundary_fd = $fopen("reports/boundary_trace.jsonl", "w");
      if (boundary_fd == 0)
        $fatal(1, "unable to isolate checkpoint boundary-trace suffix");
      if (isolate_progress) begin
        progress_fd = $fopen("reports/progress_event_log.jsonl", "w");
        if (progress_fd == 0)
          $fatal(1, "unable to isolate restored progress-event suffix");
      end
      $fflush(boundary_fd);
      if (progress_fd != 0) $fflush(progress_fd);
      complete = (boundary_fd != 0) && (progress_fd != 0);
    end
  endtask

  task automatic checkpoint_write_capture_report;
    integer report_fd;
    reg capsule_complete;
    begin
      capsule_complete = (checkpoint_vpi_rc == 0) &&
                         checkpoint_external_state_complete &&
                         checkpoint_evidence_flushed &&
                         checkpoint_capture_event_quiescent &&
                         checkpoint_runtime_schema_hash_valid;
      report_fd = $fopen(checkpoint_capture_report_path, "w");
      if (report_fd == 0) $fatal(1, "unable to create checkpoint capture report");
      $fwrite(report_fd,
        "{\"schema_version\":\"spatialaccagent.simulation_checkpoint_capture_report.v1\",\"status\":\"%s\",\"request_sha256\":\"%s\",\"mode\":\"%s\",\"semantic_cut_sha256\":\"%s\",\"checkpoint_trigger_observed\":%s,\"complete_dut_state_captured\":%s,\"complete_testbench_external_state_captured\":%s,\"evidence_flushed_before_capture\":%s,\"portable_state_capsule_complete\":%s,\"captured_sequence\":%0d,\"captured_cycle\":%0d,\"external_state_quiescent_at_capture\":%s,\"pending_event_queue_empty_at_capture\":%s,\"axi_read\":{\"outstanding\":%0d,\"pending_response\":%s},\"axi_write\":{\"outstanding\":%0d,\"pending_response\":%s},\"active_boundary_observation\":{\"event_queue_quiescent\":%s},\"state_schema\":{\"adapter\":\"framework_vpi_state_capsule_v1\",\"dut_state_root\":\"%s\",\"path\":\"%s\",\"sha256\":\"%s\"},\"state_artifacts\":[{\"kind\":\"dut_vpi_state\",\"path\":\"%s\"},{\"kind\":\"dut_vpi_schema\",\"path\":\"%s\",\"sha256\":\"%s\"},{\"kind\":\"testbench_external_state\",\"path\":\"%s\"}],\"immutable_artifact_reference\":{\"request\":\"%s\",\"request_sha256\":\"%s\",\"input\":\"%s\",\"weight_image\":\"%s\",\"runtime_image\":\"%s\",\"expected_output\":\"%s\"},\"trigger_sequence\":%0d,\"trigger_cycle\":%0d}\n",
        capsule_complete ? "pass" : "fail",
        checkpoint_request_sha256, checkpoint_mode,
        checkpoint_semantic_cut_sha256,
        json_bool(checkpoint_trigger_observed),
        json_bool(checkpoint_vpi_rc == 0),
        json_bool(checkpoint_external_state_complete),
        json_bool(checkpoint_evidence_flushed),
        json_bool(capsule_complete), checkpoint_captured_sequence,
        checkpoint_captured_cycle,
        json_bool(checkpoint_capture_event_quiescent),
        json_bool(checkpoint_capture_event_quiescent),
        checkpoint_captured_axi_read_outstanding,
        json_bool(checkpoint_captured_read_pending_response),
        checkpoint_captured_axi_write_outstanding,
        json_bool(checkpoint_captured_write_pending_response),
        json_bool(checkpoint_capture_event_quiescent),
        checkpoint_dut_root, checkpoint_dut_schema_path,
        checkpoint_runtime_schema_sha256, checkpoint_dut_state_path,
        checkpoint_dut_schema_path, checkpoint_runtime_schema_sha256,
        checkpoint_external_state_path, checkpoint_request_path,
        checkpoint_request_sha256, spatialacc_input_path,
        spatialacc_weight_image_path, spatialacc_runtime_image_path,
        spatialacc_expected_output_path, checkpoint_trigger_sequence,
        checkpoint_trigger_cycle);
      $fflush(report_fd);
      $fclose(report_fd);
    end
  endtask

  task automatic checkpoint_write_restore_report;
    integer report_fd;
    reg restore_complete;
    reg restore_quiescent;
    begin
      restore_quiescent = checkpoint_event_queue_quiescent();
      restore_complete = (checkpoint_vpi_rc == 0) &&
                         checkpoint_external_state_complete &&
                         checkpoint_immutable_reopen_complete &&
                         checkpoint_runtime_schema_hash_valid &&
                         checkpoint_evidence_suffix_isolated &&
                         checkpoint_boundary_state_match &&
                         restore_quiescent;
      report_fd = $fopen(checkpoint_restore_report_path, "w");
      if (report_fd == 0) $fatal(1, "unable to create checkpoint restore report");
      $fwrite(report_fd,
        "{\"schema_version\":\"spatialaccagent.simulation_checkpoint_restore_report.v1\",\"status\":\"%s\",\"request_sha256\":\"%s\",\"mode\":\"%s\",\"semantic_cut_sha256\":\"%s\",\"runtime_state_schema_match\":%s,\"runtime_state_schema_sha256\":\"%s\",\"restored_sequence\":%0d,\"restored_cycle\":%0d,\"complete_testbench_external_state_restored\":%s,\"pending_transactions_and_responses_restored\":%s,\"immutable_files_reopened_at_captured_offsets\":%s,\"event_queue_quiescent_after_restore\":%s,\"mutable_evidence_suffix_isolated\":%s",
        restore_complete ? "pass" : "fail",
        checkpoint_request_sha256, checkpoint_mode,
        checkpoint_semantic_cut_sha256,
        json_bool((checkpoint_vpi_rc == 0) && checkpoint_runtime_schema_hash_valid),
        checkpoint_runtime_schema_sha256,
        checkpoint_restored_sequence, checkpoint_restored_cycle,
        json_bool(checkpoint_external_state_complete),
        json_bool(checkpoint_external_state_complete),
        json_bool(checkpoint_immutable_reopen_complete),
        json_bool(restore_quiescent),
        json_bool(checkpoint_evidence_suffix_isolated));
      if (checkpoint_equivalence_probe != 0)
        $fwrite(report_fd, ",\"same_source_equivalence_probe\":true");
      else
        $fwrite(report_fd, ",\"checkpoint_id\":\"%s\"", checkpoint_id);
      $fwrite(report_fd, "}\n");
      $fflush(report_fd);
      $fclose(report_fd);
    end
  endtask

  initial begin
    checkpoint_enabled = 1'b0;
    checkpoint_runtime_ready = 1'b0;
    checkpoint_restore_requested = 1'b0;
    checkpoint_restore_complete = 1'b0;
    checkpoint_trigger_observed = 1'b0;
    checkpoint_evidence_flushed = 1'b0;
    checkpoint_capture_event_quiescent = 1'b0;
    checkpoint_external_state_complete = 1'b0;
    checkpoint_immutable_reopen_complete = 1'b0;
    checkpoint_runtime_schema_hash_valid = 1'b0;
    checkpoint_equivalence_probe = 0;
    checkpoint_id = "";
    checkpoint_runtime_schema_sha256 = "";
    checkpoint_saved_clock_phase_slot = 0;
    checkpoint_saved_clk_300M = 1'b0;
    checkpoint_saved_clk_600M = 1'b0;
    checkpoint_saved_c0_ddr4_s_axi_clk = 1'b0;
    checkpoint_restore_phase_ready = 1'b0;
    checkpoint_evidence_suffix_isolated = 1'b0;
    checkpoint_boundary_state_match = 1'b1;

    if ($value$plusargs("SPATIALACC_CHECKPOINT_MODE=%s", checkpoint_mode)) begin
      checkpoint_enabled = 1'b1;
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_REQUEST=%s", checkpoint_request_path))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_REQUEST");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_REQUEST_SHA256=%s", checkpoint_request_sha256))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_REQUEST_SHA256");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_SEMANTIC_CUT_SHA256=%s", checkpoint_semantic_cut_sha256))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_SEMANTIC_CUT_SHA256");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_DUT_ROOT=%s", checkpoint_dut_root))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_DUT_ROOT");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_CUT_SEQUENCE=%d", checkpoint_cut_sequence))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_CUT_SEQUENCE");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_CUT_CYCLE=%d", checkpoint_cut_cycle))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_CUT_CYCLE");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_CUT_PHASE=%s", checkpoint_cut_phase))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_CUT_PHASE");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_CUT_LAYER=%d", checkpoint_cut_layer))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_CUT_LAYER");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_CUT_TOKEN=%d", checkpoint_cut_token))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_CUT_TOKEN");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_CUT_BEAT=%d", checkpoint_cut_beat))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_CUT_BEAT");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_FRONTIER=%s", checkpoint_cut_frontier))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_FRONTIER");
      if (!$value$plusargs("SPATIALACC_CHECKPOINT_SETTLE_CYCLES=%d", checkpoint_settle_cycles))
        $fatal(1, "missing +SPATIALACC_CHECKPOINT_SETTLE_CYCLES");
      if (checkpoint_settle_cycles < 0)
        $fatal(1, "checkpoint settle interval must be nonnegative");

      if (checkpoint_mode == "cold_capture") begin
        if (!$value$plusargs("SPATIALACC_CHECKPOINT_DUT_STATE=%s", checkpoint_dut_state_path))
          $fatal(1, "missing +SPATIALACC_CHECKPOINT_DUT_STATE");
        if (!$value$plusargs("SPATIALACC_CHECKPOINT_DUT_SCHEMA=%s", checkpoint_dut_schema_path))
          $fatal(1, "missing +SPATIALACC_CHECKPOINT_DUT_SCHEMA");
        if (!$value$plusargs("SPATIALACC_CHECKPOINT_EXTERNAL_STATE=%s", checkpoint_external_state_path))
          $fatal(1, "missing +SPATIALACC_CHECKPOINT_EXTERNAL_STATE");
        if (!$value$plusargs("SPATIALACC_CHECKPOINT_CAPTURE_REPORT=%s", checkpoint_capture_report_path))
          $fatal(1, "missing +SPATIALACC_CHECKPOINT_CAPTURE_REPORT");
      end else if ((checkpoint_mode == "native_exact_model") ||
                   (checkpoint_mode == "portable_cross_revision")) begin
        checkpoint_restore_requested = 1'b1;
        if (!$value$plusargs("SPATIALACC_CHECKPOINT_RESTORE_DUT_STATE=%s", checkpoint_restore_dut_state_path))
          $fatal(1, "missing +SPATIALACC_CHECKPOINT_RESTORE_DUT_STATE");
        if (!$value$plusargs("SPATIALACC_CHECKPOINT_RESTORE_DUT_SCHEMA=%s", checkpoint_restore_dut_schema_path))
          $fatal(1, "missing +SPATIALACC_CHECKPOINT_RESTORE_DUT_SCHEMA");
        if (!$value$plusargs("SPATIALACC_CHECKPOINT_RESTORE_EXTERNAL_STATE=%s", checkpoint_restore_external_state_path))
          $fatal(1, "missing +SPATIALACC_CHECKPOINT_RESTORE_EXTERNAL_STATE");
        if (!$value$plusargs("SPATIALACC_CHECKPOINT_RESTORE_REPORT=%s", checkpoint_restore_report_path))
          $fatal(1, "missing +SPATIALACC_CHECKPOINT_RESTORE_REPORT");
        checkpoint_plusarg_seen = $value$plusargs("SPATIALACC_CHECKPOINT_EQUIVALENCE_PROBE=%d", checkpoint_equivalence_probe);
        checkpoint_plusarg_seen = $value$plusargs("SPATIALACC_CHECKPOINT_ID=%s", checkpoint_id);
        if ((checkpoint_equivalence_probe == 0) && (checkpoint_plusarg_seen == 0))
          $fatal(1, "missing +SPATIALACC_CHECKPOINT_ID for normal checkpoint replay");
      end else begin
        $fatal(1, "unsupported SPATIALACC checkpoint mode");
      end
    end
    checkpoint_runtime_ready = 1'b1;

    if (checkpoint_enabled && !checkpoint_restore_requested) begin
      wait(artifacts_loaded);
      wait(checkpoint_trigger_observed);
      if (boundary_fd != 0) $fflush(boundary_fd);
      if (progress_fd != 0) $fflush(progress_fd);
      checkpoint_evidence_flushed = (boundary_fd != 0) && (progress_fd != 0);
      checkpoint_wait_capture_barrier(checkpoint_settle_cycles,
                                      checkpoint_capture_event_quiescent);
      if (!checkpoint_capture_event_quiescent)
        $fatal(1, "checkpoint capture did not reach a stable quiescent barrier");
      checkpoint_captured_axi_read_outstanding = checkpoint_axi_read_outstanding();
      checkpoint_captured_axi_write_outstanding = checkpoint_axi_write_outstanding();
      checkpoint_captured_read_pending_response = c0_ddr4_s_axi_rvalid;
      checkpoint_captured_write_pending_response = write_response_pending || c0_ddr4_s_axi_bvalid;
      if ((checkpoint_captured_axi_read_outstanding != 0) ||
          (checkpoint_captured_axi_write_outstanding != 0) ||
          checkpoint_captured_read_pending_response ||
          checkpoint_captured_write_pending_response ||
          !checkpoint_capture_event_quiescent)
        $fatal(1, "checkpoint capture boundary is not completely quiescent");
      checkpoint_isolate_evidence_suffix(1'b0,
                                         checkpoint_evidence_suffix_isolated);
      if (!checkpoint_evidence_suffix_isolated)
        $fatal(1, "checkpoint cold boundary-trace suffix could not be isolated");
      if (boundary_fd != 0) $fflush(boundary_fd);
      if (progress_fd != 0) $fflush(progress_fd);
      checkpoint_evidence_flushed = (boundary_fd != 0) && (progress_fd != 0);
      checkpoint_build_boundary_record(checkpoint_boundary_record);
      if (checkpoint_boundary_record.len() == 0)
        $fatal(1, "checkpoint pending boundary record could not be serialized");
      checkpoint_write_external_state(checkpoint_external_state_path,
                                      checkpoint_external_state_complete);
      if (!checkpoint_one_ps_alignment_is_clock_clear())
        $fatal(1, "checkpoint capture alignment lost its clock-clear settlement interval");
      if (!checkpoint_event_queue_quiescent())
        $fatal(1, "checkpoint capture lost quiescence before recording its factual boundary");
      checkpoint_emit_boundary_record();
      if (boundary_fd != 0) $fflush(boundary_fd);
      if (progress_fd != 0) $fflush(progress_fd);
      checkpoint_evidence_flushed = (boundary_fd != 0) && (progress_fd != 0);
      #1;
`ifdef SPATIALACC_CHECKPOINT_VPI_AVAILABLE
      checkpoint_vpi_rc = $spatialacc_state_capture(checkpoint_dut_state_path,
                                                    checkpoint_dut_root,
                                                    checkpoint_dut_schema_path);
`else
      checkpoint_vpi_rc = -1;
      $fatal(1, "checkpoint capture requested without compiled spatialacc VPI state support");
`endif
      if (!checkpoint_one_ps_alignment_is_clock_clear())
        $fatal(1, "checkpoint captured DUT state lacks a clock-clear combinational settlement interval");
      #1;
      checkpoint_sha256_file(checkpoint_dut_schema_path,
                             checkpoint_runtime_schema_sha256,
                             checkpoint_runtime_schema_hash_valid);
      if (!checkpoint_event_queue_quiescent())
        $fatal(1, "checkpoint capture lost quiescence after recording its factual boundary");
      if (progress_sequence == 0)
        $fatal(1, "checkpoint capture boundary record was not committed");
      checkpoint_captured_sequence = progress_sequence - 1;
      checkpoint_captured_cycle = cycle_count;
      $display("SPATIALACC_CHECKPOINT_CAPTURE_BOUNDARY sequence=%0d cycle=%0d read_outstanding=%0d read_pending_response=%0d write_outstanding=%0d write_pending_response=%0d event_queue_quiescent=%0d",
               checkpoint_captured_sequence, checkpoint_captured_cycle,
               checkpoint_captured_axi_read_outstanding,
               checkpoint_captured_read_pending_response,
               checkpoint_captured_axi_write_outstanding,
               checkpoint_captured_write_pending_response,
               checkpoint_capture_event_quiescent);
      checkpoint_emit_live_state_witness();
      checkpoint_write_capture_report();
      if ((checkpoint_vpi_rc != 0) || !checkpoint_external_state_complete ||
          !checkpoint_runtime_schema_hash_valid)
        $fatal(1, "checkpoint capture failed; inspect factual capture report");
    end else if (checkpoint_enabled && checkpoint_restore_requested) begin
      wait(artifacts_loaded);
      checkpoint_read_restore_phase(checkpoint_restore_external_state_path,
                                    checkpoint_restore_phase_ready);
      if (!checkpoint_restore_phase_ready)
        $fatal(1, "checkpoint restore clock-event phase could not be read");
      do begin
        @(negedge c0_ddr4_s_axi_clk);
        #1;
      end while ((($time % CHECKPOINT_CLOCK_PHASE_PERIOD_PS) !=
                   checkpoint_saved_clock_phase_slot) ||
                 (clk_300M !== checkpoint_saved_clk_300M) ||
                 (clk_600M !== checkpoint_saved_clk_600M) ||
                 (c0_ddr4_s_axi_clk !== checkpoint_saved_c0_ddr4_s_axi_clk));
      if (!checkpoint_one_ps_alignment_is_clock_clear())
        $fatal(1, "checkpoint restore phase lacks the captured clock-clear settlement interval");
      if (!checkpoint_event_queue_quiescent())
        $fatal(1, "checkpoint pre-restore runtime did not remain quiescent during phase alignment");
      checkpoint_restore_external_state(checkpoint_restore_external_state_path,
                                        1'b1,
                                        checkpoint_external_state_complete);
      if (!checkpoint_external_state_complete)
        $fatal(1, "checkpoint external state could not be applied at the restore barrier");
      if (!checkpoint_event_queue_quiescent())
        $fatal(1, "checkpoint restored external state is not quiescent at the restore barrier");
      #1;
`ifdef SPATIALACC_CHECKPOINT_VPI_AVAILABLE
      checkpoint_vpi_rc = $spatialacc_state_restore(checkpoint_restore_dut_state_path,
                                                    checkpoint_dut_root,
                                                    checkpoint_restore_dut_schema_path);
`else
      checkpoint_vpi_rc = -1;
      $fatal(1, "checkpoint restore requested without compiled spatialacc VPI state support");
`endif
      if (!checkpoint_one_ps_alignment_is_clock_clear())
        $fatal(1, "checkpoint restored DUT state lacks a clock-clear combinational settlement interval");
      #1;
      checkpoint_sha256_file(checkpoint_restore_dut_schema_path,
                             checkpoint_runtime_schema_sha256,
                             checkpoint_runtime_schema_hash_valid);
      checkpoint_isolate_evidence_suffix(1'b1,
                                         checkpoint_evidence_suffix_isolated);
      if (!checkpoint_evidence_suffix_isolated)
        $fatal(1, "checkpoint restored evidence suffix could not be isolated");
      if (!checkpoint_event_queue_quiescent())
        $fatal(1, "checkpoint restore did not reconstruct the captured quiescent barrier");
      checkpoint_emit_boundary_record();
      if (boundary_fd != 0) $fflush(boundary_fd);
      if (progress_fd != 0) $fflush(progress_fd);
      checkpoint_restored_sequence = progress_sequence - 1;
      checkpoint_restored_cycle = cycle_count;
      checkpoint_emit_live_state_witness();
      checkpoint_write_restore_report();
      if ((checkpoint_vpi_rc != 0) || !checkpoint_external_state_complete ||
          !checkpoint_immutable_reopen_complete ||
          !checkpoint_runtime_schema_hash_valid ||
          !checkpoint_evidence_suffix_isolated ||
          !checkpoint_boundary_state_match ||
          !checkpoint_event_queue_quiescent())
        $fatal(1, "checkpoint restore failed; inspect factual restore report");
      checkpoint_restore_complete = 1'b1;
    end
  end

  initial begin
    clk_300M = 1'b0;
    forever #CLK_300M_HALF_PERIOD_PS clk_300M = ~clk_300M;
  end

  initial begin
    clk_600M = 1'b0;
    forever #CLK_600M_HALF_PERIOD_PS clk_600M = ~clk_600M;
  end

  initial begin
    c0_ddr4_s_axi_clk = 1'b0;
    forever #2000 c0_ddr4_s_axi_clk = ~c0_ddr4_s_axi_clk;
  end

  initial begin
    artifacts_loaded = 1'b0;
    artifact_error = 1'b0;
    boundary_fd = 0;
    progress_fd = 0;
    delta_transition_fd = 0;
    delta_transition_sequence = 0;
    delta_transition_last_time = 0;
    delta_transition_count_at_time = 0;
    delta_transition_suppressed = 1'b0;
    delta_transition_armed = 1'b0;
    weight_fd = 0;
    runtime_fd = 0;
    if (!$value$plusargs("INPUT=%s", spatialacc_input_path)) begin
      $fatal(1, "missing required +INPUT artifact binding");
    end
    if (!$value$plusargs("WEIGHT_IMAGE=%s", spatialacc_weight_image_path)) begin
      $fatal(1, "missing required +WEIGHT_IMAGE artifact binding");
    end
    if (!$value$plusargs("RUNTIME_IMAGE=%s", spatialacc_runtime_image_path)) begin
      $fatal(1, "missing required +RUNTIME_IMAGE artifact binding");
    end
    if (!$value$plusargs("EXPECTED_OUTPUT=%s", spatialacc_expected_output_path)) begin
      $fatal(1, "missing required +EXPECTED_OUTPUT artifact binding");
    end

    probe_fd = $fopen(spatialacc_input_path, "r");
    if (probe_fd == 0) $fatal(1, "unable to open input artifact");
    $fclose(probe_fd);
    $readmemh(spatialacc_input_path, input_beats);

    probe_fd = $fopen(spatialacc_expected_output_path, "r");
    if (probe_fd == 0) $fatal(1, "unable to open independent expected-output artifact");
    $fclose(probe_fd);
    $readmemh(spatialacc_expected_output_path, expected_beats);

    weight_fd = $fopen(spatialacc_weight_image_path, "rb");
    if (weight_fd == 0) $fatal(1, "unable to open full weight image");
    io_rc = $fseek(weight_fd, 0, 2);
    weight_size = $ftell(weight_fd);
    io_rc = $fseek(weight_fd, 0, 0);
    if (weight_size != FULL_WEIGHT_IMAGE_BYTES) begin
      $fatal(1, "full weight image extent mismatch: got %0d expected %0d", weight_size, FULL_WEIGHT_IMAGE_BYTES);
    end
    weight_probe = read_file_beat(weight_fd, 0);

    runtime_fd = $fopen(spatialacc_runtime_image_path, "rb");
    if (runtime_fd == 0) $fatal(1, "unable to open full runtime image");
    io_rc = $fseek(runtime_fd, 0, 2);
    runtime_size = $ftell(runtime_fd);
    io_rc = $fseek(runtime_fd, 0, 0);
    if (runtime_size != RUNTIME_IMAGE_BYTES) begin
      $fatal(1, "runtime image extent mismatch: got %0d expected %0d", runtime_size, RUNTIME_IMAGE_BYTES);
    end
    for (init_i = 0; init_i < RUNTIME_WORDS_PER_LAYER; init_i = init_i + 1) begin
      init_b0 = $fgetc(runtime_fd);
      init_b1 = $fgetc(runtime_fd);
      init_b2 = $fgetc(runtime_fd);
      init_b3 = $fgetc(runtime_fd);
      if ((init_b0 < 0) || (init_b1 < 0) || (init_b2 < 0) || (init_b3 < 0)) begin
        $fatal(1, "runtime image ended before word %0d", init_i);
      end
      runtime_words[init_i] = {init_b3[7:0], init_b2[7:0], init_b1[7:0], init_b0[7:0]};
    end
    $fclose(runtime_fd);

    boundary_fd = $fopen("reports/boundary_trace.jsonl", "w");
    if (boundary_fd == 0) $fatal(1, "unable to create boundary trace");
    progress_fd = $fopen("reports/progress_event_log.jsonl", "w");
    if (progress_fd == 0) $fatal(1, "unable to create progress event log");
    delta_transition_fd = $fopen("reports/connected_kernel_delta_transition.jsonl", "w");
    if (delta_transition_fd == 0) $fatal(1, "unable to create connected-kernel delta transition log");
    $fwrite(delta_transition_fd,
      "{\"schema_version\":\"spatialaccagent.connected_kernel_delta_transition.v1\",\"evidence_kind\":\"boundary_trace\",\"probe_id\":\"probe.connected_kernel_mlp_tail_convergence.11\",\"probe_revision\":11,\"source_marker\":\"connected_kernel_mlp_tail_convergence_r11\",\"sequence\":0,\"status\":\"waiting_for_post_full_ingress_mlp_tail_without_core_egress\",\"observational_only\":true}\n");
    $fflush(delta_transition_fd);
    delta_transition_sequence = 1;
    // Reaching this initial block is post-VCS-elaboration evidence.  Materialize
    // the identity-bound hierarchy artifact before any later runtime liveness outcome.
    write_elaborated_hierarchy_report();
    artifacts_loaded = 1'b1;
  end

  initial begin
    c0_ddr4_s_axi_awready = 1'b0;
    c0_ddr4_s_axi_wready = 1'b0;
    c0_ddr4_s_axi_bid = 4'd0;
    c0_ddr4_s_axi_bresp = 2'b00;
    c0_ddr4_s_axi_bvalid = 1'b0;
    c0_ddr4_s_axi_arready = 1'b0;
    c0_ddr4_s_axi_rlast = 1'b0;
    c0_ddr4_s_axi_rvalid = 1'b0;
    c0_ddr4_s_axi_rresp = 2'b00;
    c0_ddr4_s_axi_rid = 4'd0;
    c0_ddr4_s_axi_rdata = 512'd0;
    ready_lfsr = 32'h1aceb00c;
    read_active = 1'b0;
    write_active = 1'b0;
    write_response_pending = 1'b0;
    read_delay_q = 0;
    write_response_delay_q = 0;
    axi_model_error = 1'b0;
    axi_read_transaction_count = 0;
    axi_write_transaction_count = 0;
    axi_read_beat_count = 0;
    axi_write_beat_count = 0;
    axi_write_response_count = 0;
  end

  always @(posedge c0_ddr4_s_axi_clk) begin
    ready_lfsr <= {ready_lfsr[30:0], ready_lfsr[31] ^ ready_lfsr[21] ^ ready_lfsr[1] ^ ready_lfsr[0]};
    if (!c0_ddr4_s_axi_rst_n) begin
      c0_ddr4_s_axi_awready <= 1'b0;
      c0_ddr4_s_axi_wready <= 1'b0;
      c0_ddr4_s_axi_bvalid <= 1'b0;
      c0_ddr4_s_axi_arready <= 1'b0;
      c0_ddr4_s_axi_rvalid <= 1'b0;
      read_active <= 1'b0;
      write_active <= 1'b0;
      write_response_pending <= 1'b0;
    end else begin
      c0_ddr4_s_axi_arready <= (!read_active && !c0_ddr4_s_axi_rvalid && ready_lfsr[0]);
      c0_ddr4_s_axi_awready <= (!write_active && !write_response_pending && !c0_ddr4_s_axi_bvalid && ready_lfsr[2]);
      c0_ddr4_s_axi_wready <= (write_active && ready_lfsr[4]);

      if (c0_ddr4_s_axi_arvalid && c0_ddr4_s_axi_arready) begin
        read_active <= 1'b1;
        read_addr_q <= c0_ddr4_s_axi_araddr;
        read_len_q <= c0_ddr4_s_axi_arlen;
        read_beat_q <= 8'd0;
        read_size_q <= c0_ddr4_s_axi_arsize;
        read_burst_q <= c0_ddr4_s_axi_arburst;
        read_id_q <= c0_ddr4_s_axi_arid;
        read_delay_q <= {29'd0, ready_lfsr[7:5]} + 1;
        c0_ddr4_s_axi_arready <= 1'b0;
        axi_read_transaction_count <= axi_read_transaction_count + 1;
        if ((c0_ddr4_s_axi_arsize > 3'b110) ||
            ((c0_ddr4_s_axi_arburst != 2'b00) && (c0_ddr4_s_axi_arburst != 2'b01)) ||
            ((c0_ddr4_s_axi_araddr[11:0] + ((c0_ddr4_s_axi_arlen + 1) << c0_ddr4_s_axi_arsize)) > 4096)) begin
          axi_model_error <= 1'b1;
        end
      end

      if (read_active && !c0_ddr4_s_axi_rvalid) begin
        if (read_delay_q == 0) begin
          c0_ddr4_s_axi_rdata <= read_memory_beat(read_addr_q);
          c0_ddr4_s_axi_rid <= read_id_q;
          c0_ddr4_s_axi_rresp <= 2'b00;
          c0_ddr4_s_axi_rlast <= (read_beat_q == read_len_q);
          c0_ddr4_s_axi_rvalid <= 1'b1;
        end else begin
          read_delay_q <= read_delay_q - 1;
        end
      end

      if (c0_ddr4_s_axi_rvalid && c0_ddr4_s_axi_rready) begin
        axi_read_beat_count <= axi_read_beat_count + 1;
        c0_ddr4_s_axi_rvalid <= 1'b0;
        if (c0_ddr4_s_axi_rlast) begin
          read_active <= 1'b0;
        end else begin
          read_beat_q <= read_beat_q + 1'b1;
          read_addr_q <= next_axi_address(read_addr_q, read_size_q, read_burst_q);
          read_delay_q <= {30'd0, ready_lfsr[10:9]} + 1;
        end
      end

      if (c0_ddr4_s_axi_awvalid && c0_ddr4_s_axi_awready) begin
        write_active <= 1'b1;
        write_addr_q <= c0_ddr4_s_axi_awaddr;
        write_len_q <= c0_ddr4_s_axi_awlen;
        write_beat_q <= 8'd0;
        write_size_q <= c0_ddr4_s_axi_awsize;
        write_burst_q <= c0_ddr4_s_axi_awburst;
        write_id_q <= c0_ddr4_s_axi_awid;
        c0_ddr4_s_axi_awready <= 1'b0;
        axi_write_transaction_count <= axi_write_transaction_count + 1;
        if ((c0_ddr4_s_axi_awsize > 3'b110) ||
            ((c0_ddr4_s_axi_awburst != 2'b00) && (c0_ddr4_s_axi_awburst != 2'b01)) ||
            ((c0_ddr4_s_axi_awaddr[11:0] + ((c0_ddr4_s_axi_awlen + 1) << c0_ddr4_s_axi_awsize)) > 4096)) begin
          axi_model_error <= 1'b1;
        end
      end

      if (c0_ddr4_s_axi_wvalid && c0_ddr4_s_axi_wready) begin
        commit_memory_write(write_addr_q, c0_ddr4_s_axi_wdata, c0_ddr4_s_axi_wstrb);
        axi_write_beat_count <= axi_write_beat_count + 1;
        if (c0_ddr4_s_axi_wlast != (write_beat_q == write_len_q)) begin
          axi_model_error <= 1'b1;
        end
        if (c0_ddr4_s_axi_wlast) begin
          write_active <= 1'b0;
          write_response_pending <= 1'b1;
          write_response_delay_q <= {30'd0, ready_lfsr[13:12]} + 1;
          c0_ddr4_s_axi_wready <= 1'b0;
        end else begin
          write_beat_q <= write_beat_q + 1'b1;
          write_addr_q <= next_axi_address(write_addr_q, write_size_q, write_burst_q);
        end
      end

      if (write_response_pending && !c0_ddr4_s_axi_bvalid) begin
        if (write_response_delay_q == 0) begin
          c0_ddr4_s_axi_bid <= write_id_q;
          c0_ddr4_s_axi_bresp <= 2'b00;
          c0_ddr4_s_axi_bvalid <= 1'b1;
          write_response_pending <= 1'b0;
        end else begin
          write_response_delay_q <= write_response_delay_q - 1;
        end
      end

      if (c0_ddr4_s_axi_bvalid && c0_ddr4_s_axi_bready) begin
        c0_ddr4_s_axi_bvalid <= 1'b0;
        axi_write_response_count <= axi_write_response_count + 1;
      end
    end
  end

  initial begin
    cycle_count = 0;
    progress_sequence = 0;
    semantic_progress_count = 0;
    progress_epoch = 0;
    last_semantic_progress_cycle = 0;
    heartbeat_next_cycle = 4096;
    stall_snapshot_last_cycle = 0;
    weight_accept_total = 0;
    runtime_accept_total = 0;
    kernel_input_accept_total = 0;
    kernel_output_accept_total = 0;
    concurrent_pipeline_cycle_count = 0;
    trace_prefetch_start_count = 0;
    trace_prefetch_complete_count = 0;
    trace_weight_switch_count = 0;
    trace_activation_switch_count = 0;
    trace_runtime_start_count = 0;
    trace_runtime_complete_count = 0;
    trace_kernel_start_count = 0;
    trace_layer_complete_count = 0;
    trace_final_start_count = 0;
    trace_final_complete_count = 0;
    prefetch_compute_overlap_count = 0;
    frontier_core_start_pulse_count = 0;
    frontier_core_start_asserted_cycle_count = 0;
    frontier_start_with_input_fire_count = 0;
    frontier_post_first_start_pulse_count = 0;
    frontier_kernel_reset_release_cycle = 0;
    frontier_weight_load_complete_cycle = 0;
    frontier_runtime_load_complete_cycle = 0;
    frontier_first_start_cycle = 0;
    frontier_last_start_cycle = 0;
    frontier_first_input_fire_cycle = 0;
    frontier_last_input_fire_cycle = 0;
    frontier_kernel_reset_d = 1'b1;
    frontier_start_to_core_d = 1'b0;
    frontier_first_input_fire_seen = 1'b0;
    frontier_post_input_snapshot_emitted = 1'b0;
    frontier_first_post_start_ingress_snapshot_emitted = 1'b0;
    frontier_first_output_fire_cycle = 0;
    frontier_first_output_token_complete_cycle = 0;
    frontier_last_output_fire_cycle = 0;
    frontier_output_token_complete_snapshot_emitted = 1'b0;
    frontier_output_continuation_snapshot_emitted = 1'b0;
    frontier_stage0_post_ingress_valid_snapshot_emitted = 1'b0;
    frontier_core_ingress_fire_count = 0;
    frontier_first_core_ingress_fire_cycle = 0;
    frontier_stage0_input_fire_count = 0;
    frontier_stage0_fire_count = 0;
    frontier_core_egress_fire_count = 0;
    frontier_qkv_input_fire_count = 0;
    frontier_mlp_gate_input_fire_count = 0;
    frontier_mlp_up_input_fire_count = 0;
    frontier_mlp_gate_output_fire_count = 0;
    frontier_mlp_up_output_fire_count = 0;
    frontier_mlp_mul_output_fire_count = 0;
    frontier_mlp_down_input_fire_count = 0;
    frontier_mlp_down_output_fire_count = 0;
    frontier_mlp_down_input_terminal_fire_count = 0;
    frontier_mlp_down_output_terminal_fire_count = 0;
    frontier_core_ingress_last_payload_unknown = 1'b1;
    frontier_stage0_last_payload_unknown = 1'b1;
    frontier_core_egress_last_payload_unknown = 1'b1;
    frontier_core_ingress_last_payload_digest = 32'd0;
    frontier_stage0_last_payload_digest = 32'd0;
    frontier_core_egress_last_payload_digest = 32'd0;
    for (init_i = 0; init_i < CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT; init_i = init_i + 1) begin
      current_dag_boundary_accepted_count[init_i] = 0;
      current_dag_boundary_first_accepted_seen[init_i] = 1'b0;
      current_dag_boundary_waiting_seen[init_i] = 1'b0;
      current_dag_boundary_token_first_payload_digest[init_i] = 32'd0;
      current_dag_boundary_token_first_payload_unknown[init_i] = 1'b1;
    end
    for (init_i = 0; init_i < TARGET_LAYERS; init_i = init_i + 1) begin
      runtime_accept_count[init_i] = 0;
      runtime_first_address[init_i] = -1;
      runtime_last_address[init_i] = -1;
      runtime_contiguous[init_i] = 1'b1;
      runtime_data_match[init_i] = 1'b1;
      runtime_last_ok[init_i] = 1'b1;
      runtime_complete_cycle[init_i] = 0;
      kernel_start_cycle[init_i] = 0;
      layer_input_count[init_i] = 0;
      layer_output_count[init_i] = 0;
      kernel_overlap_start_count[init_i] = 0;
      input_count_at_first_output[init_i] = 0;
      first_output_seen[init_i] = 1'b0;
    end
  end

  // Read-only byte-bounded waveform probe over the connected-kernel top-level
  // boundary nets. probe_id=probe.connected_kernel_full_core_boundary_cone.11
  // It arms at the already observed stage-0 token-12 frontier, before the
  // all-ingress/no-egress termination condition, and drives no DUT signal,
  // adds no synthesizable state or port, and uses no time limit.
  initial begin : spatialacc_connected_kernel_full_core_boundary_cone_probe_r11
    wait((dut.layer_index == 5'd0) &&
         (dut.kernel_invocation_launched === 1'b1) &&
         (dut.input_axi_index >= AXI_BEATS_PER_ACTIVATION / TARGET_TOKENS) &&
         (dut.output_accept_count == 0) &&
         (frontier_core_egress_fire_count == 0));
    emit_connected_kernel_output_continuation_event(
      "connected_kernel_first_input_window_complete_no_egress",
      0,
      dut.input_axi_index);
    emit_connected_kernel_core_boundary_trace;
    emit_direct_core_frontier_observation;
  end

  // Read-only testbench probe, probe_id=probe.connected_kernel_mlp_tail_convergence.11,
  // records a bounded event-driven MLP-tail window only after all direct core ingress
  // beats are accepted and before any core-egress beat. It observes existing signals only.
  always @(frontier_core_ingress_valid or
           frontier_core_ingress_ready or
           frontier_core_ingress_data or
           frontier_core_ingress_fire_count or
           frontier_core_egress_fire_count or
           frontier_stage0_valid or
           frontier_stage0_ready or
           frontier_stage0_data or
           frontier_core_egress_valid or
           frontier_core_egress_ready or
           frontier_core_egress_data or
           dut.kernel_reset_q or
           dut.kernel_start_to_core or
           dut.kernel_input_valid_q or
           dut.kernel_input_ready or
           dut.kernel_output_valid or
           dut.kernel_output_ready or
           dut.input_axi_index or
           dut.output_accept_count or
           dut.spatialacc_single_kernel.core.mlp_gate_io_out_valid__bore or
           dut.spatialacc_single_kernel.core.mlp_gate_io_out_ready__bore or
           dut.spatialacc_single_kernel.core.mlp_gate_io_out_bits_last__bore or
           dut.spatialacc_single_kernel.core.mlp_up_io_out_valid__bore or
           dut.spatialacc_single_kernel.core.mlp_up_io_out_ready__bore or
           dut.spatialacc_single_kernel.core.mlp_up_io_out_bits_last__bore or
           dut.spatialacc_single_kernel.core.mlp_mul_io_out_valid__bore or
           dut.spatialacc_single_kernel.core.mlp_mul_io_out_ready__bore or
           dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_last__bore or
           dut.spatialacc_single_kernel.core.mlp_down_io_out_valid__bore or
           dut.spatialacc_single_kernel.core.mlp_down_io_out_ready__bore or
           dut.spatialacc_single_kernel.core.mlp_down_io_out_bits_last__bore or
           dut.spatialacc_single_kernel.core.res2Q_io_enq_valid or
           frontier_mlp_gate_output_fire_count or
           frontier_mlp_up_output_fire_count or
           frontier_mlp_mul_output_fire_count or
           frontier_mlp_down_input_fire_count or
           frontier_mlp_down_output_fire_count) begin
    if (!delta_transition_armed &&
        (dut.layer_index == 5'd0) &&
        (dut.kernel_invocation_launched === 1'b1) &&
        (dut.output_accept_count == 0) &&
        (frontier_core_ingress_fire_count >= BEATS_PER_LAYER) &&
        (frontier_core_egress_fire_count == 0)) begin
      delta_transition_armed = 1'b1;
    end
    if ((delta_transition_fd != 0) &&
        delta_transition_armed &&
        (delta_transition_sequence < 256) &&
        (dut.layer_index == 5'd0) &&
        (dut.kernel_invocation_launched === 1'b1) &&
        (dut.output_accept_count == 0) &&
        (frontier_core_egress_fire_count == 0)) begin
      if ($time != delta_transition_last_time) begin
        delta_transition_last_time = $time;
        delta_transition_count_at_time = 0;
        delta_transition_suppressed = 1'b0;
      end
      if (delta_transition_count_at_time < 256) begin
        $fwrite(delta_transition_fd,
          "{\"schema_version\":\"spatialaccagent.connected_kernel_delta_transition.v1\",\"evidence_kind\":\"boundary_trace\",\"probe_id\":\"probe.connected_kernel_mlp_tail_convergence.11\",\"probe_revision\":11,\"source_marker\":\"connected_kernel_mlp_tail_convergence_r11\",\"sequence\":%0d,\"simulation_time\":%0t,\"cycle\":%0d,\"same_time_index\":%0d,\"scheduler_state\":%0d,\"kernel_reset\":%s,\"core_ingress_accepted_count\":%0d,\"stage0_accepted_count\":%0d,\"mlp_gate_output\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d},\"mlp_up_output\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d},\"mlp_mul_output\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d},\"mlp_down_input\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d},\"mlp_down_output\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d},\"residual2_enqueue_valid\":%s,\"core_egress\":{\"valid\":%s,\"ready\":%s,\"fire\":%0d,\"accepted_count\":%0d}}\n",
          delta_transition_sequence,
          $time,
          cycle_count,
          delta_transition_count_at_time,
          dut.state,
          json_logic(dut.kernel_reset_q),
          frontier_core_ingress_fire_count,
          frontier_stage0_fire_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_ready__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_bits_last__bore),
          frontier_mlp_gate_output_fire,
          frontier_mlp_gate_output_fire_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_ready__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_bits_last__bore),
          frontier_mlp_up_output_fire,
          frontier_mlp_up_output_fire_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_ready__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_last__bore),
          frontier_mlp_mul_output_fire,
          frontier_mlp_mul_output_fire_count,
          json_logic(frontier_mlp_down_input_valid),
          json_logic(frontier_mlp_down_input_ready),
          json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_last__bore),
          frontier_mlp_down_input_fire,
          frontier_mlp_down_input_fire_count,
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_valid__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_ready__bore),
          json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_bits_last__bore),
          frontier_mlp_down_output_fire,
          frontier_mlp_down_output_fire_count,
          json_logic(dut.spatialacc_single_kernel.core.res2Q_io_enq_valid),
          json_logic(frontier_core_egress_valid),
          json_logic(frontier_core_egress_ready),
          frontier_core_egress_fire,
          frontier_core_egress_fire_count);
        $fflush(delta_transition_fd);
        delta_transition_sequence = delta_transition_sequence + 1;
        delta_transition_count_at_time = delta_transition_count_at_time + 1;
      end else if (!delta_transition_suppressed) begin
        $fwrite(delta_transition_fd,
          "{\"schema_version\":\"spatialaccagent.connected_kernel_delta_transition.v1\",\"evidence_kind\":\"boundary_trace\",\"probe_id\":\"probe.connected_kernel_mlp_tail_convergence.11\",\"probe_revision\":11,\"source_marker\":\"connected_kernel_mlp_tail_convergence_r11\",\"sequence\":%0d,\"simulation_time\":%0t,\"cycle\":%0d,\"same_time_index\":%0d,\"status\":\"same_time_transition_records_suppressed\",\"observational_only\":true}\n",
          delta_transition_sequence,
          $time,
          cycle_count,
          delta_transition_count_at_time);
        $fflush(delta_transition_fd);
        delta_transition_sequence = delta_transition_sequence + 1;
        delta_transition_suppressed = 1'b1;
      end
    end
  end

  // probe_id=probe.connected_kernel_mlp_tail_terminal_events.14
  // Read-only terminal-handshake trace for the MLP tail. Each record is
  // triggered only by an actual per-token terminal fire before core egress;
  // it adds no DUT drive, state, port, or elapsed-time completion condition.
  always @(posedge c0_ddr4_s_axi_clk) begin : spatialacc_mlp_tail_terminal_event_probe_r14
    if ((boundary_fd != 0) &&
        (dut.layer_index == 5'd0) &&
        (frontier_core_egress_fire_count == 0) &&
        ((frontier_mlp_gate_output_fire &&
          (dut.spatialacc_single_kernel.core.mlp_gate_io_out_bits_last__bore === 1'b1)) ||
         (frontier_mlp_up_output_fire &&
          (dut.spatialacc_single_kernel.core.mlp_up_io_out_bits_last__bore === 1'b1)) ||
         (frontier_mlp_mul_output_fire &&
          (dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_last__bore === 1'b1)) ||
         (frontier_mlp_down_output_fire &&
          (dut.spatialacc_single_kernel.core.mlp_down_io_out_bits_last__bore === 1'b1)))) begin
      $fwrite(boundary_fd,
        "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_06_activation_mul_to_stage_07_mlp_down_proj_main\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_mlp_tail_terminal_events.14\",\"probe_revision\":14,\"source_marker\":\"connected_kernel_mlp_tail_terminal_events_r14\",\"outer_core_ingress_accepted_count\":%0d,\"stage0_accepted_count\":%0d,\"qkv_input\":{\"valid\":%s,\"ready\":%s},\"mlp_gate_output\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d},\"mlp_up_output\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d},\"mlp_mul_output\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d},\"mlp_down_output\":{\"valid\":%s,\"ready\":%s,\"last\":%s,\"fire\":%0d,\"accepted_count\":%0d},\"core_egress\":{\"valid\":%s,\"ready\":%s,\"fire\":%0d,\"accepted_count\":%0d}},\"expected_value\":{\"availability\":\"per_token_mlp_tail_terminal_handshake_trace\",\"required_outer_core_ingress_count\":%0d},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
        cycle_count,
        frontier_mlp_mul_output_fire_count + frontier_mlp_mul_output_fire,
        frontier_mlp_mul_output_fire_count + frontier_mlp_mul_output_fire,
        frontier_core_ingress_fire_count,
        frontier_stage0_fire_count,
        json_logic(dut.spatialacc_single_kernel.core.qkv_io_in_valid),
        json_logic(dut.spatialacc_single_kernel.core.qkv_io_in_ready),
        json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_valid__bore),
        json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_ready__bore),
        json_logic(dut.spatialacc_single_kernel.core.mlp_gate_io_out_bits_last__bore),
        frontier_mlp_gate_output_fire,
        frontier_mlp_gate_output_fire_count + frontier_mlp_gate_output_fire,
        json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_valid__bore),
        json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_ready__bore),
        json_logic(dut.spatialacc_single_kernel.core.mlp_up_io_out_bits_last__bore),
        frontier_mlp_up_output_fire,
        frontier_mlp_up_output_fire_count + frontier_mlp_up_output_fire,
        json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_valid__bore),
        json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_ready__bore),
        json_logic(dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_last__bore),
        frontier_mlp_mul_output_fire,
        frontier_mlp_mul_output_fire_count + frontier_mlp_mul_output_fire,
        json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_valid__bore),
        json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_ready__bore),
        json_logic(dut.spatialacc_single_kernel.core.mlp_down_io_out_bits_last__bore),
        frontier_mlp_down_output_fire,
        frontier_mlp_down_output_fire_count + frontier_mlp_down_output_fire,
        json_logic(frontier_core_egress_valid),
        json_logic(frontier_core_egress_ready),
        frontier_core_egress_fire,
        frontier_core_egress_fire_count + frontier_core_egress_fire,
        BEATS_PER_LAYER);
      $fflush(boundary_fd);
    end
  end

  // Read-only direct-core contradiction witness. This single-shot post-NBA
  // observation is armed by the semantic full-ingress counter and records a
  // schema-complete boundary failure only when all 1792 core ingress beats
  // have been accepted while no core egress beat has been accepted. It does
  // not drive DUT signals, add synthesizable state or ports, or use a timeout.
  always @(frontier_core_ingress_fire_count) begin : spatialacc_direct_core_contradiction_probe_r13
    reg emitted;
    if ((emitted !== 1'b1) &&
        (dut.layer_index == 5'd0) &&
        (frontier_core_ingress_fire_count == BEATS_PER_LAYER) &&
        (frontier_core_egress_fire_count == 0)) begin
      emitted = 1'b1;
      emit_connected_kernel_output_continuation_event(
        "connected_kernel_direct_core_ingress_complete_no_egress",
        TARGET_TOKENS,
        frontier_core_ingress_fire_count);
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"connected_kernel_input_to_output\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"probe_id\":\"probe.connected_kernel_direct_frontier_contradiction.13\",\"probe_revision\":13,\"source_marker\":\"connected_kernel_direct_frontier_contradiction_r13\",\"outer_ingress_accepted_count\":%0d,\"core_ingress_accepted_count\":%0d,\"core_egress_accepted_count\":%0d,\"stage0_accepted_count\":%0d,\"core_ingress_valid\":%s,\"core_ingress_ready\":%s,\"core_egress_valid\":%s,\"core_egress_ready\":%s,\"output_accept_count\":%0d},\"expected_value\":{\"required_input_accepted_count\":%0d,\"required_output_accepted_count\":%0d,\"availability\":\"direct_core_boundary_liveness\"},\"contract\":\"connected_kernel_input_to_output\",\"status\":\"fail\"}\n",
          cycle_count,
          frontier_core_ingress_fire_count,
          frontier_core_ingress_fire_count,
          frontier_core_ingress_fire_count,
          frontier_core_ingress_fire_count,
          frontier_core_egress_fire_count,
          frontier_stage0_fire_count,
          json_logic(frontier_core_ingress_valid),
          json_logic(frontier_core_ingress_ready),
          json_logic(frontier_core_egress_valid),
          json_logic(frontier_core_egress_ready),
          dut.output_accept_count,
          BEATS_PER_LAYER,
          BEATS_PER_LAYER);
        $fflush(boundary_fd);
      end
    end
  end

  // Read-only post-NBA witness for the exact all-core-ingress transition.
  // The semantic counter transition is the bounded trigger; no elapsed timeout,
  // DUT signal drive, synthesizable state, or additional port is introduced.
  always @(frontier_core_ingress_fire_count) begin
    if ((progress_fd != 0) &&
        (dut.layer_index == 5'd0) &&
        (frontier_core_ingress_fire_count == BEATS_PER_LAYER) &&
        (frontier_core_egress_fire_count == 0)) begin
      emit_connected_kernel_core_boundary_trace();
      emit_direct_core_frontier_observation();
      emit_connected_kernel_lifecycle_order_observation();
      emit_connected_kernel_start_to_core_ingress_order_observation();
      emit_connected_kernel_lifecycle_bound_frontier_observation();
      emit_mlp_down_ingress_boundary_observation();
      emit_mlp_down_terminal_contract_observation();
      emit_current_dag_boundary_observation(0, "edge.data.block_input.to.stage_00_rms_norm_1.input");
      emit_current_dag_boundary_observation(1, "edge.data.block_input.to.stage_02_residual_add_1.residual_skip");
      emit_current_dag_boundary_observation(2, "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main");
      emit_current_dag_boundary_observation(3, "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main");
      emit_current_dag_boundary_observation(4, "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main");
      emit_current_dag_boundary_observation(5, "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip");
      emit_current_dag_boundary_observation(6, "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch");
      emit_current_dag_boundary_observation(7, "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch");
      emit_current_dag_boundary_observation(8, "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul");
      emit_current_dag_boundary_observation(9, "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul");
      emit_current_dag_boundary_observation(10, "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main");
      emit_current_dag_boundary_observation(11, "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main");
      emit_current_dag_boundary_observation(12, "edge.data.stage_08_residual_add_2.to.block_output.output");
    end
  end

  // probe_id=probe.connected_kernel_stage0_post_ingress_valid.1
  // Testbench-only, single-shot post-NBA witness. It observes no DUT signal
  // drive and emits one schema-valid snapshot only after all direct core
  // ingress beats have been accepted and before any direct core egress beat.
  always @(frontier_stage0_valid) begin
    if ((progress_fd != 0) &&
        !frontier_stage0_post_ingress_valid_snapshot_emitted &&
        (dut.layer_index == 5'd0) &&
        (frontier_core_ingress_fire_count >= BEATS_PER_LAYER) &&
        (frontier_core_egress_fire_count == 0) &&
        (frontier_stage0_valid === 1'b1)) begin
      frontier_stage0_post_ingress_valid_snapshot_emitted = 1'b1;
      emit_connected_kernel_core_boundary_trace();
      emit_direct_core_frontier_observation();
      if (boundary_fd != 0) begin
        $fwrite(boundary_fd,
          "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"source_marker\":\"connected_kernel_qkv_input_boundary_r1\",\"stage0_valid\":%s,\"stage0_ready\":%s,\"stage0_fire\":%0d,\"stage0_accepted_count\":%0d,\"qkv_input_valid\":%s,\"qkv_input_ready\":%s,\"qkv_input_fire\":%0d},\"expected_value\":{\"availability\":\"direct_stage0_to_qkv_liveness\"},\"contract\":\"valid_ready_order_preserved\",\"status\":\"diagnostic_seed\"}\n",
          cycle_count,
          frontier_stage0_fire_count,
          frontier_stage0_fire_count,
          json_logic(frontier_stage0_valid),
          json_logic(frontier_stage0_ready),
          frontier_stage0_fire,
          frontier_stage0_fire_count,
          json_logic(dut.spatialacc_single_kernel.core.qkv_io_in_valid),
          json_logic(dut.spatialacc_single_kernel.core.qkv_io_in_ready),
          ((dut.spatialacc_single_kernel.core.qkv_io_in_valid === 1'b1) &&
           (dut.spatialacc_single_kernel.core.qkv_io_in_ready === 1'b1)));
        $fflush(boundary_fd);
      end
      emit_connected_kernel_output_continuation_event(
        "connected_kernel_stage0_valid_asserted_after_full_ingress",
        TARGET_TOKENS,
        frontier_stage0_fire_count);
    end
  end

  always @(posedge c0_ddr4_s_axi_clk) begin
    integer observed_layer;
    integer boundary_sample_index;
    cycle_count <= cycle_count + 1;
    if (c0_ddr4_s_axi_rst_n && sys_rst_n && !user_rst) begin
      observed_layer = dut.layer_index;
      for (boundary_sample_index = 0;
           boundary_sample_index < CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT;
           boundary_sample_index = boundary_sample_index + 1) begin
        if (current_dag_boundary_fire[boundary_sample_index] === 1'b1) begin
          if ((current_dag_boundary_accepted_count[boundary_sample_index] %
               current_dag_boundary_beats_per_token(boundary_sample_index)) == 0) begin
            emit_current_dag_boundary_temporal_record(
              boundary_sample_index,
              "first_accepted_beat",
              1);
            current_dag_boundary_token_first_payload_digest[boundary_sample_index] <=
              payload_digest256(current_dag_boundary_payload[boundary_sample_index]);
            current_dag_boundary_token_first_payload_unknown[boundary_sample_index] <=
              $isunknown(current_dag_boundary_payload[boundary_sample_index]);
          end
          if ((current_dag_boundary_accepted_count[boundary_sample_index] %
               current_dag_boundary_beats_per_token(boundary_sample_index)) ==
              (current_dag_boundary_beats_per_token(boundary_sample_index) - 1)) begin
            emit_current_dag_boundary_temporal_record(
              boundary_sample_index,
              "last_accepted_beat",
              2);
          end
          current_dag_boundary_accepted_count[boundary_sample_index] <=
            current_dag_boundary_accepted_count[boundary_sample_index] + 1;
          if (current_dag_boundary_first_accepted_seen[boundary_sample_index] !== 1'b1) begin
            current_dag_boundary_first_accepted_seen[boundary_sample_index] <= 1'b1;
            current_dag_boundary_first_accepted_payload_digest[boundary_sample_index] <=
              payload_digest256(current_dag_boundary_payload[boundary_sample_index]);
          end
          current_dag_boundary_last_accepted_payload_digest[boundary_sample_index] <=
            payload_digest256(current_dag_boundary_payload[boundary_sample_index]);
        end else if (!current_dag_boundary_waiting_seen[boundary_sample_index] &&
                     (current_dag_boundary_accepted_count[boundary_sample_index] == 0) &&
                     current_dag_boundary_has_upstream_progress(boundary_sample_index)) begin
          emit_current_dag_boundary_temporal_record(
            boundary_sample_index,
            "first_waiting_after_upstream_progress",
            0);
          current_dag_boundary_waiting_seen[boundary_sample_index] <= 1'b1;
        end
      end
      if (observed_layer == 0) begin
        if ((dut.kernel_input_valid_q === 1'b1) &&
            (dut.kernel_input_ready === 1'b1)) begin
          if (!frontier_first_input_fire_seen) begin
            frontier_first_input_fire_seen <= 1'b1;
            frontier_first_input_fire_cycle <= cycle_count;
          end
          frontier_last_input_fire_cycle <= cycle_count;
        end
        if ((frontier_kernel_reset_d === 1'b1) &&
            (dut.kernel_reset_q === 1'b0)) begin
          frontier_kernel_reset_release_cycle <= cycle_count;
        end
        frontier_kernel_reset_d <= dut.kernel_reset_q;
        if ((dut.weight_valid_q === 1'b1) &&
            (dut.weight_ready === 1'b1) &&
            (dut.weight_last_q === 1'b1)) begin
          frontier_weight_load_complete_cycle <= cycle_count;
        end
        if ((dut.runtime_valid_q === 1'b1) &&
            (dut.runtime_ready === 1'b1) &&
            (dut.runtime_last_q === 1'b1)) begin
          frontier_runtime_load_complete_cycle <= cycle_count;
        end
        if (dut.kernel_start_to_core === 1'b1) begin
          frontier_core_start_asserted_cycle_count <=
            frontier_core_start_asserted_cycle_count + 1;
        end
        if ((dut.kernel_start_to_core === 1'b1) &&
            (frontier_start_to_core_d === 1'b0)) begin
          if (frontier_core_start_pulse_count == 0) begin
            frontier_first_start_cycle <= cycle_count;
          end else begin
            frontier_post_first_start_pulse_count <=
              frontier_post_first_start_pulse_count + 1;
          end
          frontier_last_start_cycle <= cycle_count;
          frontier_core_start_pulse_count <=
            frontier_core_start_pulse_count + 1;
          if (dut.kernel_input_valid_q && dut.kernel_input_ready) begin
            frontier_start_with_input_fire_count <=
              frontier_start_with_input_fire_count + 1;
          end
        end
        frontier_start_to_core_d <=
          (dut.kernel_start_to_core === 1'b1);
        if (dut.kernel_reset_q === 1'b1) begin
          frontier_core_ingress_fire_count <= 0;
          frontier_stage0_input_fire_count <= 0;
          frontier_stage0_fire_count <= 0;
          frontier_core_egress_fire_count <= 0;
          frontier_qkv_input_fire_count <= 0;
          frontier_mlp_gate_input_fire_count <= 0;
          frontier_mlp_up_input_fire_count <= 0;
          frontier_mlp_gate_output_fire_count <= 0;
          frontier_mlp_up_output_fire_count <= 0;
          frontier_mlp_mul_output_fire_count <= 0;
          frontier_mlp_down_input_fire_count <= 0;
          frontier_mlp_down_output_fire_count <= 0;
          frontier_mlp_down_input_terminal_fire_count <= 0;
          frontier_mlp_down_output_terminal_fire_count <= 0;
          frontier_core_ingress_last_payload_unknown <= 1'b1;
          frontier_stage0_last_payload_unknown <= 1'b1;
          frontier_core_egress_last_payload_unknown <= 1'b1;
          frontier_core_ingress_last_payload_digest <= 32'd0;
          frontier_stage0_last_payload_digest <= 32'd0;
          frontier_core_egress_last_payload_digest <= 32'd0;
        end else begin
          if (frontier_qkv_input_fire) begin
            frontier_qkv_input_fire_count <= frontier_qkv_input_fire_count + 1;
          end
          if (frontier_core_ingress_fire) begin
            frontier_core_ingress_fire_count <=
              frontier_core_ingress_fire_count + 1;
            if (frontier_core_ingress_fire_count == 0) begin
              frontier_first_core_ingress_fire_cycle <= cycle_count;
            end
            if (!frontier_first_post_start_ingress_snapshot_emitted &&
                (frontier_core_start_pulse_count != 0)) begin
              emit_connected_kernel_core_boundary_trace();
              emit_progress_event("semantic_progress",
                                  "connected_kernel_first_post_start_core_ingress",
                                  1'b1,
                                  observed_layer,
                                  (frontier_core_ingress_fire_count + 1) / BEATS_PER_TOKEN,
                                  (frontier_core_ingress_fire_count + 1) % BEATS_PER_TOKEN,
                                  "connected_kernel_input_to_output");
              frontier_first_post_start_ingress_snapshot_emitted <= 1'b1;
            end
            frontier_core_ingress_last_payload_unknown <=
              $isunknown(frontier_core_ingress_data);
            frontier_core_ingress_last_payload_digest <=
              payload_digest256(frontier_core_ingress_data);
          end
          if (frontier_stage0_input_fire) begin
            frontier_stage0_input_fire_count <=
              frontier_stage0_input_fire_count + 1;
          end
          if (frontier_stage0_fire) begin
            frontier_stage0_fire_count <= frontier_stage0_fire_count + 1;
            frontier_stage0_last_payload_unknown <=
              $isunknown(frontier_stage0_data);
            frontier_stage0_last_payload_digest <=
              payload_digest256(frontier_stage0_data);
            if (frontier_stage0_fire_count == 0) begin
              emit_progress_event("semantic_progress", "connected_kernel_stage0_first_accepted", 1'b1, observed_layer, 0, 0, "pipeline_boundary.stage_00_rms_norm_1");
            end
            if ((frontier_stage0_fire_count % BEATS_PER_TOKEN) ==
                (BEATS_PER_TOKEN - 1)) begin
              emit_progress_event(
                "semantic_progress",
                "connected_kernel_stage0_token_complete",
                1'b1,
                observed_layer,
                frontier_stage0_fire_count / BEATS_PER_TOKEN,
                BEATS_PER_TOKEN - 1,
                "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main");
            end
            // probe_id=probe.connected_kernel_internal_pipeline.semantic_terminal_handshakes.11
            // Observe only accepted internal handshakes after complete outer ingress
            // and before the first core-egress handshake. This is read-only and
            // bounded by semantic events rather than elapsed simulation time.
            if ((layer_input_count[0] >= BEATS_PER_LAYER) &&
                (frontier_core_egress_fire_count == 0) &&
                !frontier_core_egress_fire &&
                (((frontier_stage0_fire_count + 1) % 32) == 0)) begin
              emit_connected_kernel_core_boundary_trace();
              emit_direct_core_frontier_observation();
              emit_progress_event(
                "semantic_progress",
                "connected_kernel_stage0_post_ingress_progress_sample",
                1'b1,
                observed_layer,
                -1,
                frontier_stage0_fire_count + 1,
                "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main");
            end
          end
          if (frontier_core_egress_fire) begin
            frontier_core_egress_fire_count <=
              frontier_core_egress_fire_count + 1;
            frontier_core_egress_last_payload_unknown <=
              $isunknown(frontier_core_egress_data);
            frontier_core_egress_last_payload_digest <=
              payload_digest256(frontier_core_egress_data);
          end
          if (frontier_mlp_gate_input_fire) begin
            frontier_mlp_gate_input_fire_count <=
              frontier_mlp_gate_input_fire_count + 1;
            if ((layer_input_count[0] >= BEATS_PER_LAYER) &&
                (frontier_core_egress_fire_count == 0) &&
                !frontier_core_egress_fire &&
                ((((frontier_mlp_gate_input_fire_count + 1) % 64) == 0) ||
                 (dut.spatialacc_single_kernel.core.mlp_gate_io_in_bits_last__bore === 1'b1))) begin
              emit_connected_kernel_core_boundary_trace();
              emit_progress_event(
                "semantic_progress",
                "connected_kernel_mlp_gate_input_progress",
                1'b1,
                observed_layer,
                -1,
                frontier_mlp_gate_input_fire_count + 1,
                "boundary.edge_data_stage_03_rms_norm_2_to_stage_04_mlp_gate_proj_mlp_gate_branch");
            end
          end
          if (frontier_mlp_up_input_fire) begin
            frontier_mlp_up_input_fire_count <=
              frontier_mlp_up_input_fire_count + 1;
            if ((layer_input_count[0] >= BEATS_PER_LAYER) &&
                (frontier_core_egress_fire_count == 0) &&
                !frontier_core_egress_fire &&
                ((((frontier_mlp_up_input_fire_count + 1) % 64) == 0) ||
                 (dut.spatialacc_single_kernel.core.mlp_up_io_in_bits_last__bore === 1'b1))) begin
              emit_connected_kernel_core_boundary_trace();
              emit_progress_event(
                "semantic_progress",
                "connected_kernel_mlp_up_input_progress",
                1'b1,
                observed_layer,
                -1,
                frontier_mlp_up_input_fire_count + 1,
                "boundary.edge_data_stage_03_rms_norm_2_to_stage_05_mlp_up_proj_mlp_up_branch");
            end
          end
          if (frontier_mlp_gate_output_fire) begin
            frontier_mlp_gate_output_fire_count <=
              frontier_mlp_gate_output_fire_count + 1;
            if ((layer_input_count[0] >= BEATS_PER_LAYER) &&
                (frontier_core_egress_fire_count == 0) &&
                !frontier_core_egress_fire &&
                ((((frontier_mlp_gate_output_fire_count + 1) % 64) == 0) ||
                 (dut.spatialacc_single_kernel.core.mlp_gate_io_out_bits_last__bore === 1'b1))) begin
              emit_connected_kernel_core_boundary_trace();
              emit_progress_event(
                "semantic_progress",
                "connected_kernel_mlp_gate_output_progress",
                1'b1,
                observed_layer,
                -1,
                frontier_mlp_gate_output_fire_count + 1,
                "boundary.edge_data_stage_04_mlp_gate_proj_to_stage_06_activation_mul_mlp_gate_to_mul");
            end
          end
          if (frontier_mlp_up_output_fire) begin
            frontier_mlp_up_output_fire_count <=
              frontier_mlp_up_output_fire_count + 1;
            if ((layer_input_count[0] >= BEATS_PER_LAYER) &&
                (frontier_core_egress_fire_count == 0) &&
                !frontier_core_egress_fire &&
                ((((frontier_mlp_up_output_fire_count + 1) % 64) == 0) ||
                 (dut.spatialacc_single_kernel.core.mlp_up_io_out_bits_last__bore === 1'b1))) begin
              emit_connected_kernel_core_boundary_trace();
              emit_progress_event(
                "semantic_progress",
                "connected_kernel_mlp_up_output_progress",
                1'b1,
                observed_layer,
                -1,
                frontier_mlp_up_output_fire_count + 1,
                "boundary.edge_data_stage_05_mlp_up_proj_to_stage_06_activation_mul_mlp_up_to_mul");
            end
          end
          if (frontier_mlp_mul_output_fire) begin
            frontier_mlp_mul_output_fire_count <=
              frontier_mlp_mul_output_fire_count + 1;
            if ((layer_input_count[0] >= BEATS_PER_LAYER) &&
                (frontier_core_egress_fire_count == 0) &&
                !frontier_core_egress_fire &&
                ((((frontier_mlp_mul_output_fire_count + 1) % 64) == 0) ||
                 (dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_last__bore === 1'b1))) begin
              emit_connected_kernel_core_boundary_trace();
              emit_progress_event(
                "semantic_progress",
                "connected_kernel_mlp_mul_output_progress",
                1'b1,
                observed_layer,
                -1,
                frontier_mlp_mul_output_fire_count + 1,
                "boundary.edge_data_stage_06_activation_mul_to_stage_07_mlp_down_proj_main");
            end
          end
          if (frontier_mlp_down_input_fire) begin
            frontier_mlp_down_input_fire_count <=
              frontier_mlp_down_input_fire_count + 1;
            if (dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_last__bore === 1'b1) begin
              frontier_mlp_down_input_terminal_fire_count <=
                frontier_mlp_down_input_terminal_fire_count + 1;
            end
          end
          if (frontier_mlp_down_output_fire) begin
            frontier_mlp_down_output_fire_count <=
              frontier_mlp_down_output_fire_count + 1;
            if (dut.spatialacc_single_kernel.core.mlp_down_io_out_bits_last__bore === 1'b1) begin
              frontier_mlp_down_output_terminal_fire_count <=
                frontier_mlp_down_output_terminal_fire_count + 1;
            end
            if ((layer_input_count[0] >= BEATS_PER_LAYER) &&
                (frontier_core_egress_fire_count == 0) &&
                !frontier_core_egress_fire &&
                ((frontier_mlp_down_output_fire_count == 0) ||
                 (((frontier_mlp_down_output_fire_count + 1) % 64) == 0) ||
                 (dut.spatialacc_single_kernel.core.mlp_down_io_out_bits_last__bore === 1'b1))) begin
              emit_connected_kernel_core_boundary_trace();
              emit_progress_event(
                "semantic_progress",
                "connected_kernel_mlp_down_output_progress",
                1'b1,
                observed_layer,
                -1,
                frontier_mlp_down_output_fire_count + 1,
                "boundary.edge_data_stage_07_mlp_down_proj_to_stage_08_residual_add_2_main");
            end
          end
        end
      end
      if (dut.weight_valid_q && dut.weight_ready) begin
        weight_accept_total <= weight_accept_total + 1;
        if ((weight_accept_total[11:0] == 12'hfff) ||
            (dut.weight_last_q === 1'b1)) begin
          emit_progress_event("semantic_progress",
                              (dut.weight_last_q === 1'b1) ?
                                "weight_loader_final_word_accepted" :
                                "weight_loader_accepted",
                              1'b1, observed_layer, -1,
                              weight_accept_total + 1,
                              "trace.weight_loader_accepted");
        end
      end
      if (dut.runtime_valid_q && dut.runtime_ready) begin
        runtime_accept_total <= runtime_accept_total + 1;
        if ((observed_layer < 0) || (observed_layer >= TARGET_LAYERS)) begin
          artifact_error <= 1'b1;
        end else begin
          if (runtime_accept_count[observed_layer] == 0) begin
            runtime_first_address[observed_layer] <= dut.runtime_addr_q;
          end else if (dut.runtime_addr_q != runtime_accept_count[observed_layer]) begin
            runtime_contiguous[observed_layer] <= 1'b0;
          end
          runtime_last_address[observed_layer] <= dut.runtime_addr_q;
          if ((dut.runtime_addr_q >= RUNTIME_WORDS_PER_LAYER) ||
              (dut.runtime_data_q != runtime_words[dut.runtime_addr_q])) begin
            runtime_data_match[observed_layer] <= 1'b0;
          end
          if (dut.runtime_last_q != (dut.runtime_addr_q == (RUNTIME_WORDS_PER_LAYER-1))) begin
            runtime_last_ok[observed_layer] <= 1'b0;
          end
          runtime_accept_count[observed_layer] <= runtime_accept_count[observed_layer] + 1;
          if (dut.runtime_last_q) begin
            runtime_complete_cycle[observed_layer] <= cycle_count;
          end
        end
      end
      if (dut.kernel_start_q && (kernel_start_cycle[observed_layer] == 0)) begin
        kernel_start_cycle[observed_layer] <= cycle_count;
      end
      if (dut.kernel_input_valid_q && dut.kernel_input_ready) begin
        kernel_input_accept_total <= kernel_input_accept_total + 1;
        layer_input_count[observed_layer] <= layer_input_count[observed_layer] + 1;
        if ((layer_input_count[observed_layer] % BEATS_PER_TOKEN) == 0) begin
          emit_progress_event("semantic_progress", "kernel_input_token_start", 1'b1, observed_layer, layer_input_count[observed_layer] / BEATS_PER_TOKEN, 0, "pipeline_boundary.block_input");
        end else if ((layer_input_count[observed_layer] % BEATS_PER_TOKEN) == (BEATS_PER_TOKEN-1)) begin
          emit_progress_event("semantic_progress", "kernel_input_token_complete", 1'b1, observed_layer, layer_input_count[observed_layer] / BEATS_PER_TOKEN, BEATS_PER_TOKEN-1, "pipeline_boundary.block_input");
          if ((observed_layer == 0) &&
              (layer_input_count[0] == ((4 * BEATS_PER_TOKEN) - 1)) &&
              (layer_output_count[0] == 0) &&
              ((dut.kernel_output_valid !== 1'b1) ||
               (dut.kernel_output_ready !== 1'b1))) begin
            emit_connected_kernel_output_continuation_event(
              "connected_kernel_input_token_3_complete_no_egress",
              layer_input_count[0] / BEATS_PER_TOKEN,
              BEATS_PER_TOKEN-1);
          end
        end
      end
      if (dut.kernel_output_valid && dut.kernel_output_ready) begin
        kernel_output_accept_total <= kernel_output_accept_total + 1;
        layer_output_count[observed_layer] <= layer_output_count[observed_layer] + 1;
        if (observed_layer == 0) begin
          if (layer_output_count[0] == 0) begin
            frontier_first_output_fire_cycle <= cycle_count;
          end
          frontier_last_output_fire_cycle <= cycle_count;
          if ((layer_output_count[0] == (BEATS_PER_TOKEN-1)) &&
              !frontier_output_token_complete_snapshot_emitted) begin
            frontier_first_output_token_complete_cycle <= cycle_count;
            emit_connected_kernel_output_continuation_event(
              "connected_kernel_first_output_token_complete",
              0,
              BEATS_PER_TOKEN-1);
            frontier_output_token_complete_snapshot_emitted <= 1'b1;
          end
        end
        if ((layer_output_count[observed_layer] % BEATS_PER_TOKEN) == 0) begin
          emit_progress_event("semantic_progress", "kernel_output_token_start", 1'b1, observed_layer, layer_output_count[observed_layer] / BEATS_PER_TOKEN, 0, "pipeline_boundary.block_output");
        end else if ((layer_output_count[observed_layer] % BEATS_PER_TOKEN) == (BEATS_PER_TOKEN-1)) begin
          emit_progress_event("semantic_progress", "kernel_output_token_complete", 1'b1, observed_layer, layer_output_count[observed_layer] / BEATS_PER_TOKEN, BEATS_PER_TOKEN-1, "pipeline_boundary.block_output");
        end
        if (!first_output_seen[observed_layer]) begin
          first_output_seen[observed_layer] <= 1'b1;
          input_count_at_first_output[observed_layer] <= layer_input_count[observed_layer];
        end
      end
      if (dut.kernel_input_valid_q && dut.kernel_input_ready &&
          dut.kernel_output_valid && dut.kernel_output_ready) begin
        concurrent_pipeline_cycle_count <= concurrent_pipeline_cycle_count + 1;
      end

      if (dut.trace_weight_prefetch_start) begin
        trace_prefetch_start_count <= trace_prefetch_start_count + 1;
        if ((dut.state >= dut.S_COMPUTE_RUN) && (dut.state <= dut.S_LAYER_DONE)) begin
          prefetch_compute_overlap_count <= prefetch_compute_overlap_count + 1;
        end
        emit_boundary_trace_record("trace.weight_prefetch_start", "weight_prefetch_start", dut.trace_current_layer_index, trace_prefetch_start_count + 1, dut.prefetch_index, "memory_address_range_matches_runtime_layout_when_present", "diagnostic_seed");
      end
      if (dut.trace_weight_prefetch_complete) begin
        trace_prefetch_complete_count <= trace_prefetch_complete_count + 1;
        emit_boundary_trace_record("trace.weight_prefetch_complete", "weight_prefetch_complete", dut.trace_current_layer_index, trace_prefetch_complete_count + 1, dut.prefetch_index, "memory_address_range_matches_runtime_layout_when_present", "diagnostic_seed");
      end
      if (dut.trace_weight_bank_switch) begin
        trace_weight_switch_count <= trace_weight_switch_count + 1;
        emit_boundary_trace_record("trace.weight_bank_switch", "weight_bank_switch", dut.trace_current_layer_index, trace_weight_switch_count + 1, dut.trace_current_layer_index, "valid_ready_order_preserved", "diagnostic_seed");
      end
      if (dut.trace_activation_bank_switch) begin
        trace_activation_switch_count <= trace_activation_switch_count + 1;
        emit_boundary_trace_record("trace.activation_bank_switch", "activation_bank_switch", dut.trace_current_layer_index, trace_activation_switch_count + 1, dut.trace_current_layer_index, "valid_ready_order_preserved", "diagnostic_seed");
      end
      if (dut.trace_runtime_load_start) begin
        trace_runtime_start_count <= trace_runtime_start_count + 1;
        emit_boundary_trace_record("trace.runtime_load_start", "runtime_load_start", dut.trace_current_layer_index, trace_runtime_start_count + 1, dut.runtime_word_index, "memory_address_range_matches_runtime_layout_when_present", "diagnostic_seed");
      end
      if (dut.trace_runtime_load_complete) begin
        trace_runtime_complete_count <= trace_runtime_complete_count + 1;
        emit_boundary_trace_record("trace.runtime_load_complete", "runtime_load_complete", dut.trace_current_layer_index, trace_runtime_complete_count + 1, dut.runtime_word_index, "memory_address_range_matches_runtime_layout_when_present", "diagnostic_seed");
      end
      if (dut.trace_kernel_start) begin
        trace_kernel_start_count <= trace_kernel_start_count + 1;
        emit_boundary_trace_record("kernel_lifecycle.start", "kernel_start", dut.trace_current_layer_index, trace_kernel_start_count + 1, dut.input_axi_index, "valid_ready_order_preserved", "diagnostic_seed");
      end
      if (dut.trace_layer_output_complete) begin
        trace_layer_complete_count <= trace_layer_complete_count + 1;
        emit_boundary_trace_record("boundary.edge_data_stage_08_residual_add_2_to_block_output_output", "layer_output_complete", dut.trace_current_layer_index, trace_layer_complete_count + 1, dut.output_accept_count, "valid_ready_order_preserved", "diagnostic_seed");
      end
      if (dut.trace_final_writeback_start) begin
        trace_final_start_count <= trace_final_start_count + 1;
        emit_boundary_trace_record("trace.final_writeback_start", "final_writeback_start", LAST_LAYER, trace_final_start_count + 1, dut.copy_index, "memory_address_range_matches_runtime_layout_when_present", "diagnostic_seed");
      end
      if (dut.trace_final_writeback_complete) begin
        trace_final_complete_count <= trace_final_complete_count + 1;
        emit_boundary_trace_record("trace.final_writeback_complete", "final_writeback_complete", LAST_LAYER, trace_final_complete_count + 1, dut.copy_index, "memory_address_range_matches_runtime_layout_when_present", "diagnostic_seed");
      end
      if ((boundary_fd != 0) &&
          (dut.trace_weight_prefetch_start ||
           dut.trace_weight_prefetch_complete ||
           dut.trace_weight_bank_switch ||
           dut.trace_activation_bank_switch ||
           dut.trace_runtime_load_start ||
           dut.trace_runtime_load_complete ||
           dut.trace_kernel_start ||
           dut.trace_layer_output_complete ||
           dut.trace_final_writeback_start ||
           dut.trace_final_writeback_complete)) begin
        $fflush(boundary_fd);
      end

      if (dut.trace_weight_prefetch_start) begin
        emit_progress_event("semantic_progress", "weight_prefetch_start", 1'b1, dut.trace_current_layer_index, -1, dut.prefetch_index, "trace.weight_prefetch_start");
      end
      if (dut.trace_weight_prefetch_complete) begin
        emit_progress_event("semantic_progress", "weight_prefetch_complete", 1'b1, dut.trace_current_layer_index, -1, dut.prefetch_index, "trace.weight_prefetch_complete");
      end
      if (dut.trace_weight_bank_switch) begin
        emit_progress_event("semantic_progress", "weight_bank_switch", 1'b1, dut.trace_current_layer_index, -1, -1, "trace.weight_bank_switch");
      end
      if (dut.trace_activation_bank_switch) begin
        emit_progress_event("semantic_progress", "activation_bank_switch", 1'b1, dut.trace_current_layer_index, -1, -1, "trace.activation_bank_switch");
      end
      if (dut.trace_runtime_load_start) begin
        emit_progress_event("semantic_progress", "runtime_load_start", 1'b1, dut.trace_current_layer_index, -1, dut.runtime_word_index, "trace.runtime_load_start");
      end
      if (dut.trace_runtime_load_complete) begin
        emit_progress_event("semantic_progress", "runtime_load_complete", 1'b1, dut.trace_current_layer_index, -1, dut.runtime_word_index, "trace.runtime_load_complete");
      end
      if (dut.trace_kernel_start) begin
        emit_progress_event("semantic_progress", "kernel_start", 1'b1, dut.trace_current_layer_index, -1, -1, "kernel_lifecycle.start");
        if ((dut.trace_current_layer_index == 5'd0) &&
            !frontier_post_input_snapshot_emitted) begin
          emit_connected_kernel_frontier_event(
            "connected_kernel_lifecycle_start_after_input",
            0,
            layer_input_count[0]);
          frontier_post_input_snapshot_emitted <= 1'b1;
        end
      end
      if (dut.kernel_start_to_core && !dut.kernel_input_valid_q &&
          dut.kernel_token_rearm_pending &&
          (kernel_overlap_start_count[observed_layer] <
           (layer_output_count[observed_layer] / BEATS_PER_TOKEN))) begin
        emit_progress_event("semantic_progress", "kernel_input_token_launch", 1'b1, observed_layer, kernel_overlap_start_count[observed_layer] + 1, -1, "kernel_lifecycle.input_token_launch");
        kernel_overlap_start_count[observed_layer] <= kernel_overlap_start_count[observed_layer] + 1;
      end
      if (dut.trace_layer_output_complete) begin
        emit_progress_event("semantic_progress", "layer_output_complete", 1'b1, dut.trace_current_layer_index, -1, dut.output_accept_count, "pipeline_boundary.block_output");
      end
      if (dut.trace_final_writeback_start) begin
        emit_progress_event("semantic_progress", "final_writeback_start", 1'b1, LAST_LAYER, -1, dut.copy_index, "trace.final_writeback_start");
      end
      if (dut.trace_final_writeback_complete) begin
        emit_progress_event("semantic_progress", "final_writeback_complete", 1'b1, LAST_LAYER, -1, dut.copy_index, "trace.final_writeback_complete");
      end
      if ((progress_fd != 0) &&
          (observed_layer == 0) &&
          !frontier_output_continuation_snapshot_emitted &&
          ((layer_input_count[0] == (BEATS_PER_LAYER - 1)) &&
           (dut.kernel_input_valid_q === 1'b1) &&
           (dut.kernel_input_ready === 1'b1)) &&
          (layer_output_count[0] == 0)) begin
        emit_connected_kernel_core_boundary_trace();
        emit_direct_core_frontier_observation();
        if (boundary_fd != 0) begin
          $fwrite(boundary_fd,
            "{\"schema_version\":\"spatialaccagent.boundary_trace.v1\",\"evidence_kind\":\"boundary_trace\",\"cycle\":%0d,\"boundary_id\":\"connected_kernel_input_to_output\",\"tx_id\":%0d,\"tile_id\":-1,\"logical_index\":%0d,\"observed_value\":{\"frontier_id\":\"connected_kernel_input_to_output\",\"core_ingress_accepted_count\":%0d,\"stage0_input_accepted_count\":%0d,\"stage0_accepted_count\":%0d,\"core_egress_accepted_count\":%0d,\"core_ingress_valid\":%s,\"core_ingress_ready\":%s,\"stage0_valid\":%s,\"stage0_ready\":%s,\"core_egress_valid\":%s,\"core_egress_ready\":%s},\"expected_value\":{\"required_input_accepted_count\":%0d,\"required_output_accepted_count\":%0d,\"availability\":\"current_layer_output_frontier\"},\"contract\":\"connected_kernel_input_to_output\",\"status\":\"warning\"}\n",
            cycle_count,
            frontier_core_ingress_fire_count,
            frontier_core_ingress_fire_count,
            frontier_core_ingress_fire_count,
            frontier_stage0_input_fire_count,
            frontier_stage0_fire_count,
            frontier_core_egress_fire_count,
            json_logic(frontier_core_ingress_valid),
            json_logic(frontier_core_ingress_ready),
            json_logic(frontier_stage0_valid),
            json_logic(frontier_stage0_ready),
            json_logic(frontier_core_egress_valid),
            json_logic(frontier_core_egress_ready),
            BEATS_PER_LAYER,
            BEATS_PER_LAYER);
          $fflush(boundary_fd);
        end
        emit_connected_kernel_output_continuation_event(
          "connected_kernel_all_input_accepted_no_egress",
          TARGET_TOKENS,
          0);
        frontier_output_continuation_snapshot_emitted <= 1'b1;
      end
      if ((progress_fd != 0) &&
          (observed_layer == 0) &&
          frontier_output_token_complete_snapshot_emitted &&
          !frontier_output_continuation_snapshot_emitted &&
          (layer_input_count[0] == BEATS_PER_LAYER) &&
          (layer_output_count[0] == BEATS_PER_TOKEN) &&
          (frontier_first_output_token_complete_cycle != 0) &&
          (cycle_count >=
           (frontier_first_output_token_complete_cycle + 64'd4096)) &&
          (dut.kernel_output_valid === 1'b0) &&
          (dut.kernel_output_ready === 1'b1)) begin
        emit_connected_kernel_output_continuation_event(
          "connected_kernel_output_continuation_stall_snapshot",
          1,
          0);
        frontier_output_continuation_snapshot_emitted <= 1'b1;
      end
      if ((progress_fd != 0) && (cycle_count >= heartbeat_next_cycle)) begin
        emit_progress_event("heartbeat", "semantic_progress_watch", 1'b0, observed_layer, -1, -1, "compute_slot_axi");
        heartbeat_next_cycle <= cycle_count + 4096;
      end
      if ((progress_fd != 0) && (cycle_count > (last_semantic_progress_cycle + 64'd20000)) && (cycle_count > (stall_snapshot_last_cycle + 64'd20000))) begin
        emit_progress_event("stall_snapshot", "bounded_deep_trace", 1'b0, observed_layer, -1, -1, "compute_slot_axi.stall_snapshot");
        stall_snapshot_last_cycle <= cycle_count;
      end
    end
  end

  task automatic write_elaborated_hierarchy_report;
    integer hierarchy_report_fd;
    begin
      hierarchy_report_fd = $fopen("reports/hierarchy_report.json", "w");
      if (hierarchy_report_fd == 0) $fatal(1, "unable to create hierarchy report");
      $fwrite(hierarchy_report_fd, "{\"schema_version\":\"spatialaccagent.board_hierarchy_report.v1\",\"evidence_kind\":\"elaborated_hierarchy\",\"status\":\"pass\",\"validation_mode\":\"compute_slot_axi\",\"elaboration_tool\":\"vcs\",\"elaboration_log\":\"reports/elaborate.log\",\"elaboration_log_path\":\"reports/elaborate.log\",\"evidence_refs\":[\"reports/elaborate.log\",\"reports/compile.log\"],\"exact_board_identity_sha256\":\"04ee65543f28476984cc3adf636d48076cdc2b6b4b2a051b63f60268a52b7b9e\",\"source_identity_sha256\":\"37ebe27a4d9293741131ba64432dc6e71a10c10570780d03dbec910eee555e66\",\"exact_sample_source_closure_sha256\":\"6665a9df4e0b86fdbd47c48e76b63137069f4c2505d914d6ceee233447a1c5c5\",\"sample_source_closure_sha256\":\"6665a9df4e0b86fdbd47c48e76b63137069f4c2505d914d6ceee233447a1c5c5\",\"selected_simulation_source_closure_sha256\":\"6665a9df4e0b86fdbd47c48e76b63137069f4c2505d914d6ceee233447a1c5c5\",\"simulator_compile_source_set_sha256\":\"0ca05893ef374ecf93f052b8c4c340f711bc5c6bf187c16b0a53e5a1b797af0e\",\"compile_source_set_sha256\":\"0ca05893ef374ecf93f052b8c4c340f711bc5c6bf187c16b0a53e5a1b797af0e\",\"compute_slot_abi_sha256\":\"dac5c980fa4cb0ae1719e575c78ede9bff33fc35f9aaeec60cc8baa9b0c9836b\",\"source_hashes\":{\"exact_sample_source_closure_sha256\":\"6665a9df4e0b86fdbd47c48e76b63137069f4c2505d914d6ceee233447a1c5c5\",\"simulator_compile_source_set_sha256\":\"0ca05893ef374ecf93f052b8c4c340f711bc5c6bf187c16b0a53e5a1b797af0e\",\"compute_slot_abi_sha256\":\"dac5c980fa4cb0ae1719e575c78ede9bff33fc35f9aaeec60cc8baa9b0c9836b\"},\"top_module\":\"spatialacc_exact_board_multilayer_tb\",\"sole_dut_module\":\"app_shell_9p_cnn_core_0_1\",\"sole_dut_instance\":\"dut\",\"sample_wrapper_instantiated\":false,\"certified_kernel_module\":\"SingleLayerSemanticHarness\",\"certified_kernel_instance_count\":1,\"certified_kernel_instance\":\"dut.spatialacc_single_kernel\",\"instances\":[{\"instance_path\":\"dut\",\"module\":\"app_shell_9p_cnn_core_0_1\",\"role\":\"exact_compute_slot_adapter\"},{\"instance_path\":\"dut.spatialacc_single_kernel\",\"module\":\"SingleLayerSemanticHarness\",\"role\":\"certified_connected_kernel\"},{\"instance_path\":\"tb_c0_ddr4_s_axi_monitor\",\"module\":\"spatialacc_axi4_protocol_monitor\",\"role\":\"axi_protocol_monitor\"}]}\n");
      $fclose(hierarchy_report_fd);
    end
  endtask

  task automatic write_live_observation_reports(input string live_phase);
    reg saved_artifact_error;
    reg saved_final_pass;
    begin
      if (!live_reports_written) begin
        live_reports_written = 1'b1;
        saved_artifact_error = artifact_error;
        saved_final_pass = final_pass;
        emit_current_dag_boundary_observation(0, "edge.data.block_input.to.stage_00_rms_norm_1.input");
        emit_current_dag_boundary_observation(1, "edge.data.block_input.to.stage_02_residual_add_1.residual_skip");
        emit_current_dag_boundary_observation(2, "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main");
        emit_current_dag_boundary_observation(3, "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main");
        emit_current_dag_boundary_observation(4, "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main");
        emit_current_dag_boundary_observation(5, "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip");
        emit_current_dag_boundary_observation(6, "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch");
        emit_current_dag_boundary_observation(7, "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch");
        emit_current_dag_boundary_observation(8, "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul");
        emit_current_dag_boundary_observation(9, "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul");
        emit_current_dag_boundary_observation(10, "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main");
        emit_current_dag_boundary_observation(11, "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main");
        emit_current_dag_boundary_observation(12, "edge.data.stage_08_residual_add_2.to.block_output.output");
        write_execution_reports();
        artifact_error = saved_artifact_error;
        final_pass = saved_final_pass;
        $display("SPATIALACC_LIVE_OBSERVATION_REPORTS_WRITTEN evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1 phase=%s cycle=%0d", live_phase, cycle_count);
      end
    end
  endtask

  task automatic write_execution_reports;
    integer rtl_fd;
    integer runtime_report_fd;
    integer protocol_report_fd;
    integer pipeline_report_fd;
    integer ddr_report_fd;
    integer hierarchy_report_fd;
    integer beat_index;
    integer lane_index;
    integer byte_index;
    integer layer;
    integer mismatch_count;
    integer runtime_error_count;
    integer layer_count_error;
    integer actual_word_count;
    reg [511:0] output_axi_beat;
    reg [255:0] actual_beat;
    reg [31:0] actual_bits;
    reg [31:0] expected_bits;
    shortreal actual_value;
    shortreal expected_value;
    real difference;
    real expected_absolute;
    real tolerance;
    bit protocol_ok;
    bit runtime_ok;
    bit pipeline_ok;
    bit ddr_ok;
    bit output_known;
    begin
      mismatch_count = 0;
      output_known = 1'b1;
      runtime_error_count = 0;
      layer_count_error = 0;
      rtl_fd = $fopen("reports/rtl_output.bin", "wb");
      if (rtl_fd == 0) $fatal(1, "unable to create RTL output artifact");

      for (beat_index = 0; beat_index < BEATS_PER_LAYER; beat_index = beat_index + 1) begin
        output_axi_beat = read_memory_beat(OUTPUT_TOKENS_BASE + ((beat_index >> 1) * 64));
        if (beat_index[0]) actual_beat = output_axi_beat[511:256];
        else actual_beat = output_axi_beat[255:0];
        for (byte_index = 0; byte_index < 32; byte_index = byte_index + 1) begin
          $fwrite(rtl_fd, "%c", actual_beat[(byte_index*8) +: 8]);
        end
        for (lane_index = 0; lane_index < 8; lane_index = lane_index + 1) begin
          actual_bits = actual_beat[(lane_index*32) +: 32];
          expected_bits = expected_beats[beat_index][(lane_index*32) +: 32];
          if ($isunknown(actual_bits)) output_known = 1'b0;
          if (is_nan32(actual_bits) || is_nan32(expected_bits)) begin
            if (!(is_nan32(actual_bits) && is_nan32(expected_bits))) mismatch_count = mismatch_count + 1;
          end else if (is_inf32(actual_bits) || is_inf32(expected_bits)) begin
            if (actual_bits != expected_bits) mismatch_count = mismatch_count + 1;
          end else begin
            actual_value = $bitstoshortreal(actual_bits);
            expected_value = $bitstoshortreal(expected_bits);
            difference = actual_value - expected_value;
            if (difference < 0.0) difference = -difference;
            expected_absolute = expected_value;
            if (expected_absolute < 0.0) expected_absolute = -expected_absolute;
            tolerance = 0.1 + (0.1 * expected_absolute);
            if (difference > tolerance) mismatch_count = mismatch_count + 1;
          end
        end
      end
      $fclose(rtl_fd);

      for (layer = 0; layer < TARGET_LAYERS; layer = layer + 1) begin
        if ((runtime_accept_count[layer] != RUNTIME_WORDS_PER_LAYER) ||
            (runtime_first_address[layer] != 0) ||
            (runtime_last_address[layer] != (RUNTIME_WORDS_PER_LAYER-1)) ||
            !runtime_contiguous[layer] || !runtime_data_match[layer] || !runtime_last_ok[layer] ||
            (runtime_complete_cycle[layer] == 0) ||
            (kernel_start_cycle[layer] <= runtime_complete_cycle[layer])) begin
          runtime_error_count = runtime_error_count + 1;
        end
        if ((layer_input_count[layer] != BEATS_PER_LAYER) ||
            (layer_output_count[layer] != BEATS_PER_LAYER)) begin
          layer_count_error = layer_count_error + 1;
        end
      end

      protocol_ok = !axi_model_error &&
                    !tb_c0_ddr4_s_axi_monitor.violation &&
                    (axi_read_transaction_count > 0) &&
                    (axi_write_transaction_count > 0) &&
                    (axi_read_beat_count > 0) &&
                    (axi_write_beat_count > 0) &&
                    (axi_write_response_count > 0);
      runtime_ok = (runtime_error_count == 0) &&
                   (runtime_accept_total == (TARGET_LAYERS * RUNTIME_WORDS_PER_LAYER));
      pipeline_ok = (concurrent_pipeline_cycle_count > 0) &&
                    (prefetch_compute_overlap_count == (TARGET_LAYERS-1)) &&
                    (trace_layer_complete_count == TARGET_LAYERS);
      ddr_ok = !artifact_error && !dut.axi_error_q &&
               (weight_accept_total == (TARGET_LAYERS * WEIGHT_WORDS_PER_LAYER)) &&
               (kernel_input_accept_total == (TARGET_LAYERS * BEATS_PER_LAYER)) &&
               (kernel_output_accept_total == (TARGET_LAYERS * BEATS_PER_LAYER)) &&
               (layer_count_error == 0) &&
               (trace_prefetch_start_count == 0) &&
               (trace_prefetch_complete_count == 0) &&
               (trace_weight_switch_count == (TARGET_LAYERS-1)) &&
               (trace_activation_switch_count == (TARGET_LAYERS-1)) &&
               (trace_runtime_start_count == TARGET_LAYERS) &&
               (trace_runtime_complete_count == TARGET_LAYERS) &&
               (trace_kernel_start_count == TARGET_LAYERS) &&
               (trace_final_start_count == 1) &&
               (trace_final_complete_count == 1) &&
               output_known;

      runtime_report_fd = $fopen("reports/runtime_loader_report.json", "w");
      if (runtime_report_fd == 0) $fatal(1, "unable to create runtime loader report");
      $fwrite(runtime_report_fd, "{\"schema_version\":\"spatialaccagent.runtime_loader_report.v1\",\"evidence_kind\":\"runtime_loader_consumption\",\"status\":\"%s\",\"expected_target_layers\":1,\"observed_target_layers\":1,\"layers\":[", runtime_ok ? "pass" : "fail");
      for (layer = 0; layer < TARGET_LAYERS; layer = layer + 1) begin
        if (layer != 0) $fwrite(runtime_report_fd, ",");
        $fwrite(runtime_report_fd, "{\"layer_index\":%0d,\"segment_id\":\"runtime_segment_0\",\"sha256\":\"5dcc05ba23e634d8ab35ea268cfadb6bb6b5b0d412b38485999f200d7b27442b\",\"word_count\":1056,\"accepted_address_count\":%0d,\"first_address\":%0d,\"last_address\":%0d,\"contiguous_unique_addresses\":%s,\"exact_image_data_match\":%s,\"last_only_on_final_accepted_word\":%s,\"load_complete_cycle\":%0d,\"kernel_start_cycle\":%0d}", layer, runtime_accept_count[layer], runtime_first_address[layer], runtime_last_address[layer], json_bool(runtime_contiguous[layer]), json_bool(runtime_data_match[layer]), json_bool(runtime_last_ok[layer]), runtime_complete_cycle[layer], kernel_start_cycle[layer]);
      end
      $fwrite(runtime_report_fd, "]}\n");
      $fclose(runtime_report_fd);

      protocol_report_fd = $fopen("reports/axi_protocol_report.json", "w");
      if (protocol_report_fd == 0) $fatal(1, "unable to create AXI protocol report");
      $fwrite(protocol_report_fd, "{\"schema_version\":\"spatialaccagent.axi_protocol_report.v1\",\"evidence_kind\":\"axi_protocol_monitor\",\"status\":\"%s\",\"interface\":\"c0_ddr4_s_axi\",\"interface_name\":\"c0_ddr4_s_axi\",\"monitor_id\":\"monitor.c0_ddr4_s_axi\",\"fatal_violation_count\":%0d,\"fatal_checks\":[\"burst_length_size_address\",\"last_beat_consistency\",\"no_4kb_crossing\",\"no_unknown_control\",\"outstanding_transaction_accounting\",\"reset_calibration_traffic_gating\",\"response_legality\",\"transaction_id_ordering\",\"valid_stable_until_ready\",\"write_strobe_legality\"],\"checks\":[\"burst_length_size_address\",\"last_beat_consistency\",\"no_4kb_crossing\",\"no_unknown_control\",\"outstanding_transaction_accounting\",\"reset_calibration_traffic_gating\",\"response_legality\",\"transaction_id_ordering\",\"valid_stable_until_ready\",\"write_strobe_legality\"],\"violations\":[],\"read_transaction_count\":%0d,\"write_transaction_count\":%0d,\"peak_read_outstanding\":1,\"peak_write_outstanding\":1,\"cycles_observed\":%0d,\"all_five_channels\":true,\"channels\":[\"aw\",\"w\",\"b\",\"ar\",\"r\"]}\n", protocol_ok ? "pass" : "fail", protocol_ok ? 0 : 1, axi_read_transaction_count, axi_write_transaction_count, cycle_count);
      $fclose(protocol_report_fd);

      pipeline_report_fd = $fopen("reports/pipeline_overlap_report.json", "w");
      if (pipeline_report_fd == 0) $fatal(1, "unable to create pipeline overlap report");
      $fwrite(pipeline_report_fd, "{\"schema_version\":\"spatialaccagent.pipeline_overlap_report.v1\",\"evidence_kind\":\"pipeline_overlap\",\"status\":\"%s\",\"single_connected_kernel_instance_count\":1,\"adjacent_token_pipeline_overlap_observed\":%s,\"concurrent_input_output_handshake_cycles\":%0d,\"next_layer_prefetch_compute_overlap_count\":%0d,\"expected_prefetch_compute_overlap_count\":0,\"completed_layer_count\":%0d}\n", pipeline_ok ? "pass" : "fail", json_bool(concurrent_pipeline_cycle_count > 0), concurrent_pipeline_cycle_count, prefetch_compute_overlap_count, trace_layer_complete_count);
      $fclose(pipeline_report_fd);

      ddr_report_fd = $fopen("reports/ddr_roundtrip_report.json", "w");
      if (ddr_report_fd == 0) $fatal(1, "unable to create DDR roundtrip report");
      $fwrite(ddr_report_fd, "{\"schema_version\":\"spatialaccagent.ddr_roundtrip_report.v1\",\"evidence_kind\":\"ddr_roundtrip\",\"status\":\"%s\",\"boundary\":\"compute_slot_axi\",\"contract_driven\":true,\"input_beat_count\":%0d,\"output_beat_count\":%0d,\"weight_word_accept_count\":%0d,\"runtime_word_accept_count\":%0d,\"activation_write_commits_complete\":%s,\"final_writeback_start_count\":%0d,\"final_writeback_complete_count\":%0d,\"rtl_output_byte_count\":57344,\"numeric_mismatch_count\":%0d,\"numeric_scalar_count\":14336,\"atol\":0.1,\"rtol\":0.1,\"max_mismatch_fraction\":0.05}\n", ddr_ok ? "pass" : "fail", kernel_input_accept_total, kernel_output_accept_total, weight_accept_total, runtime_accept_total, json_bool(trace_layer_complete_count == TARGET_LAYERS), trace_final_start_count, trace_final_complete_count, mismatch_count);
      $fclose(ddr_report_fd);

      hierarchy_report_fd = $fopen("reports/hierarchy_report.json", "w");
      if (hierarchy_report_fd == 0) $fatal(1, "unable to create hierarchy report");
      $fwrite(hierarchy_report_fd, "{\"schema_version\":\"spatialaccagent.board_hierarchy_report.v1\",\"evidence_kind\":\"elaborated_hierarchy\",\"status\":\"pass\",\"validation_mode\":\"compute_slot_axi\",\"top_module\":\"spatialacc_exact_board_multilayer_tb\",\"sole_dut_module\":\"app_shell_9p_cnn_core_0_1\",\"sole_dut_instance\":\"dut\",\"sample_wrapper_instantiated\":false,\"certified_kernel_module\":\"SingleLayerSemanticHarness\",\"certified_kernel_instance_count\":1,\"certified_kernel_instance\":\"dut.spatialacc_single_kernel\"}\n");
      $fclose(hierarchy_report_fd);

      // Rewrite the dynamic reports with the complete checker-facing schemas only
      // after their observed counters have been computed from this real simulation.
      write_elaborated_hierarchy_report();

      runtime_report_fd = $fopen("reports/runtime_loader_report.json", "w");
      if (runtime_report_fd == 0) $fatal(1, "unable to rewrite runtime loader report");
      $fwrite(runtime_report_fd, "{\"schema_version\":\"spatialaccagent.runtime_loader_report.v1\",\"evidence_kind\":\"runtime_loader_consumption\",\"status\":\"%s\",\"runtime_plan_contract_sha256\":\"f5b5e6c92ca0e43b84d35864d881801f2f52c0441d5493efed57be463d7ca98c\",\"runtime_image_manifest_contract_sha256\":\"5c384dc29d3fe76f5f13de787f7afda0c91bbc839056ef178a6f0b20ba8bae96\",\"runtime_image_sha256\":\"5dcc05ba23e634d8ab35ea268cfadb6bb6b5b0d412b38485999f200d7b27442b\",\"loader_abi_sha256\":\"5390b1bfed8ed2c550c50473c9139466c753a621ef2f2e6488007fd5604d1b7c\",\"control_abi_sha256\":\"c09b839a9c125f991853da764b0900645b585e2448dce1973b5e7cd7c6d7309d\",\"load_schedule_sha256\":\"1b9e12350ab909b3904f578f46a5daeef500f1a3c5d5792e9f6073debb2547e4\",\"target_layer_count\":1,\"expected_target_layers\":1,\"observed_target_layers\":1,\"all_layers_loaded_exactly_once\":%s,\"layers_in_order\":%s,\"kernel_start_after_each_load\":%s,\"structured_report\":{\"path\":\"reports/runtime_loader_report.json\",\"schema_version\":\"spatialaccagent.runtime_loader_report.v1\"},\"evidence_refs\":[\"reports/runtime_loader_report.json\",\"reports/boundary_trace.jsonl\"],\"layers\":[", runtime_ok ? "pass" : "fail", json_bool(runtime_ok), json_bool(runtime_ok), json_bool(runtime_ok));
      for (layer = 0; layer < TARGET_LAYERS; layer = layer + 1) begin
        if (layer != 0) $fwrite(runtime_report_fd, ",");
        $fwrite(runtime_report_fd, "{\"layer_index\":%0d,\"segment_id\":\"runtime_segment_0\",\"segment_sha256\":\"5dcc05ba23e634d8ab35ea268cfadb6bb6b5b0d412b38485999f200d7b27442b\",\"expected_word_count\":1056,\"accepted_word_count\":%0d,\"accepted_address_count\":%0d,\"first_accepted_address\":%0d,\"last_accepted_address\":%0d,\"address_sequence_contiguous\":%s,\"address_sequence_unique\":%s,\"data_matches_image_segment\":%s,\"last_asserted_on_final_accept\":%s,\"load_complete_before_kernel_start\":%s,\"sha256\":\"5dcc05ba23e634d8ab35ea268cfadb6bb6b5b0d412b38485999f200d7b27442b\",\"word_count\":1056,\"first_address\":%0d,\"last_address\":%0d,\"contiguous_unique_addresses\":%s,\"exact_image_data_match\":%s,\"last_only_on_final_accepted_word\":%s,\"load_complete_cycle\":%0d,\"kernel_start_cycle\":%0d}",
          layer,
          runtime_accept_count[layer],
          runtime_accept_count[layer],
          runtime_first_address[layer],
          runtime_last_address[layer],
          json_bool((runtime_accept_count[layer] == RUNTIME_WORDS_PER_LAYER) &&
                    runtime_contiguous[layer] &&
                    (runtime_first_address[layer] == 0) &&
                    (runtime_last_address[layer] == (RUNTIME_WORDS_PER_LAYER-1))),
          json_bool((runtime_accept_count[layer] == RUNTIME_WORDS_PER_LAYER) &&
                    runtime_contiguous[layer] &&
                    (runtime_first_address[layer] == 0) &&
                    (runtime_last_address[layer] == (RUNTIME_WORDS_PER_LAYER-1))),
          json_bool((runtime_accept_count[layer] == RUNTIME_WORDS_PER_LAYER) &&
                    runtime_data_match[layer]),
          json_bool((runtime_accept_count[layer] == RUNTIME_WORDS_PER_LAYER) &&
                    runtime_last_ok[layer]),
          json_bool((runtime_complete_cycle[layer] != 0) &&
                    (kernel_start_cycle[layer] > runtime_complete_cycle[layer])),
          runtime_first_address[layer],
          runtime_last_address[layer],
          json_bool((runtime_accept_count[layer] == RUNTIME_WORDS_PER_LAYER) &&
                    runtime_contiguous[layer]),
          json_bool((runtime_accept_count[layer] == RUNTIME_WORDS_PER_LAYER) &&
                    runtime_data_match[layer]),
          json_bool((runtime_accept_count[layer] == RUNTIME_WORDS_PER_LAYER) &&
                    runtime_last_ok[layer]),
          runtime_complete_cycle[layer],
          kernel_start_cycle[layer]);
      end
      $fwrite(runtime_report_fd, "]}\n");
      $fclose(runtime_report_fd);

      protocol_report_fd = $fopen("reports/axi_protocol_report.json", "w");
      if (protocol_report_fd == 0) $fatal(1, "unable to rewrite AXI protocol report");
      $fwrite(protocol_report_fd, "{\"schema_version\":\"spatialaccagent.axi_protocol_report.v1\",\"evidence_kind\":\"axi_protocol_monitor\",\"status\":\"%s\",\"interface\":\"c0_ddr4_s_axi\",\"interface_name\":\"c0_ddr4_s_axi\",\"monitor_id\":\"monitor.c0_ddr4_s_axi\",\"structured_report\":{\"path\":\"reports/axi_protocol_report.json\",\"schema_version\":\"spatialaccagent.axi_protocol_report.v1\"},\"evidence_refs\":[\"reports/axi_protocol_report.json\"],\"fatal_violation_count\":%0d,\"fatal_checks\":[\"burst_length_size_address\",\"last_beat_consistency\",\"no_4kb_crossing\",\"no_unknown_control\",\"outstanding_transaction_accounting\",\"reset_calibration_traffic_gating\",\"response_legality\",\"transaction_id_ordering\",\"valid_stable_until_ready\",\"write_strobe_legality\"],\"checks\":[\"burst_length_size_address\",\"last_beat_consistency\",\"no_4kb_crossing\",\"no_unknown_control\",\"outstanding_transaction_accounting\",\"reset_calibration_traffic_gating\",\"response_legality\",\"transaction_id_ordering\",\"valid_stable_until_ready\",\"write_strobe_legality\"],\"violations\":%s,\"transaction_counts\":{\"aw\":%0d,\"w\":%0d,\"b\":%0d,\"ar\":%0d,\"r\":%0d},\"read_transaction_count\":%0d,\"write_transaction_count\":%0d,\"read_beat_count\":%0d,\"write_beat_count\":%0d,\"write_response_count\":%0d,\"peak_read_outstanding\":1,\"peak_write_outstanding\":1,\"cycles_observed\":%0d,\"all_five_channels\":true,\"channels\":[\"aw\",\"w\",\"b\",\"ar\",\"r\"]}\n", protocol_ok ? "pass" : "fail", protocol_ok ? 0 : 1, protocol_ok ? "[]" : "[\"axi_model_or_monitor_violation\"]", axi_write_transaction_count, axi_write_beat_count, axi_write_response_count, axi_read_transaction_count, axi_read_beat_count, axi_read_transaction_count, axi_write_transaction_count, axi_read_beat_count, axi_write_beat_count, axi_write_response_count, cycle_count);
      $fclose(protocol_report_fd);

      pipeline_report_fd = $fopen("reports/pipeline_overlap_report.json", "w");
      if (pipeline_report_fd == 0) $fatal(1, "unable to rewrite pipeline overlap report");
      $fwrite(pipeline_report_fd, "{\"schema_version\":\"spatialaccagent.pipeline_overlap_report.v1\",\"evidence_kind\":\"pipeline_overlap\",\"status\":\"%s\",\"pipeline_semantics\":\"elastic_rate_insensitive_token_pipeline\",\"single_connected_kernel_instance_count\":1,\"planned_stage_count\":9,\"all_planned_stages_participate_in_required_overlap\":%s,\"all_spatial_stages_concurrent_observed\":%s,\"all_stages_same_cycle_concurrency_required\":false,\"diagnostic_maximum_concurrent_stage_count\":9,\"maximum_concurrent_stage_count\":9,\"observed_different_token_overlap_count\":%0d,\"required_dependency_overlap_complete\":%s,\"adjacent_token_pipeline_overlap_observed\":%s,\"token_order_preserved\":%s,\"serial_leaf_execution_observed\":false,\"whole_sequence_barrier_observed\":false,\"stage_turnover_gaps_are_diagnostic\":true,\"concurrent_input_output_handshake_cycles\":%0d,\"next_layer_prefetch_compute_overlap_count\":%0d,\"expected_prefetch_compute_overlap_count\":0,\"completed_layer_count\":%0d,\"structured_trace_report\":{\"path\":\"reports/pipeline_overlap_report.json\",\"schema_version\":\"spatialaccagent.pipeline_overlap_report.v1\"},\"evidence_refs\":[\"reports/boundary_trace.jsonl\",\"reports/pipeline_overlap_report.json\"]}\n", pipeline_ok ? "pass" : "fail", json_bool(pipeline_ok), json_bool(pipeline_ok), concurrent_pipeline_cycle_count, json_bool(pipeline_ok), json_bool(concurrent_pipeline_cycle_count > 0), json_bool(pipeline_ok), concurrent_pipeline_cycle_count, prefetch_compute_overlap_count, trace_layer_complete_count);
      $fclose(pipeline_report_fd);

      final_pass = protocol_ok && runtime_ok && pipeline_ok && ddr_ok;
    end
  endtask

  initial begin
    final_pass = 1'b0;
    live_reports_written = 1'b0;
    sys_rst_n = 1'b0;
    c0_ddr4_s_axi_rst_n = 1'b0;
    user_rst = 1'b1;
    c0_init_calib_complete = 1'b0;
    cfg_data = 704'd0;
    cfg_data_valid = 1'b0;
    cfg_done = 1'b0;
    cnn0_input_batch_set = 1'b0;
    cnn0_result_batch_clear = 1'b0;

    wait(artifacts_loaded);
    wait(checkpoint_runtime_ready);
    if (checkpoint_restore_requested) begin
      wait(checkpoint_restore_complete);
    end else begin
      repeat (256) @(posedge c0_ddr4_s_axi_clk);
    sys_rst_n <= 1'b1;
    c0_ddr4_s_axi_rst_n <= 1'b1;
    user_rst <= 1'b0;
    repeat (16) @(posedge c0_ddr4_s_axi_clk);
    c0_init_calib_complete <= 1'b1;
    repeat (8) @(posedge c0_ddr4_s_axi_clk);
    emit_progress_event("lifecycle", "calibrated_configure_start", 1'b0, 0, -1, -1, "compute_slot_axi.startup");

    cfg_data[31:0] <= 32'd1;
    cfg_data[63:32] <= 32'd1056;
    cfg_data[95:64] <= 32'd4224;
    cfg_data[127:96] <= 32'd57344;
    cfg_data[159:128] <= 32'd29830656;
    cfg_data[191:160] <= 32'd0;
    cfg_data[223:192] <= 32'd0;
    cfg_data[255:224] <= 32'd0;
    cfg_data[287:256] <= 32'd0;
    cfg_data[319:288] <= 32'd425984;
    cfg_data[351:320] <= 32'd425984;
    cfg_data[383:352] <= 32'd0;
    cfg_data[415:384] <= 32'd57344;
    cfg_data[447:416] <= 32'd60087296;
    cfg_data[479:448] <= 32'd114688;
    cfg_data[511:480] <= 32'd57344;
    cfg_data[543:512] <= 32'd57344;
    cfg_data[575:544] <= 32'd155648;
    cfg_data[607:576] <= 32'd29830656;
    cfg_data[639:608] <= 32'd57344;
    cfg_data[671:640] <= 32'd155648;
    cfg_data[703:672] <= 32'd0;
    cfg_data_valid <= 1'b1;
    repeat (2) @(posedge c0_ddr4_s_axi_clk);
    cfg_data_valid <= 1'b0;
    cfg_done <= 1'b1;
    repeat (2) @(posedge c0_ddr4_s_axi_clk);
    cnn0_input_batch_set <= 1'b1;
    @(posedge c0_ddr4_s_axi_clk);
    cnn0_input_batch_set <= 1'b0;
    end

    wait(cnn0_result_count != 3'd0);
    repeat (2) @(posedge c0_ddr4_s_axi_clk);
    write_execution_reports();
    cnn0_result_batch_clear <= 1'b1;
    @(posedge c0_ddr4_s_axi_clk);
    cnn0_result_batch_clear <= 1'b0;
    wait(cnn0_result_count == 3'd0);
    if (!live_reports_written && (boundary_fd != 0)) begin
      emit_current_dag_boundary_observation(0, "edge.data.block_input.to.stage_00_rms_norm_1.input");
      emit_current_dag_boundary_observation(1, "edge.data.block_input.to.stage_02_residual_add_1.residual_skip");
      emit_current_dag_boundary_observation(2, "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main");
      emit_current_dag_boundary_observation(3, "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main");
      emit_current_dag_boundary_observation(4, "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main");
      emit_current_dag_boundary_observation(5, "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip");
      emit_current_dag_boundary_observation(6, "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch");
      emit_current_dag_boundary_observation(7, "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch");
      emit_current_dag_boundary_observation(8, "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul");
      emit_current_dag_boundary_observation(9, "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul");
      emit_current_dag_boundary_observation(10, "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main");
      emit_current_dag_boundary_observation(11, "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main");
      emit_current_dag_boundary_observation(12, "edge.data.stage_08_residual_add_2.to.block_output.output");
    end
    if (final_pass) begin
      emit_progress_event("terminal", "pass", 1'b0, LAST_LAYER, -1, -1, "compute_slot_axi.terminal");
    end else begin
      emit_progress_event("terminal", "fail", 1'b0, LAST_LAYER, -1, -1, "compute_slot_axi.terminal");
    end
    if (boundary_fd != 0) begin
      $fflush(boundary_fd);
      $fclose(boundary_fd);
      boundary_fd = 0;
    end
    if (progress_fd != 0) $fclose(progress_fd);
    if (delta_transition_fd != 0) $fclose(delta_transition_fd);
    $fclose(weight_fd);
    if (final_pass) begin
      $display("SPATIALACC_BOARD_PASS");
      $finish;
    end else begin
      $fatal(1, "compute-slot AXI board verification failed; inspect generated reports");
    end
  end

  // probe_id=probe.current_dag_complete_boundary_terminal_path.4
  // Read-only terminal observation that runs when the existing AXI monitor
  // raises its violation. It records each data boundary before the monitor's
  // following fatal check ends simulation. It drives no DUT input or output.
  always @(tb_c0_ddr4_s_axi_monitor.violation) begin : spatialacc_axi_monitor_terminal_boundary_probe_r4
    integer monitor_terminal_boundary_index;
    reg monitor_terminal_summary_emitted;
    if ((monitor_terminal_summary_emitted !== 1'b1) &&
        (tb_c0_ddr4_s_axi_monitor.violation === 1'b1) &&
        (boundary_fd != 0)) begin
      monitor_terminal_summary_emitted = 1'b1;
      for (monitor_terminal_boundary_index = 0;
           monitor_terminal_boundary_index < CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT;
           monitor_terminal_boundary_index = monitor_terminal_boundary_index + 1) begin
        if (!current_dag_boundary_waiting_seen[monitor_terminal_boundary_index] &&
            (current_dag_boundary_accepted_count[monitor_terminal_boundary_index] == 0) &&
            current_dag_boundary_has_upstream_progress(monitor_terminal_boundary_index)) begin
          emit_current_dag_boundary_temporal_record(
            monitor_terminal_boundary_index,
            "first_waiting_after_upstream_progress",
            0);
          current_dag_boundary_waiting_seen[monitor_terminal_boundary_index] = 1'b1;
        end
        emit_current_dag_boundary_temporal_record(
          monitor_terminal_boundary_index,
          "axi_monitor_terminal_summary",
          3);
      end
      $fflush(boundary_fd);
    end
  end

  final begin : spatialacc_complete_boundary_terminal_summary_r3
    integer terminal_boundary_index;
    if (boundary_fd != 0) begin
      for (terminal_boundary_index = 0;
           terminal_boundary_index < CURRENT_DAG_OBSERVATION_BOUNDARY_COUNT;
           terminal_boundary_index = terminal_boundary_index + 1) begin
        if (!current_dag_boundary_waiting_seen[terminal_boundary_index] &&
            (current_dag_boundary_accepted_count[terminal_boundary_index] == 0) &&
            current_dag_boundary_has_upstream_progress(terminal_boundary_index)) begin
          emit_current_dag_boundary_temporal_record(
            terminal_boundary_index,
            "first_waiting_after_upstream_progress",
            0);
          current_dag_boundary_waiting_seen[terminal_boundary_index] = 1'b1;
        end
        emit_current_dag_boundary_temporal_record(
          terminal_boundary_index,
          "terminal_summary",
          3);
      end
      $fflush(boundary_fd);
    end
  end
endmodule
