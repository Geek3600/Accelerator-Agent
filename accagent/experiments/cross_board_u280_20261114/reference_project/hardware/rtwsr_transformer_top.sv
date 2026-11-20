`timescale 1ns / 1ps

module rtwsr_transformer_top #(
    parameter int MODEL_ID = 0,
    parameter int LINEAR_CHANNELS = 96,
    parameter int MAX_CONTEXT = 2048,
    parameter int DATA_W = 16,
    parameter int LANES = 128,
    parameter int HBM_LOAD_LANES = 24,
    parameter bit HBM_PARALLEL_LOAD = 1'b0,
    parameter bit GAMMA_PARALLEL_LOAD = 1'b0,
    parameter bit CORE_TIMING_CANDIDATE = 1'b0,
    parameter bit CORE_128TRIT_CANDIDATE = 1'b0,
    parameter bit RESIDUAL_NORM_FUSION = 1'b0,
    parameter bit RESIDUAL_NORM_TILE_PRELOAD = 1'b0,
    parameter bit POOL_READ_PARALLEL_SLOTS = 1'b0,
    parameter bit ATTENTION_PARALLEL_CANDIDATE = 1'b0,
    parameter bit ADAPTER_STATIC_REUSE = 1'b0,
    parameter int ATTENTION_PARALLEL_HEADS = 4,
    parameter bit ATTENTION_QUANT_STREAM_PIPELINE = 1'b0,
    parameter int RECURRENCES_OVERRIDE = 0
)(
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         start,
    input  logic [15:0]                  context_tokens,
    output logic                         command_valid,
    output logic [4:0]                   command_id,
    output logic [3:0]                   command_stage,
    output logic [5:0]                   block_index,
    output logic [4:0]                   recurrence_index,
    output logic [1:0]                   command_index,
    output logic [15:0]                  matrix_rows,
    output logic [15:0]                  matrix_columns,
    output logic [15:0]                  vector_length,
    output logic [15:0]                  active_context_tokens,
    output logic                         attention_is_full,
    output logic                         payload_descriptor_valid,
    output logic                         payload_descriptor_adapter_file,
    output logic [31:0]                  payload_weight_offset_bytes,
    output logic [31:0]                  payload_weight_bytes,
    output logic [31:0]                  payload_weight_words,
    output logic [31:0]                  payload_gamma_offset_bytes,
    output logic [31:0]                  payload_gamma_bytes,
    output logic [31:0]                  payload_gamma_words,
    output logic [15:0]                  payload_matrix_rows,
    output logic [15:0]                  payload_matrix_columns,
    output logic                         done,
    output logic                         error,
    input  logic                         operator_ready,
    input  logic                         operator_done,
    output logic                         linear_engine_valid,
    output logic [4:0]                   linear_engine_command_id,
    output logic [5:0]                   linear_engine_block_index,
    output logic [4:0]                   linear_engine_recurrence_index,
    output logic [15:0]                  linear_engine_rows,
    output logic [15:0]                  linear_engine_columns,
    output logic [6:0]                   linear_engine_window_count,
    output logic [14:0]                  linear_engine_pool_words_per_port,
    output logic [14:0]                  linear_engine_tile_pool_base_per_port,
    output logic [8:0]                   linear_engine_tile_index,
    output logic [15:0]                  linear_engine_tile_row_start,
    output logic [((LINEAR_CHANNELS <= 127) ? 7 : 8)-1:0] linear_engine_tile_rows,
    output logic                         linear_engine_tile_ready,
    output logic                         linear_engine_tile_done,
    output logic                         linear_result_valid,
    input  logic                         linear_result_ready,
    output logic [3071:0]                linear_result_q12,
    output logic [6:0]                   linear_result_rows,
    output logic [6:0]                   linear_activation_window_index,

    input  logic                         weight_start,
    output logic                         weight_load_request_ready,
    input  logic                         weight_abort,
    input  logic                         weight_prefetch_start,
    output logic                         weight_prefetch_ready,
    input  logic [4:0]                   weight_prefetch_command_id,
    input  logic [5:0]                   weight_prefetch_block_index,
    input  logic [4:0]                   weight_prefetch_recurrence_index,
    input  logic [15:0]                  weight_prefetch_rows,
    input  logic [15:0]                  weight_prefetch_columns,
    input  logic                         weight_stream_valid,
    output logic                         weight_stream_ready,
    input  logic [511:0]                 weight_stream_data,
    input  logic                         weight_stream_last,
    output logic                         hbm_weight_load_start,
    output logic [15:0]                  hbm_weight_load_rows,
    output logic [15:0]                  hbm_weight_load_columns,
    output logic [4:0]                   hbm_weight_load_command_id,
    output logic [5:0]                   hbm_weight_load_block_index,
    output logic                         hbm_weight_skip_adapter_static,
    input  logic                         hbm_pool_load_valid,
    output logic                         hbm_pool_load_ready,
    input  logic [HBM_LOAD_LANES-1:0]    hbm_pool_load_enable,
    input  logic [HBM_LOAD_LANES*14-1:0] hbm_pool_load_address,
    input  logic [HBM_LOAD_LANES*512-1:0] hbm_pool_load_data,
    output logic                         weight_store_busy,
    output logic                         weight_load_done,
    output logic                         weight_protocol_error,
    output logic [16:0]                  shadow_occupancy,
    input  logic [2:0]                   round_config_valid,
    output logic [2:0]                   round_config_ready,
    input  logic [15:0]                  round_activation_scale_fp16,
    input  logic                         gamma_load_start,
    output logic                         gamma_load_start_ready,
    input  logic [4:0]                   gamma_load_command_id,
    input  logic [5:0]                   gamma_load_block_index,
    input  logic [4:0]                   gamma_load_recurrence_index,
    input  logic [15:0]                  gamma_load_matrix_rows,
    input  logic [15:0]                  gamma_load_matrix_columns,
    input  logic                         gamma_load_valid,
    output logic                         gamma_load_ready,
    input  logic [31:0]                  gamma_load_pair_data,
    input  logic [511:0]                 gamma_load_vector_data,
    input  logic                         gamma_load_last,
    output logic                         gamma_load_done,
    output logic                         gamma_protocol_error,
    input  logic [2:0]                   activation_valid,
    output logic [2:0]                   activation_ready,
    input  logic [256*8-1:0]             activation_window,

    input  logic [10:0]                  rope_write_position,
    input  logic [11:0]                  rope_active_context_tokens,
    input  logic [10:0]                  rope_window_start,
    input  logic [4095:0]                 rope_query_q4_12,
    input  logic [4095:0]                 rope_key_q4_12,
    input  logic [4095:0]                 rope_value_q4_12,
    input  logic [4095:0]                 rope_sin_q1_15,
    input  logic [4095:0]                 rope_cos_q1_15,
    output logic                         rope_ready,
    output logic                         rope_query_valid,
    output logic [4095:0]                 rope_query_rotated_q4_12,
    input  logic                         rope_kv_ready,
    output logic                         rope_kv_valid,
    output logic [10:0]                  rope_kv_token_index,
    output logic [1:0]                   rope_kv_chunk_index,
    output logic [2047:0]                rope_kv_key_chunk_q4_12,
    output logic [2047:0]                rope_kv_value_chunk_q4_12,
    output logic                         rope_kv_last,
    input  logic                         rope_cache_load_valid,
    input  logic [10:0]                  rope_cache_load_index,
    input  logic [4095:0]                 rope_cache_load_key_q4_12,
    input  logic [4095:0]                 rope_cache_load_value_q4_12,
    output logic                         rope_cache_read_request,
    input  logic                         rope_cache_read_request_ready,
    output logic [5:0]                  rope_cache_read_head,
    output logic [10:0]                  rope_cache_read_index,
    output logic                         rope_cache_load_ready,
    input  logic [ATTENTION_PARALLEL_HEADS-1:0] rope_cache_load_valid_parallel,
    input  logic [ATTENTION_PARALLEL_HEADS*11-1:0] rope_cache_load_index_parallel,
    input  logic [ATTENTION_PARALLEL_HEADS*4096-1:0] rope_cache_load_key_q4_12_parallel,
    input  logic [ATTENTION_PARALLEL_HEADS*4096-1:0] rope_cache_load_value_q4_12_parallel,
    output logic [ATTENTION_PARALLEL_HEADS-1:0] rope_cache_read_request_parallel,
    input  logic [ATTENTION_PARALLEL_HEADS-1:0] rope_cache_read_request_ready_parallel,
    output logic [ATTENTION_PARALLEL_HEADS*6-1:0] rope_cache_read_head_parallel,
    output logic [ATTENTION_PARALLEL_HEADS*11-1:0] rope_cache_read_index_parallel,
    output logic [ATTENTION_PARALLEL_HEADS-1:0] rope_cache_load_ready_parallel,
    output logic                         rope_busy,
    output logic                         rope_done,
    output logic                         rope_protocol_error,

    input  logic [4095:0]                 attention_query_q4_12,
    input  logic                         attention_kv_valid,
    output logic                         attention_kv_ready,
    input  logic [2047:0]                attention_kv_key_q4_12,
    input  logic [2047:0]                attention_kv_value_q4_12,
    output logic                         attention_out_valid,
    input  logic                         attention_out_ready,
    output logic [2047:0]                attention_out_chunk_q4_12,
    output logic                         attention_out_last,
    output logic                         attention_ready,
    output logic                         attention_busy,
    output logic                         attention_done,
    output logic                         attention_protocol_error,

    input  logic                         norm_in_valid,
    output logic                         norm_in_ready,
    input  logic [255:0]                 norm_in_activation_q4_12,
    input  logic [255:0]                 norm_in_gamma_q4_12,
    output logic                         norm_gamma_chunk_request,
    output logic [8:0]                   norm_gamma_chunk_index,
    output logic [2:0]                   norm_gamma_chunk_lane,
    output logic                         norm_preload_gamma_request,
    output logic [4:0]                   norm_preload_gamma_command_id,
    output logic [8:0]                   norm_preload_gamma_tile_index,
    input  logic                         norm_preload_gamma_valid,
    input  logic [1535:0]                norm_preload_gamma_q4_12,
    input  logic                         norm_in_last,
    output logic                         norm_out_valid,
    input  logic                         norm_out_ready,
    output logic [255:0]                 norm_out_normalized_q4_12,
    output logic [127:0]                 norm_out_quantized_int8,
    output logic                         norm_out_last,
    output logic [15:0]                  norm_inv_rms_q15,
    output logic [15:0]                  norm_activation_scale_q4_12,
    output logic                         norm_ready,
    output logic                         norm_busy,
    output logic                         norm_done,
    output logic                         norm_protocol_error,

    input  logic                         swiglu_in_valid,
    output logic                         swiglu_in_ready,
    input  logic [255:0]                 swiglu_gate_q4_12,
    input  logic [255:0]                 swiglu_up_q4_12,
    input  logic [255:0]                 swiglu_residual_q4_12,
    input  logic                         swiglu_in_last,
    input  logic [15:0]                  swiglu_residual_rate_q15,
    output logic                         swiglu_ready,
    output logic                         swiglu_out_valid,
    input  logic                         swiglu_out_ready,
    output logic [255:0]                 swiglu_output_q4_12,
    output logic                         swiglu_out_last,
    output logic                         swiglu_busy,
    output logic                         swiglu_done,
    output logic                         swiglu_protocol_error,
    output logic                         core_output_valid,
    input  logic                         core_output_ready,
    output logic [255:0]                  core_output_q4_12,
    output logic                         core_output_last,
    output logic                         core_output_done
);
    localparam int MODEL_HUGINN = 0;
    localparam int MODEL_OURO = 1;
    localparam int MODEL_DORY = 2;
    localparam int HIDDEN_SIZE = MODEL_ID == MODEL_HUGINN ? 5280 :
                                 MODEL_ID == MODEL_OURO ? 2048 : 2560;
    localparam int QUERY_SIZE = MODEL_ID == MODEL_HUGINN ? 5280 :
                                MODEL_ID == MODEL_OURO ? 2048 : 4096;
    localparam int KV_SIZE = MODEL_ID == MODEL_DORY ? 1024 : QUERY_SIZE;
    localparam int INTERMEDIATE_SIZE = MODEL_ID == MODEL_HUGINN ? 17920 :
                                       MODEL_ID == MODEL_OURO ? 5632 : 7168;
    localparam int HEAD_DIM = MODEL_ID == MODEL_HUGINN ? 96 :
                              MODEL_ID == MODEL_OURO ? 128 : 256;
    localparam int QUERY_HEADS = QUERY_SIZE / HEAD_DIM;
    localparam int HEAD_INDEX_WIDTH = (QUERY_HEADS <= 1) ? 1 : $clog2(QUERY_HEADS);
    localparam int HEAD_DIM_INDEX_WIDTH = (HEAD_DIM <= 1) ? 1 : $clog2(HEAD_DIM);
    localparam int QKV_READ_CHUNKS = (HEAD_DIM + 95) / 96;
    localparam int QKV_READ_CHUNK_INDEX_WIDTH = (QKV_READ_CHUNKS <= 1) ? 1 : $clog2(QKV_READ_CHUNKS);
    localparam int ATTENTION_OUTPUT_CHUNKS = (HEAD_DIM + LANES - 1) / LANES;
    localparam int ATTENTION_OUTPUT_CHUNK_INDEX_WIDTH = (ATTENTION_OUTPUT_CHUNKS <= 1) ? 1 :
                                                         $clog2(ATTENTION_OUTPUT_CHUNKS);
    localparam int NORM_MAX_VECTOR_LEN = MODEL_ID == MODEL_DORY ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
    localparam int NORM_CHUNKS = (NORM_MAX_VECTOR_LEN + 15) / 16;
    localparam int NORM_COUNT_WIDTH = (NORM_CHUNKS <= 1) ? 1 : $clog2(NORM_CHUNKS);
    localparam int NORMALIZED_ACTIVATION_WINDOWS = (HIDDEN_SIZE + 255) / 256;
    localparam int ADAPTER_STATE_FULL_WINDOWS = HIDDEN_SIZE / 256;
    localparam int ADAPTER_STATE_TAIL_BYTES = HIDDEN_SIZE % 256;
    localparam int ADAPTER_INPUT_WINDOWS = (2 * HIDDEN_SIZE + 255) / 256;
    localparam int ADAPTER_EMBEDDING_WINDOWS = ADAPTER_INPUT_WINDOWS - ADAPTER_STATE_FULL_WINDOWS;
    localparam int ATTENTION_ACTIVATION_WINDOWS = (QUERY_SIZE + 255) / 256;
    localparam int FFN_ACTIVATION_WINDOWS = (INTERMEDIATE_SIZE + 255) / 256;
    localparam int LINEAR_ROW_COUNT_WIDTH = (LINEAR_CHANNELS <= 127) ? 7 : 8;
    localparam int RESULT_CHUNKS = LINEAR_CHANNELS / 96;
    localparam int STATE_BANKS = 6;
    localparam int STATE_TILE_COUNT = (HIDDEN_SIZE + 95) / 96;
    localparam int NORM_VECTOR_WIDTH = 16 * 16;
    localparam int SWIGLU_VECTOR_WIDTH = 16 * 16;
    localparam int ROPE_VECTOR_WIDTH = HEAD_DIM * 16;
    localparam int ROPE_TRIG_WIDTH = HEAD_DIM * 16;
    localparam int ROPE_CHUNK_COUNT = (HEAD_DIM + LANES - 1) / LANES;
    localparam int ROPE_CHUNK_INDEX_WIDTH = (ROPE_CHUNK_COUNT <= 1) ? 1 : $clog2(ROPE_CHUNK_COUNT);
    localparam int ATTENTION_CONTEXT_WIDTH = $clog2(MAX_CONTEXT + 1);
    localparam int ATTENTION_QUERY_WIDTH = HEAD_DIM * 16;
    localparam int ATTENTION_CHUNK_WIDTH = LANES * 16;
    localparam bit ATTENTION_PARALLEL_VALID = ATTENTION_PARALLEL_CANDIDATE && MODEL_ID == MODEL_HUGINN;

    localparam logic [4:0] CMD_SCORE_SOFTMAX = 5'd6;
    localparam logic [4:0] CMD_CONTEXT = 5'd7;
    localparam logic [4:0] CMD_CONTEXT_GATE_NORM = 5'd8;
    localparam logic [4:0] CMD_ROPE_KV = 5'd5;
    localparam logic [4:0] CMD_PRE_ATTN_NORM = 5'd2;
    localparam logic [4:0] CMD_ATTN_POST = 5'd10;
    localparam logic [4:0] CMD_PRE_FFN_NORM = 5'd11;
    localparam logic [4:0] CMD_SWIGLU = 5'd13;
    localparam logic [4:0] CMD_PRE_DOWN_JUSTNORM = 5'd14;
    localparam logic [4:0] CMD_MLP_POST = 5'd16;
    localparam logic [4:0] CMD_RECURRENCE_POST = 5'd17;
    localparam logic [4:0] CMD_ADAPTER = 5'd0;
    localparam logic [4:0] CMD_O_PROJ = 5'd9;
    localparam logic [4:0] CMD_DOWN = 5'd15;
    localparam logic [4:0] CMD_GATE_PROJ = 5'd21;
    localparam logic [4:0] CMD_UP_PROJ = 5'd22;

    logic scheduler_command_ready;
    logic scheduler_command_done;
    logic rope_start;
    logic attention_start;
    logic norm_start;
    logic swiglu_start;

    logic [4:0] scheduler_command_id;
    logic payload_descriptor_raw_valid;
    logic [3:0] scheduler_command_stage;
    logic [5:0] scheduler_block_index;
    logic [4:0] scheduler_recurrence_index;
    logic [1:0] scheduler_command_index;
    logic [15:0] scheduler_matrix_rows;
    logic [15:0] scheduler_matrix_columns;
    logic [15:0] scheduler_vector_length;
    logic [15:0] scheduler_active_context_tokens;
    logic scheduler_attention_is_full;
    logic dispatch_command_ready;
    logic dispatch_command_done;
    logic dispatch_linear_valid;
    logic linear_command_ready;
    logic linear_command_done;
    logic linear_command_error;
    logic scheduler_error;
    logic tile_execution_ready, tile_execution_error;
    logic gemv_result_valid, gemv_result_ready, gemv_tile_done;
    logic [LINEAR_CHANNELS*32-1:0] gemv_result_q12;
    logic [LINEAR_ROW_COUNT_WIDTH-1:0] gemv_result_rows;
    logic [15:0] linear_result_row_start;
    logic result_serialize_valid_q;
    logic [LINEAR_CHANNELS*32-1:0] result_serialize_data_q;
    logic [LINEAR_ROW_COUNT_WIDTH-1:0] result_serialize_rows_q;
    logic [15:0] result_serialize_row_start_q;
    logic [7:0] result_serialize_offset_q;
    logic [4:0] dispatch_command_id;
    logic [5:0] dispatch_block_index;
    logic [4:0] dispatch_recurrence_index;
    logic [15:0] dispatch_matrix_rows;
    logic [15:0] dispatch_matrix_columns;
    logic [4:0] tile_command_id;
    logic [5:0] tile_block_index;
    logic [4:0] tile_recurrence_index;
    logic [15:0] tile_matrix_rows;
    logic [15:0] tile_matrix_columns;
    logic adapter_result_sink;
    logic linear_result_ready_to_engine;
    logic [2:0] gemv_activation_valid;
    logic [256*8-1:0] gemv_activation_window;
    logic [15:0] gemv_activation_scale_fp16;
    logic norm_use_recurrent_state;
    logic adapter_internal_activation;
    logic adapter_embedding_valid_q;
    (* ram_style = "distributed" *) logic [2047:0]
        adapter_embedding_memory [0:ADAPTER_EMBEDDING_WINDOWS-1];
    logic linear_result_targets_qkv;
    logic norm_feed_valid;
    logic norm_feed_last;
    logic [255:0] norm_feed_activation;
    logic norm_unit_out_ready;
    logic recurrent_state_valid_q;
    logic activation_buffer_valid_q;
    logic [15:0] recurrent_activation_scale_fp16_q;
    logic [NORM_COUNT_WIDTH-1:0] norm_state_chunk_q;
    logic [NORM_COUNT_WIDTH:0] norm_state_request_chunk_q;
    logic norm_state_data_valid_q;
    logic [NORM_COUNT_WIDTH-1:0] norm_output_chunk_q;
    logic [2:0] state_read_bank;
    logic [8:0] state_read_tile_index;
    logic state_read_enable;
    logic core_output_read_enable;
    logic [NORM_COUNT_WIDTH-1:0] core_output_chunk_q;
    logic core_output_data_valid_q;
    logic core_output_complete_q;
    logic [1535:0] recurrent_state_write_data;
    logic [255:0] recurrent_state_read_data [0:STATE_BANKS-1];
    logic [255:0] recurrent_delta_read_data [0:STATE_BANKS-1];
    logic [255:0] residual_tile_state [0:STATE_BANKS*RESULT_CHUNKS-1];
    logic [1535:0] fused_residual_data;
    logic [63:0] fused_tile_sum_square, fused_sum_square_q;
    logic fused_sum_valid_q;
    logic fused_residual_write, fused_norm_input, fused_norm_preload;
    logic norm_add_residual;
    logic qkv_buffer_ready, qkv_buffer_valid, qkv_read_ready, qkv_read_valid;
    logic [1535:0] qkv_query_chunk, qkv_key_chunk, qkv_value_chunk;
    logic bridge_start, bridge_ready, bridge_done, bridge_error;
    logic serial_bridge_ready, serial_bridge_done, serial_bridge_error;
    logic bridge_qkv_read_start, bridge_qkv_read_done;
    logic [HEAD_INDEX_WIDTH-1:0] bridge_qkv_read_head;
    logic [QKV_READ_CHUNK_INDEX_WIDTH-1:0] bridge_qkv_read_chunk;
    logic bridge_rope_start, bridge_rope_kv_ready;
    logic [ROPE_VECTOR_WIDTH-1:0] bridge_rope_query, bridge_rope_key, bridge_rope_value;
    logic bridge_attention_start, bridge_attention_kv_valid, bridge_attention_out_ready;
    logic [ROPE_VECTOR_WIDTH-1:0] bridge_attention_query;
    logic [ATTENTION_CHUNK_WIDTH-1:0] bridge_attention_kv_key, bridge_attention_kv_value;
    logic bridge_context_valid, bridge_context_last;
    logic [HEAD_INDEX_WIDTH-1:0] bridge_context_head;
    logic [ATTENTION_OUTPUT_CHUNK_INDEX_WIDTH-1:0] bridge_context_chunk;
    logic [ATTENTION_CHUNK_WIDTH-1:0] bridge_context_data;
    logic qkv_parallel_read_start, qkv_parallel_read_ready, qkv_parallel_read_valid;
    logic qkv_parallel_read_done;
    logic [ATTENTION_PARALLEL_HEADS-1:0] qkv_parallel_read_mask;
    logic [ATTENTION_PARALLEL_HEADS*HEAD_INDEX_WIDTH-1:0] qkv_parallel_read_heads;
    logic [ATTENTION_PARALLEL_HEADS*QKV_READ_CHUNK_INDEX_WIDTH-1:0] qkv_parallel_read_chunks;
    logic [ATTENTION_PARALLEL_HEADS*1536-1:0] qkv_parallel_query_chunks, qkv_parallel_key_chunks, qkv_parallel_value_chunks;
    logic parallel_bridge_ready, parallel_bridge_done, parallel_bridge_error;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_rope_start, parallel_rope_ready, parallel_rope_query_valid;
    logic [ATTENTION_PARALLEL_HEADS*ROPE_VECTOR_WIDTH-1:0] parallel_rope_queries, parallel_rope_keys, parallel_rope_values;
    logic [ATTENTION_PARALLEL_HEADS*ROPE_VECTOR_WIDTH-1:0] parallel_rope_queries_rotated;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_rope_done, parallel_rope_error;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_rope_kv_valid, parallel_rope_kv_ready;
    logic [ATTENTION_PARALLEL_HEADS*ATTENTION_CHUNK_WIDTH-1:0] parallel_rope_kv_keys, parallel_rope_kv_values;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_attention_start;
    logic parallel_attention_ready;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_attention_ready_by_head;
    logic [ATTENTION_PARALLEL_HEADS*ROPE_VECTOR_WIDTH-1:0] parallel_attention_queries;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_attention_kv_valid, parallel_attention_kv_ready;
    logic [ATTENTION_PARALLEL_HEADS*ATTENTION_CHUNK_WIDTH-1:0] parallel_attention_kv_keys, parallel_attention_kv_values;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_attention_done, parallel_attention_error, parallel_attention_out_valid;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_attention_out_ready;
    logic [ATTENTION_PARALLEL_HEADS*ATTENTION_CHUNK_WIDTH-1:0] parallel_attention_out;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_context_valid;
    logic [ATTENTION_PARALLEL_HEADS*HEAD_INDEX_WIDTH-1:0] parallel_context_heads;
    logic [ATTENTION_PARALLEL_HEADS*ATTENTION_OUTPUT_CHUNK_INDEX_WIDTH-1:0] parallel_context_chunks;
    logic [ATTENTION_PARALLEL_HEADS*ATTENTION_CHUNK_WIDTH-1:0] parallel_context_data;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_cache_load_valid, parallel_cache_load_ready;
    logic [ATTENTION_PARALLEL_HEADS*11-1:0] parallel_cache_load_indices, parallel_cache_read_indices;
    logic [ATTENTION_PARALLEL_HEADS*4096-1:0] parallel_cache_load_keys, parallel_cache_load_values;
    logic [ATTENTION_PARALLEL_HEADS-1:0] parallel_cache_read_request, parallel_cache_read_request_ready;
    logic [ATTENTION_PARALLEL_HEADS*6-1:0] parallel_cache_read_heads;
    logic [ATTENTION_PARALLEL_HEADS*ROPE_VECTOR_WIDTH-1:0] parallel_cache_query_rotated;
    logic attention_activation_buffer_valid_q;
    logic [15:0] attention_activation_scale_fp16_q;
    logic [15:0] attention_activation_scale_q4_12_q;
    logic [2047:0] attention_activation_window_q;
    (* ram_style = "block" *) logic [ATTENTION_CHUNK_WIDTH-1:0]
        attention_context_chunk_memory [0:QUERY_HEADS*ATTENTION_OUTPUT_CHUNKS-1];
    (* ram_style = "block" *) logic [ATTENTION_CHUNK_WIDTH-1:0]
        attention_context_chunk_memory_parallel [0:ATTENTION_PARALLEL_HEADS-1]
            [0:QUERY_HEADS*ATTENTION_OUTPUT_CHUNKS-1];
    (* ram_style = "distributed" *) logic [2047:0]
        attention_activation_memory [0:ATTENTION_ACTIVATION_WINDOWS-1];
    typedef enum logic [2:0] {
        ATTN_QUANT_IDLE,
        ATTN_QUANT_SCAN,
        ATTN_QUANTIZE,
        ATTN_QUANT_DIVIDE,
        ATTN_QUANT_STORE,
        ATTN_QUANT_DRAIN,
        ATTN_QUANT_FLUSH
    } attention_quant_state_t;
    attention_quant_state_t attention_quant_state_q;
    logic [15:0] attention_quant_index_q;
    logic [HEAD_INDEX_WIDTH-1:0] attention_quant_head_q;
    logic [HEAD_DIM_INDEX_WIDTH-1:0] attention_quant_dimension_q;
    logic [15:0] attention_max_abs_q4_12_q;
    logic attention_quantized_valid_q;
    logic [7:0] attention_quantized_index_q;
    logic [7:0] attention_quantized_value_q;
    logic attention_quant_negative_q;
    logic attention_divider_ready;
    logic attention_divider_done;
    logic [15:0] attention_divider_dividend;
    logic [15:0] attention_divider_divisor;
    logic [7:0] attention_divider_quotient;
    logic attention_stream_output_valid;
    logic [7:0] attention_stream_quotient;
    logic attention_stream_negative;
    logic [15:0] attention_stream_output_index;
    logic [2047:0] attention_activation_window_next;
    logic signed [8:0] attention_stream_quantized_value;
    logic signed [15:0] attention_quant_input;
    logic [15:0] attention_quant_abs;
    logic ffn_pipeline_write_ready;
    logic ffn_activation_valid;
    logic [2047:0] ffn_activation_window;
    logic [15:0] ffn_activation_scale_fp16;
    logic linear_result_internal_sink;

    always_comb begin
        integer quant_head;
        integer quant_dimension;
        integer quant_lane;
        integer quant_address;
        quant_head = int'(attention_quant_head_q);
        quant_dimension = int'(attention_quant_dimension_q);
        quant_lane = quant_dimension % LANES;
        quant_address = quant_head * ATTENTION_OUTPUT_CHUNKS + quant_dimension / LANES;
        if (ATTENTION_PARALLEL_VALID)
            attention_quant_input = $signed(attention_context_chunk_memory_parallel[quant_head % ATTENTION_PARALLEL_HEADS]
                [quant_address][quant_lane*16 +: 16]);
        else
            attention_quant_input = $signed(attention_context_chunk_memory[quant_address]
                                            [quant_lane*16 +: 16]);
        attention_quant_abs = attention_quant_input < 0 ?
                              16'(-attention_quant_input) : 16'(attention_quant_input);
        attention_divider_dividend = attention_quant_abs +
                                     (attention_activation_scale_q4_12_q >> 1);
        attention_divider_divisor = attention_activation_scale_q4_12_q;
        attention_activation_window_next = attention_activation_window_q;
        attention_stream_quantized_value = '0;
        if (attention_stream_negative)
            attention_stream_quantized_value = -$signed({1'b0, attention_stream_quotient});
        else
            attention_stream_quantized_value = $signed({1'b0, attention_stream_quotient});
        if (ATTENTION_QUANT_STREAM_PIPELINE && attention_stream_output_valid) begin
            if (attention_stream_output_index[7:0] == 0)
                attention_activation_window_next = '0;
            attention_activation_window_next[
                int'(attention_stream_output_index[7:0]) * 8 +: 8] =
                attention_stream_quantized_value[7:0];
        end
    end

    generate
        if (ATTENTION_QUANT_STREAM_PIPELINE) begin : g_attention_quant_stream
            rtwsr_round_divider_stream7 u_attention_round_divider (
                .clk(clk), .rst_n(rst_n && !weight_abort),
                .input_valid(attention_quant_state_q == ATTN_QUANTIZE),
                .dividend(attention_divider_dividend),
                .divisor(attention_divider_divisor),
                .input_negative(attention_quant_input < 0),
                .input_index(attention_quant_index_q),
                .output_valid(attention_stream_output_valid),
                .quotient(attention_stream_quotient),
                .output_negative(attention_stream_negative),
                .output_index(attention_stream_output_index)
            );
            assign attention_divider_ready = 1'b1;
            assign attention_divider_done = 1'b0;
            assign attention_divider_quotient = attention_stream_quotient;
        end else begin : g_attention_quant_serial
            rtwsr_round_divider_7bit #(.FAST(CORE_TIMING_CANDIDATE)) u_attention_round_divider (
                .clk(clk), .rst_n(rst_n), .start(attention_quant_state_q == ATTN_QUANTIZE),
                .dividend(attention_divider_dividend), .divisor(attention_divider_divisor),
                .ready(attention_divider_ready), .done(attention_divider_done),
                .quotient(attention_divider_quotient)
            );
            assign attention_stream_output_valid = 1'b0;
            assign attention_stream_quotient = '0;
            assign attention_stream_negative = 1'b0;
            assign attention_stream_output_index = '0;
        end
    endgenerate

    logic [2047:0] normalized_activation_window_q;
    (* ram_style = "distributed" *) logic [2047:0]
        normalized_activation_memory [0:NORMALIZED_ACTIVATION_WINDOWS-1];

    function automatic logic signed [15:0] saturate_q4_12(input logic signed [31:0] value);
        begin
            if (value > 32'sd32767)
                saturate_q4_12 = 16'sd32767;
            else if (value < -32'sd32768)
                saturate_q4_12 = -16'sd32768;
            else
                saturate_q4_12 = value[15:0];
        end
    endfunction

    function automatic logic [15:0] q4_12_to_fp16(input logic [15:0] value);
        integer leading_bit;
        integer bit_index;
        logic [15:0] significand;
        begin
            leading_bit = -1;
            significand = '0;
            for (bit_index = 15; bit_index >= 0; bit_index = bit_index - 1)
                if (value[bit_index] && leading_bit < 0)
                    leading_bit = bit_index;
            if (leading_bit < 0)
                q4_12_to_fp16 = 16'h0000;
            else begin
                if (leading_bit > 10)
                    significand = value >> (leading_bit - 10);
                else
                    significand = value << (10 - leading_bit);
                q4_12_to_fp16 = {1'b0, 5'(leading_bit + 3), significand[9:0]};
            end
        end
    endfunction

    always_comb begin
        integer lane;
        integer residual_chunk;
        logic signed [31:0] q12_value;
        logic signed [16:0] residual_sum;
        logic signed [15:0] residual_value;
        logic signed [31:0] square_value;
        recurrent_state_write_data = '0;
        fused_residual_data = '0;
        fused_tile_sum_square = '0;
        residual_sum = '0;
        residual_value = '0;
        square_value = '0;
        residual_chunk = (int'(linear_result_row_start) / 96) % RESULT_CHUNKS;
        for (lane = 0; lane < 96; lane = lane + 1) begin
            if (lane < int'(linear_result_rows)) begin
                q12_value = $signed(linear_result_q12[lane*32 +: 32]);
                recurrent_state_write_data[lane*16 +: 16] = saturate_q4_12(q12_value);
                residual_sum = $signed(residual_tile_state[
                    residual_chunk*STATE_BANKS + lane/16][(lane % 16)*16 +: 16]) +
                    $signed(recurrent_state_write_data[lane*16 +: 16]);
                residual_value = saturate_q4_12({{15{residual_sum[16]}}, residual_sum});
                fused_residual_data[lane*16 +: 16] = residual_value;
                square_value = $signed(residual_value) * $signed(residual_value);
                fused_tile_sum_square = fused_tile_sum_square + 64'($unsigned(square_value));
            end
        end
    end

    assign fused_residual_write = RESIDUAL_NORM_FUSION && MODEL_ID == MODEL_HUGINN &&
        recurrent_state_valid_q && (linear_engine_command_id == CMD_O_PROJ ||
                                    linear_engine_command_id == CMD_DOWN);
    assign norm_use_recurrent_state = MODEL_ID == MODEL_HUGINN &&
        recurrent_state_valid_q &&
        (scheduler_command_id == CMD_PRE_ATTN_NORM ||
         scheduler_command_id == CMD_ATTN_POST ||
         scheduler_command_id == CMD_PRE_FFN_NORM ||
         scheduler_command_id == CMD_MLP_POST);
    assign norm_add_residual = norm_use_recurrent_state &&
        (scheduler_command_id == CMD_ATTN_POST || scheduler_command_id == CMD_MLP_POST);
    assign fused_norm_input = RESIDUAL_NORM_FUSION && norm_add_residual && fused_sum_valid_q;
    assign fused_norm_preload = RESIDUAL_NORM_TILE_PRELOAD && fused_norm_input;
    assign norm_preload_gamma_request = RESIDUAL_NORM_TILE_PRELOAD && fused_residual_write &&
        linear_result_valid;
    assign norm_preload_gamma_command_id = linear_engine_command_id == CMD_O_PROJ ?
        CMD_ATTN_POST : CMD_MLP_POST;
    assign norm_preload_gamma_tile_index = 9'(int'(linear_result_row_start) / 96);

    assign core_output_read_enable = MODEL_ID == MODEL_HUGINN && done &&
        !core_output_data_valid_q && !core_output_complete_q &&
        int'(core_output_chunk_q) < NORM_CHUNKS;
    assign state_read_enable = core_output_read_enable ||
        (norm_use_recurrent_state && !fused_norm_preload && !norm_start &&
         (!norm_state_data_valid_q || norm_in_ready) &&
         int'(norm_state_request_chunk_q) < NORM_CHUNKS);
    assign state_read_bank = core_output_read_enable ?
        3'(int'(core_output_chunk_q) % STATE_BANKS) :
        3'(int'(norm_state_request_chunk_q) % STATE_BANKS);
    assign state_read_tile_index = core_output_read_enable ?
        9'(int'(core_output_chunk_q) / STATE_BANKS) :
        9'(int'(norm_state_request_chunk_q) / STATE_BANKS);
    assign norm_gamma_chunk_request = state_read_enable && !core_output_read_enable;
    assign norm_gamma_chunk_index = 9'(norm_state_request_chunk_q);
    assign norm_gamma_chunk_lane = 3'(int'(norm_state_chunk_q) % STATE_BANKS);
    assign core_output_valid = MODEL_ID == MODEL_HUGINN && done && core_output_data_valid_q;
    assign core_output_q4_12 = recurrent_state_read_data[
        int'(core_output_chunk_q) % STATE_BANKS];
    assign core_output_last = core_output_valid &&
        core_output_chunk_q == NORM_COUNT_WIDTH'(NORM_CHUNKS - 1);
    assign core_output_done = core_output_complete_q;

    logic tile_launch;

    generate
        if (MODEL_ID == MODEL_HUGINN) begin : g_huginn_recurrent_state
            for (genvar state_bank = 0; state_bank < STATE_BANKS; state_bank = state_bank + 1) begin : g_bank
                (* ram_style = "block" *) logic [255:0] state_memory [0:STATE_TILE_COUNT-1];
                (* ram_style = "block" *) logic [255:0] delta_memory [0:STATE_TILE_COUNT-1];
                logic [255:0] read_data_q;
                logic [255:0] delta_read_data_q;
                logic state_write_enable;
                logic [$clog2(STATE_TILE_COUNT)-1:0] state_write_address;
                logic [255:0] state_write_data;

                assign recurrent_state_read_data[state_bank] = read_data_q;
                assign recurrent_delta_read_data[state_bank] = delta_read_data_q;

                always_comb begin
                    state_write_enable = 1'b0;
                    state_write_address = '0;
                    state_write_data = '0;
                    if (adapter_result_sink && linear_result_valid &&
                        linear_result_ready_to_engine) begin
                        state_write_enable = 1'b1;
                        state_write_address = $clog2(STATE_TILE_COUNT)'(
                            int'(linear_result_row_start) / 96);
                        state_write_data = recurrent_state_write_data[state_bank*256 +: 256];
                    end else if ((scheduler_command_id == CMD_ATTN_POST ||
                                  scheduler_command_id == CMD_MLP_POST) &&
                                 norm_use_recurrent_state && norm_out_valid &&
                                 norm_unit_out_ready && scheduler_vector_length == HIDDEN_SIZE &&
                                 (int'(norm_output_chunk_q) % STATE_BANKS) == state_bank) begin
                        state_write_enable = 1'b1;
                        state_write_address = $clog2(STATE_TILE_COUNT)'(
                            int'(norm_output_chunk_q) / STATE_BANKS);
                        state_write_data = norm_out_normalized_q4_12;
                    end
                end

                always_ff @(posedge clk) begin
                    if (rst_n && !weight_abort) begin
                        if (state_write_enable)
                            state_memory[state_write_address] <= state_write_data;
                        if (linear_result_internal_sink && linear_result_valid &&
                            linear_result_ready_to_engine &&
                            (linear_engine_command_id == CMD_O_PROJ ||
                             linear_engine_command_id == CMD_DOWN) &&
                            !(RESIDUAL_NORM_TILE_PRELOAD && fused_residual_write))
                            delta_memory[int'(linear_result_row_start) / 96] <=
                                fused_residual_write ? fused_residual_data[state_bank*256 +: 256] :
                                recurrent_state_write_data[state_bank*256 +: 256];
                        if (fused_residual_write && tile_launch) begin
                            if (LINEAR_CHANNELS == 192) begin
                                residual_tile_state[state_bank] <=
                                    state_memory[linear_engine_tile_index * 2];
                                residual_tile_state[STATE_BANKS + state_bank] <=
                                    (linear_engine_tile_index * 2 + 1 < STATE_TILE_COUNT) ?
                                    state_memory[linear_engine_tile_index * 2 + 1] : '0;
                            end else begin
                                residual_tile_state[state_bank] <=
                                    state_memory[linear_engine_tile_index];
                            end
                        end
                        if (state_read_enable && state_read_bank == 3'(state_bank)) begin
                            read_data_q <= state_memory[state_read_tile_index];
                            delta_read_data_q <= delta_memory[state_read_tile_index];
                        end
                    end
                end
            end
        end else begin : g_no_recurrent_state
            assign recurrent_state_read_data = '{default:'0};
            assign recurrent_delta_read_data = '{default:'0};
            assign residual_tile_state = '{default:'0};
        end
    endgenerate

    always_comb begin
        adapter_internal_activation = MODEL_ID == MODEL_HUGINN &&
            linear_engine_command_id == CMD_ADAPTER && adapter_embedding_valid_q &&
            recurrent_state_valid_q && activation_buffer_valid_q;
        norm_feed_valid = norm_use_recurrent_state ? norm_state_data_valid_q : norm_in_valid;
        norm_feed_last = norm_use_recurrent_state ?
            (norm_state_chunk_q == NORM_COUNT_WIDTH'(NORM_CHUNKS - 1)) : norm_in_last;
        norm_feed_activation = norm_in_activation_q4_12;
        if (norm_use_recurrent_state) begin
            norm_feed_activation = recurrent_state_read_data[int'(norm_state_chunk_q) % STATE_BANKS];
            if (fused_norm_input) begin
                norm_feed_activation = recurrent_delta_read_data[int'(norm_state_chunk_q) % STATE_BANKS];
            end else if (norm_add_residual) begin
                for (integer lane = 0; lane < 16; lane = lane + 1) begin
                    logic signed [16:0] sum_q12;
                    sum_q12 = $signed(recurrent_state_read_data[int'(norm_state_chunk_q) % STATE_BANKS]
                                      [lane*16 +: 16]) +
                              $signed(recurrent_delta_read_data[int'(norm_state_chunk_q) % STATE_BANKS]
                                      [lane*16 +: 16]);
                    norm_feed_activation[lane*16 +: 16] = saturate_q4_12(
                        {{15{sum_q12[16]}}, sum_q12});
                end
            end
        end

        gemv_activation_valid = adapter_internal_activation ||
            (linear_engine_command_id == CMD_O_PROJ && attention_activation_buffer_valid_q) ||
            (MODEL_ID == MODEL_HUGINN && linear_engine_command_id == CMD_DOWN &&
             ffn_activation_valid) ||
            activation_buffer_valid_q ? 3'b111 : activation_valid;
        if (MODEL_ID == MODEL_HUGINN && linear_engine_command_id == CMD_DOWN &&
            ffn_activation_valid)
            gemv_activation_scale_fp16 = ffn_activation_scale_fp16;
        else if (linear_engine_command_id == CMD_O_PROJ && attention_activation_buffer_valid_q)
            gemv_activation_scale_fp16 = attention_activation_scale_fp16_q;
        else
            gemv_activation_scale_fp16 = activation_buffer_valid_q ?
                recurrent_activation_scale_fp16_q : round_activation_scale_fp16;
        gemv_activation_window = activation_window;
        if (adapter_internal_activation) begin
            if (int'(linear_activation_window_index) < ADAPTER_STATE_FULL_WINDOWS)
                gemv_activation_window = normalized_activation_memory[linear_activation_window_index];
            else if (int'(linear_activation_window_index) < ADAPTER_INPUT_WINDOWS) begin
                gemv_activation_window = adapter_embedding_memory[
                    int'(linear_activation_window_index) - ADAPTER_STATE_FULL_WINDOWS];
                if (int'(linear_activation_window_index) == ADAPTER_STATE_FULL_WINDOWS) begin
                    for (integer adapter_byte = 0; adapter_byte < 256; adapter_byte++)
                        if (adapter_byte < ADAPTER_STATE_TAIL_BYTES)
                            gemv_activation_window[adapter_byte*8 +: 8] =
                                normalized_activation_memory[ADAPTER_STATE_FULL_WINDOWS]
                                    [adapter_byte*8 +: 8];
                end
            end
            else
                gemv_activation_window = '0;
        end else if (linear_engine_command_id == CMD_O_PROJ && attention_activation_buffer_valid_q) begin
            if (int'(linear_activation_window_index) < ATTENTION_ACTIVATION_WINDOWS)
                gemv_activation_window =
                    attention_activation_memory[linear_activation_window_index];
            else
                gemv_activation_window = '0;
        end else if (MODEL_ID == MODEL_HUGINN && linear_engine_command_id == CMD_DOWN &&
                     ffn_activation_valid) begin
            gemv_activation_window = ffn_activation_window;
        end else if (activation_buffer_valid_q) begin
            if (int'(linear_activation_window_index) < NORMALIZED_ACTIVATION_WINDOWS)
                gemv_activation_window =
                    normalized_activation_memory[linear_activation_window_index];
            else
                gemv_activation_window = '0;
        end
        adapter_result_sink = MODEL_ID == MODEL_HUGINN &&
            linear_engine_command_id == CMD_ADAPTER;
        linear_result_internal_sink = MODEL_ID == MODEL_HUGINN &&
            (linear_engine_command_id == CMD_O_PROJ ||
             linear_engine_command_id == CMD_DOWN ||
             linear_engine_command_id == CMD_GATE_PROJ ||
             linear_engine_command_id == CMD_UP_PROJ);
        linear_result_targets_qkv = linear_engine_command_id == 5'd3 ||
                                    linear_engine_command_id == 5'd18 ||
                                    linear_engine_command_id == 5'd19 ||
                                    linear_engine_command_id == 5'd20;
        linear_result_ready_to_engine = (adapter_result_sink ||
            (linear_result_targets_qkv ? qkv_buffer_ready :
             (linear_result_internal_sink ? ffn_pipeline_write_ready : linear_result_ready))) &&
            (!norm_preload_gamma_request || norm_preload_gamma_valid);
        norm_unit_out_ready = norm_out_ready || norm_busy;
    end

    always_ff @(posedge clk) begin
        if (!rst_n || weight_abort) begin
            fused_sum_square_q <= '0;
            fused_sum_valid_q <= 1'b0;
        end else begin
            if (fused_residual_write && linear_result_valid && linear_result_ready_to_engine) begin
                if (linear_engine_tile_index == 0 &&
                    linear_result_row_start == linear_engine_tile_row_start)
                    fused_sum_square_q <= fused_tile_sum_square;
                else
                    fused_sum_square_q <= fused_sum_square_q + fused_tile_sum_square;
                if (int'(linear_result_row_start) + int'(linear_result_rows) == HIDDEN_SIZE)
                    fused_sum_valid_q <= 1'b1;
            end
            if (norm_done && fused_norm_input)
                fused_sum_valid_q <= 1'b0;
        end
    end

    always_ff @(posedge clk) begin
        logic [2047:0] next_activation_window;
        if (!rst_n || weight_abort) begin
            recurrent_state_valid_q <= 1'b0;
            adapter_embedding_valid_q <= 1'b0;
            activation_buffer_valid_q <= 1'b0;
            recurrent_activation_scale_fp16_q <= 16'h3c00;
            norm_state_chunk_q <= '0;
            norm_state_request_chunk_q <= '0;
            norm_state_data_valid_q <= 1'b0;
            norm_output_chunk_q <= '0;
            normalized_activation_window_q <= '0;
            core_output_chunk_q <= '0;
            core_output_data_valid_q <= 1'b0;
            core_output_complete_q <= 1'b0;
        end else begin
            if (start) begin
                recurrent_state_valid_q <= 1'b0;
                adapter_embedding_valid_q <= 1'b0;
                core_output_chunk_q <= '0;
                core_output_data_valid_q <= 1'b0;
                core_output_complete_q <= 1'b0;
            end
            if (!adapter_embedding_valid_q && linear_engine_command_id == CMD_ADAPTER &&
                (&activation_valid) && (&activation_ready) &&
                int'(linear_activation_window_index) >= ADAPTER_STATE_FULL_WINDOWS &&
                int'(linear_activation_window_index) < ADAPTER_INPUT_WINDOWS) begin
                adapter_embedding_memory[
                    int'(linear_activation_window_index) - ADAPTER_STATE_FULL_WINDOWS] <= activation_window;
                if (int'(linear_activation_window_index) == ADAPTER_INPUT_WINDOWS - 1)
                    adapter_embedding_valid_q <= 1'b1;
            end
            if (norm_start && norm_ready) begin
                norm_state_chunk_q <= '0;
                norm_state_request_chunk_q <= '0;
                norm_state_data_valid_q <= 1'b0;
                norm_output_chunk_q <= '0;
                activation_buffer_valid_q <= 1'b0;
                normalized_activation_window_q <= '0;
            end
            if (state_read_enable) begin
                if (!core_output_read_enable) begin
                    norm_state_chunk_q <= NORM_COUNT_WIDTH'(norm_state_request_chunk_q);
                    norm_state_request_chunk_q <= norm_state_request_chunk_q + 1'b1;
                    norm_state_data_valid_q <= 1'b1;
                end else begin
                    core_output_data_valid_q <= 1'b1;
                end
            end else if (norm_use_recurrent_state && norm_feed_valid && norm_in_ready) begin
                norm_state_data_valid_q <= 1'b0;
            end
            if (core_output_valid && core_output_ready) begin
                core_output_data_valid_q <= 1'b0;
                if (core_output_last)
                    core_output_complete_q <= 1'b1;
                else
                    core_output_chunk_q <= core_output_chunk_q + 1'b1;
            end
            if (norm_out_valid && norm_unit_out_ready) begin
                next_activation_window = normalized_activation_window_q;
                next_activation_window[(int'(norm_output_chunk_q) % 16) * 128 +: 128] =
                    norm_out_quantized_int8;
                if (scheduler_vector_length == HIDDEN_SIZE) begin
                    normalized_activation_window_q <= next_activation_window;
                    if ((int'(norm_output_chunk_q) % 16) == 15 || norm_out_last) begin
                        normalized_activation_memory[int'(norm_output_chunk_q) / 16] <=
                            next_activation_window;
                        normalized_activation_window_q <= '0;
                    end
                end
                if (norm_out_last) begin
                    norm_output_chunk_q <= '0;
                    if (scheduler_vector_length == HIDDEN_SIZE) begin
                        activation_buffer_valid_q <= 1'b1;
                        recurrent_activation_scale_fp16_q <= q4_12_to_fp16(norm_activation_scale_q4_12);
                    end
                end else begin
                    norm_output_chunk_q <= norm_output_chunk_q + 1'b1;
                end
            end
            if (adapter_result_sink && linear_result_valid && linear_result_ready_to_engine) begin
                if (int'(linear_result_row_start) + int'(linear_result_rows) == HIDDEN_SIZE)
                    recurrent_state_valid_q <= 1'b1;
            end
        end
    end

    always_ff @(posedge clk) begin
        integer address;
        integer context_head;
        integer context_dimension;
        integer context_lane;
        integer current_value;
        integer absolute_value;
        integer next_maximum;
        integer scale_value;
        integer quantized_value;
        if (!rst_n || weight_abort) begin
            attention_activation_buffer_valid_q <= 1'b0;
            attention_activation_scale_fp16_q <= 16'h3c00;
            attention_activation_scale_q4_12_q <= 16'd1;
            attention_quant_state_q <= ATTN_QUANT_IDLE;
            attention_quant_index_q <= '0;
            attention_quant_head_q <= '0;
            attention_quant_dimension_q <= '0;
            attention_max_abs_q4_12_q <= '0;
            attention_quantized_valid_q <= 1'b0;
            attention_quantized_index_q <= '0;
            attention_quantized_value_q <= '0;
            attention_quant_negative_q <= 1'b0;
            attention_activation_window_q <= '0;
        end else begin
            if (bridge_start && bridge_ready) begin
                attention_activation_buffer_valid_q <= 1'b0;
                attention_quant_state_q <= ATTN_QUANT_IDLE;
                attention_quant_index_q <= '0;
                attention_quant_head_q <= '0;
                attention_quant_dimension_q <= '0;
                attention_max_abs_q4_12_q <= '0;
                attention_quantized_valid_q <= 1'b0;
                attention_activation_window_q <= '0;
            end

            if (ATTENTION_PARALLEL_VALID) begin
                for (integer context_port = 0; context_port < ATTENTION_PARALLEL_HEADS; context_port = context_port + 1) begin
                    if (parallel_context_valid[context_port]) begin
                        address = int'(parallel_context_heads[context_port*HEAD_INDEX_WIDTH +: HEAD_INDEX_WIDTH]) *
                                  ATTENTION_OUTPUT_CHUNKS +
                                  int'(parallel_context_chunks[context_port*ATTENTION_OUTPUT_CHUNK_INDEX_WIDTH +:
                                      ATTENTION_OUTPUT_CHUNK_INDEX_WIDTH]);
                        attention_context_chunk_memory_parallel[context_port][address] <=
                            parallel_context_data[context_port*ATTENTION_CHUNK_WIDTH +: ATTENTION_CHUNK_WIDTH];
                    end
                end
            end else if (bridge_context_valid) begin
                address = int'(bridge_context_head) * ATTENTION_OUTPUT_CHUNKS +
                          int'(bridge_context_chunk);
                attention_context_chunk_memory[address] <= bridge_context_data;
            end

            if (ATTENTION_QUANT_STREAM_PIPELINE && attention_stream_output_valid) begin
                attention_activation_window_q <= attention_activation_window_next;
                if (attention_stream_output_index[7:0] == 8'hff ||
                    attention_stream_output_index == QUERY_SIZE - 1)
                    attention_activation_memory[attention_stream_output_index[15:8]] <=
                        attention_activation_window_next;
                if (attention_stream_output_index == QUERY_SIZE - 1) begin
                    attention_activation_scale_fp16_q <=
                        q4_12_to_fp16(attention_activation_scale_q4_12_q);
                    attention_activation_buffer_valid_q <= 1'b1;
                    attention_quant_state_q <= ATTN_QUANT_IDLE;
                    attention_quant_index_q <= '0;
                    attention_quant_head_q <= '0;
                    attention_quant_dimension_q <= '0;
                end
            end

            case (attention_quant_state_q)
                ATTN_QUANT_IDLE: begin
                    if (bridge_done && !bridge_error) begin
                        attention_quant_index_q <= '0;
                        attention_quant_head_q <= '0;
                        attention_quant_dimension_q <= '0;
                        attention_max_abs_q4_12_q <= '0;
                        attention_quantized_valid_q <= 1'b0;
                        attention_quant_state_q <= ATTN_QUANT_SCAN;
                    end
                end
                ATTN_QUANT_SCAN: begin
                    context_head = int'(attention_quant_head_q);
                    context_dimension = int'(attention_quant_dimension_q);
                    context_lane = context_dimension % LANES;
                    address = context_head * ATTENTION_OUTPUT_CHUNKS +
                              context_dimension / LANES;
                    if (ATTENTION_PARALLEL_VALID)
                        current_value = $signed(attention_context_chunk_memory_parallel[context_head % ATTENTION_PARALLEL_HEADS]
                            [address][context_lane*16 +: 16]);
                    else
                        current_value = $signed(attention_context_chunk_memory[address][context_lane*16 +: 16]);
                    absolute_value = current_value < 0 ? -current_value : current_value;
                    next_maximum = int'(attention_max_abs_q4_12_q);
                    if (absolute_value > next_maximum)
                        next_maximum = absolute_value;
                    attention_max_abs_q4_12_q <= 16'(next_maximum);
                    if (attention_quant_dimension_q == HEAD_DIM - 1) begin
                        attention_quant_head_q <= attention_quant_head_q + 1'b1;
                        attention_quant_dimension_q <= '0;
                    end else begin
                        attention_quant_dimension_q <= attention_quant_dimension_q + 1'b1;
                    end
                    if (attention_quant_index_q == QUERY_SIZE - 1) begin
                        scale_value = (next_maximum + 126) / 127;
                        if (scale_value < 1)
                            scale_value = 1;
                        attention_activation_scale_q4_12_q <= 16'(scale_value);
                        attention_quant_index_q <= '0;
                        attention_quant_head_q <= '0;
                        attention_quant_dimension_q <= '0;
                        attention_quant_state_q <= ATTN_QUANTIZE;
                    end else begin
                        attention_quant_index_q <= attention_quant_index_q + 1'b1;
                    end
                end
                ATTN_QUANTIZE: begin
                    if (ATTENTION_QUANT_STREAM_PIPELINE) begin
                        if (attention_quant_index_q == QUERY_SIZE - 1) begin
                            attention_quant_state_q <= ATTN_QUANT_DRAIN;
                        end else begin
                            attention_quant_index_q <= attention_quant_index_q + 1'b1;
                            if (attention_quant_dimension_q == HEAD_DIM - 1) begin
                                attention_quant_head_q <= attention_quant_head_q + 1'b1;
                                attention_quant_dimension_q <= '0;
                            end else begin
                                attention_quant_dimension_q <= attention_quant_dimension_q + 1'b1;
                            end
                        end
                    end else if (attention_divider_ready) begin
                        attention_quant_negative_q <= (attention_quant_input < 0);
                        attention_quant_state_q <= ATTN_QUANT_DIVIDE;
                    end
                end
                ATTN_QUANT_DIVIDE: begin
                    if (!ATTENTION_QUANT_STREAM_PIPELINE && attention_divider_done)
                        attention_quant_state_q <= ATTN_QUANT_STORE;
                end
                ATTN_QUANT_STORE: begin
                    if (!ATTENTION_QUANT_STREAM_PIPELINE) begin
                        quantized_value = int'(attention_divider_quotient);
                        if (attention_quant_negative_q)
                            quantized_value = -quantized_value;
                        if (attention_quant_dimension_q == HEAD_DIM - 1) begin
                            attention_quant_head_q <= attention_quant_head_q + 1'b1;
                            attention_quant_dimension_q <= '0;
                        end else begin
                            attention_quant_dimension_q <= attention_quant_dimension_q + 1'b1;
                        end
                        if (attention_quantized_valid_q) begin
                            for (integer quantized_byte = 0; quantized_byte < 256;
                                 quantized_byte = quantized_byte + 1) begin
                                if (int'(attention_quantized_index_q) == quantized_byte)
                                    attention_activation_window_q[quantized_byte*8 +: 8] <=
                                        attention_quantized_value_q;
                            end
                        end
                        attention_quantized_index_q <= attention_quant_index_q[7:0];
                        attention_quantized_value_q <= 8'(quantized_value);
                        attention_quantized_valid_q <= 1'b1;
                        if (attention_quant_index_q[7:0] == 8'hff ||
                            attention_quant_index_q == QUERY_SIZE - 1) begin
                            attention_quant_state_q <= ATTN_QUANT_DRAIN;
                        end else begin
                            attention_quant_index_q <= attention_quant_index_q + 1'b1;
                            attention_quant_state_q <= ATTN_QUANTIZE;
                        end
                    end
                end
                ATTN_QUANT_DRAIN: begin
                    if (!ATTENTION_QUANT_STREAM_PIPELINE) begin
                        if (attention_quantized_valid_q) begin
                            for (integer quantized_byte = 0; quantized_byte < 256;
                                 quantized_byte = quantized_byte + 1) begin
                                if (int'(attention_quantized_index_q) == quantized_byte)
                                    attention_activation_window_q[quantized_byte*8 +: 8] <=
                                        attention_quantized_value_q;
                            end
                            attention_quantized_valid_q <= 1'b0;
                        end
                        attention_quant_state_q <= ATTN_QUANT_FLUSH;
                    end
                end
                ATTN_QUANT_FLUSH: begin
                    if (!ATTENTION_QUANT_STREAM_PIPELINE) begin
                        attention_activation_memory[attention_quant_index_q[15:8]] <=
                            attention_activation_window_q;
                        attention_activation_window_q <= '0;
                        if (attention_quant_index_q == QUERY_SIZE - 1) begin
                            attention_activation_scale_fp16_q <=
                                q4_12_to_fp16(attention_activation_scale_q4_12_q);
                            attention_activation_buffer_valid_q <= 1'b1;
                            attention_quant_state_q <= ATTN_QUANT_IDLE;
                            attention_quant_index_q <= '0;
                            attention_quant_head_q <= '0;
                            attention_quant_dimension_q <= '0;
                        end else begin
                            attention_quant_index_q <= attention_quant_index_q + 1'b1;
                            attention_quant_state_q <= ATTN_QUANTIZE;
                        end
                    end
                end
                default: attention_quant_state_q <= ATTN_QUANT_IDLE;
            endcase
        end
    end

    rtwsr_recurrent_command_scheduler #(
        .MODEL_ID(MODEL_ID), .RECURRENCES_OVERRIDE(RECURRENCES_OVERRIDE)
    ) u_scheduler (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .context_tokens(context_tokens),
        .command_valid(command_valid),
        .command_ready(scheduler_command_ready),
        .command_done(scheduler_command_done),
        .command_id(scheduler_command_id),
        .command_stage(scheduler_command_stage),
        .block_index(scheduler_block_index),
        .recurrence_index(scheduler_recurrence_index),
        .command_index(scheduler_command_index),
        .matrix_rows(scheduler_matrix_rows),
        .matrix_columns(scheduler_matrix_columns),
        .vector_length(scheduler_vector_length),
        .active_context_tokens(scheduler_active_context_tokens),
        .attention_is_full(scheduler_attention_is_full),
        .done(done),
        .error(scheduler_error)
    );

    assign error = scheduler_error || linear_command_error ||
                   weight_protocol_error || gamma_protocol_error || tile_execution_error ||
                   rope_protocol_error || attention_protocol_error ||
                   norm_protocol_error || swiglu_protocol_error || bridge_error;

    assign bridge_ready = ATTENTION_PARALLEL_VALID ? parallel_bridge_ready : serial_bridge_ready;
    assign bridge_done = ATTENTION_PARALLEL_VALID ? parallel_bridge_done : serial_bridge_done;
    assign bridge_error = ATTENTION_PARALLEL_VALID ? parallel_bridge_error : serial_bridge_error;

    assign bridge_start = command_valid && scheduler_command_id == CMD_ROPE_KV;

    assign command_id = scheduler_command_id;
    assign command_stage = scheduler_command_stage;
    assign block_index = scheduler_block_index;
    assign recurrence_index = scheduler_recurrence_index;
    assign command_index = scheduler_command_index;
    assign matrix_rows = scheduler_matrix_rows;
    assign matrix_columns = scheduler_matrix_columns;
    assign vector_length = scheduler_vector_length;
    assign active_context_tokens = scheduler_active_context_tokens;
    assign attention_is_full = scheduler_attention_is_full;

    generate
        if (MODEL_ID == MODEL_HUGINN) begin : g_huginn_payload_descriptor
            rtwsr_huginn_payload_descriptor u_payload_descriptor (
                .command_id(scheduler_command_id),
                .block_index(scheduler_block_index),
                .recurrence_index(scheduler_recurrence_index),
                .valid(payload_descriptor_raw_valid),
                .adapter_file(payload_descriptor_adapter_file),
                .weight_offset_bytes(payload_weight_offset_bytes),
                .weight_bytes(payload_weight_bytes),
                .weight_words(payload_weight_words),
                .gamma_offset_bytes(payload_gamma_offset_bytes),
                .gamma_bytes(payload_gamma_bytes),
                .gamma_words(payload_gamma_words),
                .matrix_rows(payload_matrix_rows),
                .matrix_columns(payload_matrix_columns)
            );
        end else begin : g_no_huginn_payload_descriptor
            assign payload_descriptor_raw_valid = 1'b0;
            assign payload_descriptor_adapter_file = 1'b0;
            assign payload_weight_offset_bytes = '0;
            assign payload_weight_bytes = '0;
            assign payload_weight_words = '0;
            assign payload_gamma_offset_bytes = '0;
            assign payload_gamma_bytes = '0;
            assign payload_gamma_words = '0;
            assign payload_matrix_rows = '0;
            assign payload_matrix_columns = '0;
        end
    endgenerate
    assign payload_descriptor_valid = command_valid && payload_descriptor_raw_valid;

    rtwsr_linear_command_dispatch u_linear_command_dispatch (
        .command_valid(command_valid),
        .command_id(scheduler_command_id),
        .block_index(scheduler_block_index),
        .recurrence_index(scheduler_recurrence_index),
        .matrix_rows(scheduler_matrix_rows),
        .matrix_columns(scheduler_matrix_columns),
        .linear_engine_ready(linear_command_ready),
        .linear_engine_done(linear_command_done),
        .operator_ready(operator_ready),
        .operator_done(operator_done),
        .linear_engine_valid(dispatch_linear_valid),
        .linear_engine_command_id(dispatch_command_id),
        .linear_engine_block_index(dispatch_block_index),
        .linear_engine_recurrence_index(dispatch_recurrence_index),
        .linear_engine_rows(dispatch_matrix_rows),
        .linear_engine_columns(dispatch_matrix_columns),
        .scheduler_command_ready(dispatch_command_ready),
        .scheduler_command_done(dispatch_command_done)
    );

    rtwsr_linear_tile_controller #(
        .CHANNELS(LINEAR_CHANNELS),
        .TILE_INDEX_WIDTH(9),
        .USW_WINDOW_SIZE(256),
        .WORDS_PER_USW(4),
        .POOL_DEPTH(16384)
    ) u_linear_tiles (
        .clk(clk),
        .rst_n(rst_n),
        .command_valid(dispatch_linear_valid),
        .command_ready(linear_command_ready),
        .command_id(dispatch_command_id),
        .block_index(dispatch_block_index),
        .recurrence_index(dispatch_recurrence_index),
        .matrix_rows(dispatch_matrix_rows),
        .matrix_columns(dispatch_matrix_columns),
        .tile_valid(linear_engine_valid),
        .tile_ready(linear_engine_tile_ready),
        .tile_done(linear_engine_tile_done),
        .tile_command_id(linear_engine_command_id),
        .tile_block_index(linear_engine_block_index),
        .tile_recurrence_index(linear_engine_recurrence_index),
        .tile_matrix_rows(linear_engine_rows),
        .tile_matrix_columns(linear_engine_columns),
        .matrix_window_count(linear_engine_window_count),
        .matrix_pool_words_per_port(linear_engine_pool_words_per_port),
        .tile_pool_base_per_port(linear_engine_tile_pool_base_per_port),
        .tile_index(linear_engine_tile_index),
        .tile_row_start(linear_engine_tile_row_start),
        .tile_active_rows(linear_engine_tile_rows),
        .command_done(linear_command_done),
        .protocol_error(linear_command_error)
    );

    logic pool_read_enable, pool_read_valid, pool_read_error;
    logic [8:0] pool_read_tile_index;
    logic [6:0] pool_read_window_index;
    logic [1:0] pool_read_subword_index;
    logic [(POOL_READ_PARALLEL_SLOTS ? LINEAR_CHANNELS : LINEAR_CHANNELS/4)*512-1:0] pool_read_data;
    logic weights_resident_q;
    logic [4:0] resident_command_q;
    logic [5:0] resident_block_q;
    logic weight_load_start, weight_memory_error, weight_control_error_q;
    logic [15:0] resident_rows_q, resident_columns_q;
    logic tile_activation_ready;
    logic tile_resources_ready;
    logic tile_weight_match;
    logic gamma_read_enable, gamma_read_match, gamma_read_valid;
    logic [LINEAR_CHANNELS*16-1:0] gamma_read_tile_data;
    logic prefetch_accept, prefetch_pending_q, prefetch_loaded_q;
    logic resident_consumed_q, promote_prefetch, activate_weights;
    logic initial_weight_load_start;
    logic [4:0] prefetched_command_q;
    logic [5:0] prefetched_block_q;
    logic [15:0] prefetched_rows_q, prefetched_columns_q;

    // Weight and Gamma descriptors remain stable until this tile is accepted.
    assign weight_load_request_ready = linear_engine_valid &&
        linear_engine_tile_index == 0 && tile_execution_ready && !weight_store_busy &&
        !prefetch_pending_q && (!weights_resident_q || resident_consumed_q);
    assign initial_weight_load_start = weight_start && weight_load_request_ready;
    assign weight_prefetch_ready = weights_resident_q && !prefetch_pending_q &&
        !weight_store_busy && !weight_start && !weight_abort;
    assign prefetch_accept = weight_prefetch_start && weight_prefetch_ready;
    assign weight_load_start = initial_weight_load_start || prefetch_accept;
    assign hbm_weight_load_start = HBM_PARALLEL_LOAD && weight_load_start;
    assign hbm_weight_load_rows = prefetch_accept ? weight_prefetch_rows : linear_engine_rows;
    assign hbm_weight_load_columns = prefetch_accept ?
        weight_prefetch_columns : linear_engine_columns;
    assign hbm_weight_load_command_id = prefetch_accept ?
        weight_prefetch_command_id : linear_engine_command_id;
    assign hbm_weight_load_block_index = prefetch_accept ?
        weight_prefetch_block_index : linear_engine_block_index;
    assign hbm_weight_skip_adapter_static = ADAPTER_STATIC_REUSE && HBM_PARALLEL_LOAD &&
        (prefetch_accept ? weight_prefetch_command_id == CMD_ADAPTER &&
                           (weight_prefetch_recurrence_index != 0 ||
                            weight_prefetch_block_index != 0) :
                           linear_engine_command_id == CMD_ADAPTER &&
                           (linear_engine_recurrence_index != 0 ||
                            linear_engine_block_index != 0));
    assign promote_prefetch = prefetch_pending_q && prefetch_loaded_q &&
        resident_consumed_q && linear_engine_valid && linear_engine_tile_index == 0 &&
        prefetched_command_q == linear_engine_command_id &&
        prefetched_block_q == linear_engine_block_index &&
        prefetched_rows_q == linear_engine_rows && prefetched_columns_q == linear_engine_columns;
    assign activate_weights = (weight_load_done && !prefetch_pending_q &&
        !weight_protocol_error) || promote_prefetch;
    assign weight_protocol_error = weight_memory_error || weight_control_error_q;
    assign tile_weight_match = weights_resident_q &&
        resident_command_q == linear_engine_command_id &&
        resident_block_q == linear_engine_block_index &&
        resident_rows_q == linear_engine_rows &&
        resident_columns_q == linear_engine_columns;
    assign gamma_read_enable = linear_engine_valid && tile_weight_match &&
        !weight_start && !weight_abort;
    assign tile_resources_ready = tile_weight_match && gamma_read_valid &&
        (&round_config_valid) &&
        (linear_engine_command_id != CMD_O_PROJ || attention_activation_buffer_valid_q) &&
        !weight_start && !weight_abort;
    assign linear_engine_tile_ready = tile_execution_ready && tile_resources_ready &&
        !result_serialize_valid_q;
    assign tile_launch = linear_engine_valid && linear_engine_tile_ready;
    assign round_config_ready = {3{linear_engine_valid && tile_execution_ready &&
        weights_resident_q && resident_command_q == linear_engine_command_id &&
        resident_block_q == linear_engine_block_index && resident_rows_q == linear_engine_rows &&
        resident_columns_q == linear_engine_columns && (&round_config_valid) &&
        gamma_read_valid && !weight_start && !weight_abort}};
    assign activation_ready = {3{tile_activation_ready && (&gemv_activation_valid)}};

    always_ff @(posedge clk) begin
        if (!rst_n || weight_abort) begin
            weights_resident_q <= 1'b0;
            resident_rows_q <= '0;
            resident_columns_q <= '0;
            resident_command_q <= '0;
            resident_block_q <= '0;
            weight_control_error_q <= 1'b0;
            prefetch_pending_q <= 1'b0;
            prefetch_loaded_q <= 1'b0;
            resident_consumed_q <= 1'b0;
            prefetched_command_q <= '0;
            prefetched_block_q <= '0;
            prefetched_rows_q <= '0;
            prefetched_columns_q <= '0;
        end else begin
            if ((weight_start && !initial_weight_load_start) ||
                (weight_prefetch_start && !weight_prefetch_ready))
                weight_control_error_q <= 1'b1;
            if (initial_weight_load_start) begin
                weights_resident_q <= 1'b0;
                weight_control_error_q <= 1'b0;
                resident_rows_q <= linear_engine_rows;
                resident_columns_q <= linear_engine_columns;
                resident_command_q <= linear_engine_command_id;
                resident_block_q <= linear_engine_block_index;
            end else if (weight_load_done && !prefetch_pending_q) begin
                weights_resident_q <= !weight_protocol_error;
                resident_consumed_q <= 1'b0;
            end
            if (linear_engine_tile_done &&
                int'(linear_engine_tile_row_start) + int'(linear_engine_tile_rows) ==
                int'(resident_rows_q))
                resident_consumed_q <= 1'b1;
            if (prefetch_accept) begin
                prefetch_pending_q <= 1'b1;
                prefetch_loaded_q <= 1'b0;
                prefetched_command_q <= weight_prefetch_command_id;
                prefetched_block_q <= weight_prefetch_block_index;
                prefetched_rows_q <= weight_prefetch_rows;
                prefetched_columns_q <= weight_prefetch_columns;
            end
            if (weight_load_done && prefetch_pending_q)
                prefetch_loaded_q <= !weight_protocol_error;
            if (promote_prefetch) begin
                resident_command_q <= prefetched_command_q;
                resident_block_q <= prefetched_block_q;
                resident_rows_q <= prefetched_rows_q;
                resident_columns_q <= prefetched_columns_q;
                resident_consumed_q <= 1'b0;
                prefetch_pending_q <= 1'b0;
                prefetch_loaded_q <= 1'b0;
            end
        end
    end

    rtwsr_runtime_weight_subsystem #(
        .CHANNELS(LINEAR_CHANNELS),
        .HBM_LOAD_LANES(HBM_LOAD_LANES),
        .OVERLAP_READ(1'b1), .HBM_PARALLEL_LOAD(HBM_PARALLEL_LOAD),
        .READ_PARALLEL_SLOTS(POOL_READ_PARALLEL_SLOTS)
    ) u_weight_memory (
        .activate_loaded_weights(activate_weights),
        .consumed_tile_valid(linear_engine_tile_done),
        .consumed_tile_index(linear_engine_tile_index),
        .clk(clk), .rst_n(rst_n),
        .load_start(weight_load_start), .load_abort(weight_abort),
        .load_rows(prefetch_accept ? weight_prefetch_rows : linear_engine_rows),
        .load_columns(hbm_weight_skip_adapter_static ? 16'd5280 :
            (prefetch_accept ? weight_prefetch_columns : linear_engine_columns)),
        .weight_stream_valid(weight_stream_valid),
        .weight_stream_ready(weight_stream_ready),
        .weight_stream_data(weight_stream_data), .weight_stream_last(weight_stream_last),
        .parallel_load_valid(hbm_pool_load_valid),
        .parallel_load_ready(hbm_pool_load_ready),
        .parallel_load_enable(hbm_pool_load_enable),
        .parallel_load_address(hbm_pool_load_address),
        .parallel_load_data(hbm_pool_load_data),
        .pool_drain_enable(1'b1), .weight_store_busy(weight_store_busy),
        .weight_load_done(weight_load_done), .weight_protocol_error(weight_memory_error),
        .shadow_occupancy(shadow_occupancy), .pool_window_count(), .pool_words_per_port(),
        .pool_read_enable(pool_read_enable), .pool_read_tile_index(pool_read_tile_index),
        .pool_read_window_index(pool_read_window_index),
        .pool_read_subword_index(pool_read_subword_index),
        .pool_read_valid(pool_read_valid), .pool_read_data(pool_read_data),
        .pool_read_error(pool_read_error)
    );

    rtwsr_runtime_gamma_pool #(
        .CHANNELS(LINEAR_CHANNELS), .PARALLEL_LOAD(GAMMA_PARALLEL_LOAD)
    ) u_gamma_memory (
        .clk(clk), .rst_n(rst_n), .load_abort(weight_abort),
        .load_start(gamma_load_start), .load_start_ready(gamma_load_start_ready),
        .load_command_id(gamma_load_command_id),
        .load_block_index(gamma_load_block_index),
        .load_recurrence_index(gamma_load_recurrence_index),
        .load_matrix_rows(gamma_load_matrix_rows),
        .load_matrix_columns(gamma_load_matrix_columns),
        .load_valid(gamma_load_valid), .load_ready(gamma_load_ready),
        .load_pair_data(gamma_load_pair_data), .load_vector_data(gamma_load_vector_data),
        .load_last(gamma_load_last),
        .load_done(gamma_load_done), .protocol_error(gamma_protocol_error),
        .read_enable(gamma_read_enable),
        .read_command_id(linear_engine_command_id),
        .read_block_index(linear_engine_block_index),
        .read_recurrence_index(linear_engine_recurrence_index),
        .read_matrix_rows(linear_engine_rows),
        .read_matrix_columns(linear_engine_columns),
        .read_tile_index(linear_engine_tile_index),
        .release_enable(linear_engine_tile_done),
        .release_tile_index(linear_engine_tile_index),
        .read_match(gamma_read_match), .read_valid(gamma_read_valid),
        .read_tile_data(gamma_read_tile_data)
    );

    rtwsr_runtime_tile_gemv #(
        .CHANNELS(LINEAR_CHANNELS), .ROW_COUNT_WIDTH(LINEAR_ROW_COUNT_WIDTH),
        .ADAPTER_STATIC_REUSE(ADAPTER_STATIC_REUSE),
        .TRITS_PER_CYCLE(CORE_128TRIT_CANDIDATE ? 128 : 64),
        .READ_PARALLEL_SLOTS(POOL_READ_PARALLEL_SLOTS)
    ) u_linear_engine (
        .clk(clk), .rst_n(rst_n && !weight_abort),
        .tile_valid(tile_launch), .tile_ready(tile_execution_ready),
        .tile_index(linear_engine_tile_index), .tile_rows(linear_engine_tile_rows),
        .matrix_columns(linear_engine_columns), .tile_gamma_fp16(gamma_read_tile_data),
        .activation_scale_fp16(gemv_activation_scale_fp16),
        .adapter_reuse(MODEL_ID == MODEL_HUGINN && linear_engine_command_id == CMD_ADAPTER),
        .adapter_cache_invalidate(start || weight_abort),
        .activation_ready(tile_activation_ready), .activation_valid(&gemv_activation_valid),
        .activation_window(gemv_activation_window),
        .activation_window_index(linear_activation_window_index),
        .pool_read_enable(pool_read_enable), .pool_read_tile_index(pool_read_tile_index),
        .pool_read_window_index(pool_read_window_index),
        .pool_read_subword_index(pool_read_subword_index),
        .pool_read_valid(pool_read_valid), .pool_read_data(pool_read_data),
        .result_valid(gemv_result_valid), .result_ready(gemv_result_ready),
        .result_q12(gemv_result_q12), .result_rows(gemv_result_rows),
        .tile_done(gemv_tile_done), .protocol_error(tile_execution_error)
    );

    assign linear_engine_tile_done = gemv_tile_done;

    generate
        if (LINEAR_CHANNELS == 96) begin : g_direct_linear_result
            assign gemv_result_ready = linear_result_ready_to_engine;
            assign linear_result_valid = gemv_result_valid;
            assign linear_result_q12 = gemv_result_q12[3071:0];
            assign linear_result_rows = gemv_result_rows[6:0];
            assign linear_result_row_start = linear_engine_tile_row_start;
            assign result_serialize_valid_q = 1'b0;
            assign result_serialize_data_q = '0;
            assign result_serialize_rows_q = '0;
            assign result_serialize_row_start_q = '0;
            assign result_serialize_offset_q = '0;
        end else begin : g_serialized_linear_result
            logic [LINEAR_ROW_COUNT_WIDTH-1:0] remaining_rows;
            assign gemv_result_ready = !result_serialize_valid_q;
            assign linear_result_valid = result_serialize_valid_q;
            assign linear_result_q12 = result_serialize_data_q[
                int'(result_serialize_offset_q)*32 +: 3072];
            assign remaining_rows = result_serialize_rows_q -
                                    LINEAR_ROW_COUNT_WIDTH'(result_serialize_offset_q);
            assign linear_result_rows = remaining_rows > 96 ? 7'd96 : 7'(remaining_rows);
            assign linear_result_row_start = result_serialize_row_start_q +
                                             16'(result_serialize_offset_q);

            always_ff @(posedge clk) begin
                if (!rst_n || weight_abort) begin
                    result_serialize_valid_q <= 1'b0;
                    result_serialize_data_q <= '0;
                    result_serialize_rows_q <= '0;
                    result_serialize_row_start_q <= '0;
                    result_serialize_offset_q <= '0;
                end else begin
                    if (gemv_result_valid && gemv_result_ready) begin
                        result_serialize_valid_q <= 1'b1;
                        result_serialize_data_q <= gemv_result_q12;
                        result_serialize_rows_q <= gemv_result_rows;
                        result_serialize_row_start_q <= linear_engine_tile_row_start;
                        result_serialize_offset_q <= '0;
                    end else if (linear_result_valid && linear_result_ready_to_engine) begin
                        if (int'(result_serialize_offset_q) + 96 >=
                            int'(result_serialize_rows_q)) begin
                            result_serialize_valid_q <= 1'b0;
                            result_serialize_offset_q <= '0;
                        end else begin
                            result_serialize_offset_q <= result_serialize_offset_q + 8'd96;
                        end
                    end
                end
            end
        end
    endgenerate

    rtwsr_qkv_head_buffer_banked #(
        .QUERY_SIZE(QUERY_SIZE), .KV_SIZE(KV_SIZE), .HEAD_DIM(HEAD_DIM),
        .PARALLEL_READ_PORTS(ATTENTION_PARALLEL_HEADS)
    ) u_qkv_head_buffer (
        .clk(clk), .rst_n(rst_n && !weight_abort),
        .write_valid(linear_result_valid && linear_result_ready_to_engine),
        .write_ready(qkv_buffer_ready),
        .write_command_id(scheduler_command_id),
        .write_row_start(linear_result_row_start),
        .write_rows(linear_result_rows),
        .write_result_q12(linear_result_q12),
        .qkv_valid(qkv_buffer_valid),
        .read_start(bridge_qkv_read_start),
        .read_head_index(bridge_qkv_read_head),
        .read_chunk_index(bridge_qkv_read_chunk),
        .read_ready(qkv_read_ready),
        .read_valid(qkv_read_valid), .read_done(bridge_qkv_read_done),
        .query_chunk_q4_12(qkv_query_chunk),
        .key_chunk_q4_12(qkv_key_chunk),
        .value_chunk_q4_12(qkv_value_chunk),
        .parallel_read_start(ATTENTION_PARALLEL_VALID ? qkv_parallel_read_start : 1'b0),
        .parallel_read_heads(qkv_parallel_read_heads),
        .parallel_read_chunks(qkv_parallel_read_chunks),
        .parallel_read_ready(qkv_parallel_read_ready),
        .parallel_read_valid(qkv_parallel_read_valid),
        .parallel_read_done(ATTENTION_PARALLEL_VALID ? qkv_parallel_read_done : 1'b0),
        .parallel_query_chunks_q4_12(qkv_parallel_query_chunks),
        .parallel_key_chunks_q4_12(qkv_parallel_key_chunks),
        .parallel_value_chunks_q4_12(qkv_parallel_value_chunks)
    );

    generate
        if (!ATTENTION_PARALLEL_VALID) begin : g_serial_attention
            assign rope_cache_read_request_parallel = '0;
            assign rope_cache_read_head_parallel = '0;
            assign rope_cache_read_index_parallel = '0;
            assign rope_cache_load_ready_parallel = '0;
            assign rope_cache_read_head =
                bridge_qkv_read_head / (QUERY_HEADS / (KV_SIZE / HEAD_DIM));

            rtwsr_recurrent_attention_bridge #(
                .QUERY_SIZE(QUERY_SIZE), .KV_SIZE(KV_SIZE), .HEAD_DIM(HEAD_DIM), .LANES(LANES)
            ) u_recurrent_attention_bridge (
                .clk(clk), .rst_n(rst_n && !weight_abort),
                .start(bridge_start), .ready(serial_bridge_ready), .done(serial_bridge_done),
                .protocol_error(serial_bridge_error), .qkv_valid(qkv_buffer_valid),
                .qkv_read_start(bridge_qkv_read_start), .qkv_read_head(bridge_qkv_read_head),
                .qkv_read_chunk(bridge_qkv_read_chunk), .qkv_read_ready(qkv_read_ready),
                .qkv_read_valid(qkv_read_valid), .qkv_read_done(bridge_qkv_read_done),
                .qkv_query_chunk(qkv_query_chunk), .qkv_key_chunk(qkv_key_chunk),
                .qkv_value_chunk(qkv_value_chunk), .rope_start(bridge_rope_start),
                .rope_ready(rope_ready), .rope_query(bridge_rope_query), .rope_key(bridge_rope_key),
                .rope_value(bridge_rope_value), .rope_query_valid(rope_query_valid),
                .rope_query_rotated(rope_query_rotated_q4_12[ROPE_VECTOR_WIDTH-1:0]),
                .rope_done(rope_done), .rope_error(rope_protocol_error),
                .rope_kv_valid(rope_kv_valid), .rope_kv_ready(bridge_rope_kv_ready),
                .rope_kv_key(rope_kv_key_chunk_q4_12), .rope_kv_value(rope_kv_value_chunk_q4_12),
                .attention_start(bridge_attention_start), .attention_ready(attention_ready),
                .attention_query(bridge_attention_query), .attention_kv_ready(attention_kv_ready),
                .attention_kv_valid(bridge_attention_kv_valid), .attention_kv_key(bridge_attention_kv_key),
                .attention_kv_value(bridge_attention_kv_value), .attention_done(attention_done),
                .attention_error(attention_protocol_error), .attention_out_valid(attention_out_valid),
                .attention_out_ready(bridge_attention_out_ready), .attention_out(attention_out_chunk_q4_12),
                .context_valid(bridge_context_valid), .context_head(bridge_context_head),
                .context_chunk(bridge_context_chunk), .context_last(bridge_context_last),
                .context_data(bridge_context_data)
            );

            rtwsr_rope_kv_cache #(
                .HEAD_DIM(HEAD_DIM), .MAX_CONTEXT(MAX_CONTEXT), .LANES(LANES), .EXTERNAL_CACHE(1'b1)
            ) u_rope_kv_cache (
                .clk(clk), .rst_n(rst_n), .start(bridge_rope_start),
                .write_position(rope_write_position),
                .active_context_tokens(scheduler_active_context_tokens[11:0]),
                .window_start(rope_window_start), .query_q4_12(bridge_rope_query),
                .key_q4_12(bridge_rope_key), .value_q4_12(bridge_rope_value),
                .rope_sin_q1_15(rope_sin_q1_15[ROPE_TRIG_WIDTH-1:0]),
                .rope_cos_q1_15(rope_cos_q1_15[ROPE_TRIG_WIDTH-1:0]),
                .ready(rope_ready), .query_valid(rope_query_valid),
                .query_rotated_q4_12(rope_query_rotated_q4_12[ROPE_VECTOR_WIDTH-1:0]),
                .kv_ready(bridge_rope_kv_ready), .kv_valid(rope_kv_valid),
                .kv_token_index(rope_kv_token_index),
                .kv_chunk_index(rope_kv_chunk_index[ROPE_CHUNK_INDEX_WIDTH-1:0]),
                .kv_key_chunk_q4_12(rope_kv_key_chunk_q4_12),
                .kv_value_chunk_q4_12(rope_kv_value_chunk_q4_12), .kv_last(rope_kv_last),
                .cache_load_ready(rope_cache_load_ready), .cache_load_valid(rope_cache_load_valid),
                .cache_load_index(rope_cache_load_index),
                .cache_load_key_q4_12(rope_cache_load_key_q4_12[ROPE_VECTOR_WIDTH-1:0]),
                .cache_load_value_q4_12(rope_cache_load_value_q4_12[ROPE_VECTOR_WIDTH-1:0]),
                .cache_read_request(rope_cache_read_request),
                .cache_read_request_ready(rope_cache_read_request_ready),
                .cache_read_index(rope_cache_read_index), .busy(rope_busy),
                .done(rope_done), .protocol_error(rope_protocol_error)
            );

            rtwsr_attention_gemv_unit #(
                .HEAD_DIM(HEAD_DIM), .LANES(LANES), .MAX_CONTEXT(MAX_CONTEXT),
                .QUERY_WIDTH(ATTENTION_QUERY_WIDTH), .CHUNK_WIDTH(ATTENTION_CHUNK_WIDTH),
                .FAST_RECIPROCAL(CORE_TIMING_CANDIDATE)
            ) u_attention (
                .clk(clk), .rst_n(rst_n), .start(bridge_attention_start),
                .active_context_tokens(scheduler_active_context_tokens[ATTENTION_CONTEXT_WIDTH-1:0]),
                .query_vector_q4_12(bridge_attention_query), .ready(attention_ready),
                .kv_valid(bridge_attention_kv_valid), .kv_ready(attention_kv_ready),
                .kv_key_chunk_q4_12(bridge_attention_kv_key),
                .kv_value_chunk_q4_12(bridge_attention_kv_value),
                .out_valid(attention_out_valid), .out_ready(bridge_attention_out_ready),
                .out_chunk_q4_12(attention_out_chunk_q4_12), .out_last(attention_out_last),
                .busy(attention_busy), .done(attention_done),
                .protocol_error(attention_protocol_error)
            );
        end else begin : g_parallel4_attention
            rtwsr_recurrent_attention_bridge4 #(
                .PARALLEL_HEADS(ATTENTION_PARALLEL_HEADS),
                .QUERY_HEADS(QUERY_HEADS), .HEAD_DIM(HEAD_DIM), .LANES(LANES),
                .READ_WIDTH(96*16), .CHUNK_WIDTH(ATTENTION_CHUNK_WIDTH),
                .HEAD_INDEX_W(HEAD_INDEX_WIDTH), .READ_CHUNK_INDEX_W(QKV_READ_CHUNK_INDEX_WIDTH),
                .ATTENTION_CHUNK_INDEX_W(ATTENTION_OUTPUT_CHUNK_INDEX_WIDTH)
            ) u_bridge4 (
                .clk(clk), .rst_n(rst_n && !weight_abort), .start(bridge_start),
                .ready(parallel_bridge_ready), .done(parallel_bridge_done),
                .protocol_error(parallel_bridge_error), .qkv_valid(qkv_buffer_valid),
                .qkv_read_start(qkv_parallel_read_start), .qkv_read_heads(qkv_parallel_read_heads),
                .qkv_read_chunks(qkv_parallel_read_chunks), .qkv_read_ready(qkv_parallel_read_ready),
                .qkv_read_valid(qkv_parallel_read_valid), .qkv_read_done(qkv_parallel_read_done),
                .qkv_read_mask(qkv_parallel_read_mask), .qkv_query_chunks(qkv_parallel_query_chunks),
                .qkv_key_chunks(qkv_parallel_key_chunks), .qkv_value_chunks(qkv_parallel_value_chunks),
                .rope_start(parallel_rope_start), .rope_ready(parallel_rope_ready),
                .rope_queries(parallel_rope_queries), .rope_keys(parallel_rope_keys),
                .rope_values(parallel_rope_values), .rope_query_valid(parallel_rope_query_valid),
                .rope_queries_rotated(parallel_rope_queries_rotated), .rope_done(parallel_rope_done),
                .rope_error(parallel_rope_error), .rope_kv_valid(parallel_rope_kv_valid),
                .rope_kv_ready(parallel_rope_kv_ready), .rope_kv_keys(parallel_rope_kv_keys),
                .rope_kv_values(parallel_rope_kv_values), .attention_start(parallel_attention_start),
                .attention_ready(parallel_attention_ready), .attention_queries(parallel_attention_queries),
                .attention_kv_ready(parallel_attention_kv_ready),
                .attention_kv_valid(parallel_attention_kv_valid),
                .attention_kv_keys(parallel_attention_kv_keys),
                .attention_kv_values(parallel_attention_kv_values),
                .attention_done(parallel_attention_done), .attention_error(parallel_attention_error),
                .attention_out_valid(parallel_attention_out_valid),
                .attention_out_ready(parallel_attention_out_ready), .attention_out(parallel_attention_out),
                .context_valid(parallel_context_valid), .context_heads(parallel_context_heads),
                .context_chunks(parallel_context_chunks), .context_data(parallel_context_data)
            );

            for (genvar parallel_head = 0; parallel_head < ATTENTION_PARALLEL_HEADS; parallel_head = parallel_head + 1) begin : g_parallel_lane
                rtwsr_rope_kv_cache #(
                    .HEAD_DIM(HEAD_DIM), .MAX_CONTEXT(MAX_CONTEXT), .LANES(LANES), .EXTERNAL_CACHE(1'b1)
                ) u_rope_kv_cache (
                    .clk(clk), .rst_n(rst_n), .start(parallel_rope_start[parallel_head]),
                    .write_position(rope_write_position),
                    .active_context_tokens(scheduler_active_context_tokens[11:0]),
                    .window_start(rope_window_start),
                    .query_q4_12(parallel_rope_queries[parallel_head*ROPE_VECTOR_WIDTH +: ROPE_VECTOR_WIDTH]),
                    .key_q4_12(parallel_rope_keys[parallel_head*ROPE_VECTOR_WIDTH +: ROPE_VECTOR_WIDTH]),
                    .value_q4_12(parallel_rope_values[parallel_head*ROPE_VECTOR_WIDTH +: ROPE_VECTOR_WIDTH]),
                    .rope_sin_q1_15(rope_sin_q1_15[ROPE_TRIG_WIDTH-1:0]),
                    .rope_cos_q1_15(rope_cos_q1_15[ROPE_TRIG_WIDTH-1:0]),
                    .ready(parallel_rope_ready[parallel_head]),
                    .query_valid(parallel_rope_query_valid[parallel_head]),
                    .query_rotated_q4_12(parallel_rope_queries_rotated[parallel_head*ROPE_VECTOR_WIDTH +: ROPE_VECTOR_WIDTH]),
                    .kv_ready(parallel_rope_kv_ready[parallel_head]),
                    .kv_valid(parallel_rope_kv_valid[parallel_head]),
                    .kv_token_index(), .kv_chunk_index(),
                    .kv_key_chunk_q4_12(parallel_rope_kv_keys[parallel_head*ATTENTION_CHUNK_WIDTH +: ATTENTION_CHUNK_WIDTH]),
                    .kv_value_chunk_q4_12(parallel_rope_kv_values[parallel_head*ATTENTION_CHUNK_WIDTH +: ATTENTION_CHUNK_WIDTH]),
                    .kv_last(), .cache_load_ready(parallel_cache_load_ready[parallel_head]),
                    .cache_load_valid(rope_cache_load_valid_parallel[parallel_head]),
                    .cache_load_index(rope_cache_load_index_parallel[parallel_head*11 +: 11]),
                    .cache_load_key_q4_12(rope_cache_load_key_q4_12_parallel[
                        parallel_head*4096 +: ROPE_VECTOR_WIDTH]),
                    .cache_load_value_q4_12(rope_cache_load_value_q4_12_parallel[
                        parallel_head*4096 +: ROPE_VECTOR_WIDTH]),
                    .cache_read_request(parallel_cache_read_request[parallel_head]),
                    .cache_read_request_ready(rope_cache_read_request_ready_parallel[parallel_head]),
                    .cache_read_index(parallel_cache_read_indices[parallel_head*11 +: 11]),
                    .busy(), .done(parallel_rope_done[parallel_head]),
                    .protocol_error(parallel_rope_error[parallel_head])
                );

                rtwsr_attention_gemv_unit #(
                    .HEAD_DIM(HEAD_DIM), .LANES(LANES), .MAX_CONTEXT(MAX_CONTEXT),
                    .QUERY_WIDTH(ATTENTION_QUERY_WIDTH), .CHUNK_WIDTH(ATTENTION_CHUNK_WIDTH),
                    .FAST_RECIPROCAL(CORE_TIMING_CANDIDATE)
                ) u_attention (
                    .clk(clk), .rst_n(rst_n), .start(parallel_attention_start[parallel_head]),
                    .active_context_tokens(scheduler_active_context_tokens[ATTENTION_CONTEXT_WIDTH-1:0]),
                    .query_vector_q4_12(parallel_attention_queries[parallel_head*ROPE_VECTOR_WIDTH +: ROPE_VECTOR_WIDTH]),
                    .ready(parallel_attention_ready_by_head[parallel_head]),
                    .kv_valid(parallel_attention_kv_valid[parallel_head]),
                    .kv_ready(parallel_attention_kv_ready[parallel_head]),
                    .kv_key_chunk_q4_12(parallel_attention_kv_keys[parallel_head*ATTENTION_CHUNK_WIDTH +: ATTENTION_CHUNK_WIDTH]),
                    .kv_value_chunk_q4_12(parallel_attention_kv_values[parallel_head*ATTENTION_CHUNK_WIDTH +: ATTENTION_CHUNK_WIDTH]),
                    .out_valid(parallel_attention_out_valid[parallel_head]),
                    .out_ready(parallel_attention_out_ready[parallel_head]),
                    .out_chunk_q4_12(parallel_attention_out[parallel_head*ATTENTION_CHUNK_WIDTH +: ATTENTION_CHUNK_WIDTH]),
                    .out_last(), .busy(), .done(parallel_attention_done[parallel_head]),
                    .protocol_error(parallel_attention_error[parallel_head])
                );
            end

            assign parallel_cache_read_heads = qkv_parallel_read_heads;
            assign parallel_attention_ready = &parallel_attention_ready_by_head;
            assign rope_cache_read_request_parallel = parallel_cache_read_request;
            assign rope_cache_read_head_parallel = parallel_cache_read_heads;
            assign rope_cache_read_index_parallel = parallel_cache_read_indices;
            assign rope_cache_load_ready_parallel = parallel_cache_load_ready;
            assign rope_cache_read_request = 1'b0;
            assign rope_cache_read_head = '0;
            assign rope_cache_read_index = '0;
            assign rope_cache_load_ready = 1'b0;
            assign bridge_rope_start = parallel_rope_start[0];
            assign bridge_rope_kv_ready = parallel_rope_kv_ready[0];
            assign bridge_attention_start = parallel_attention_start[0];
            assign bridge_attention_kv_valid = parallel_attention_kv_valid[0];
            assign bridge_attention_out_ready = parallel_attention_out_ready[0];
            assign bridge_context_valid = 1'b0;
            assign bridge_context_head = '0;
            assign bridge_context_chunk = '0;
            assign bridge_context_last = 1'b0;
            assign bridge_context_data = '0;
            assign rope_ready = &parallel_rope_ready;
            assign rope_query_valid = &parallel_rope_query_valid;
            assign rope_query_rotated_q4_12 = {{(4096-ROPE_VECTOR_WIDTH){1'b0}},
                parallel_rope_queries_rotated[0 +: ROPE_VECTOR_WIDTH]};
            assign rope_done = &parallel_rope_done;
            assign rope_protocol_error = |parallel_rope_error;
            assign rope_kv_valid = parallel_rope_kv_valid[0];
            assign rope_kv_token_index = '0;
            assign rope_kv_chunk_index = '0;
            assign rope_kv_key_chunk_q4_12 = parallel_rope_kv_keys[0 +: ATTENTION_CHUNK_WIDTH];
            assign rope_kv_value_chunk_q4_12 = parallel_rope_kv_values[0 +: ATTENTION_CHUNK_WIDTH];
            assign rope_kv_last = 1'b0;
            assign attention_ready = parallel_attention_ready;
            assign attention_kv_ready = parallel_attention_kv_ready[0];
            assign attention_out_valid = parallel_attention_out_valid[0];
            assign attention_out_chunk_q4_12 = parallel_attention_out[0 +: ATTENTION_CHUNK_WIDTH];
            assign attention_out_last = 1'b0;
            assign attention_busy = !parallel_attention_ready && !parallel_bridge_done;
            assign attention_done = &parallel_attention_done;
            assign attention_protocol_error = |parallel_attention_error;
        end
    endgenerate

    rtwsr_rmsnorm_quant_unit #(
        .VECTOR_LEN(HIDDEN_SIZE),
        .MAX_VECTOR_LEN(NORM_MAX_VECTOR_LEN),
        .LANES(16),
        .PRELOAD_TILED_INPUT(RESIDUAL_NORM_TILE_PRELOAD),
        .PARALLEL_QUANTIZE(CORE_TIMING_CANDIDATE)
    ) u_rmsnorm_quant (
        .clk(clk),
        .rst_n(rst_n),
        .start(norm_start),
        .vector_length(scheduler_vector_length),
        .precomputed_sum_valid(fused_norm_input),
        .precomputed_sum_square(fused_sum_square_q),
        .preloaded_input_valid(fused_norm_preload),
        .preload_write(norm_preload_gamma_request && linear_result_ready_to_engine),
        .preload_tile_index(9'(int'(linear_result_row_start) / 96)),
        .preload_activation_q4_12(fused_residual_data),
        .preload_gamma_q4_12(norm_preload_gamma_q4_12),
        .ready(norm_ready),
        .in_valid(norm_feed_valid),
        .in_ready(norm_in_ready),
        .in_activation_q4_12(norm_feed_activation),
        .in_gamma_q4_12(norm_in_gamma_q4_12),
        .in_last(norm_feed_last),
        .out_valid(norm_out_valid),
        .out_ready(norm_unit_out_ready),
        .out_normalized_q4_12(norm_out_normalized_q4_12),
        .out_quantized_int8(norm_out_quantized_int8),
        .out_last(norm_out_last),
        .inv_rms_q15(norm_inv_rms_q15),
        .activation_scale_q4_12(norm_activation_scale_q4_12),
        .busy(norm_busy),
        .done(norm_done),
        .protocol_error(norm_protocol_error)
    );

    generate
        if (MODEL_ID == MODEL_HUGINN) begin : g_huginn_ffn_pipeline
            rtwsr_huginn_ffn_pipeline #(
                .STREAM_FUSED(CORE_TIMING_CANDIDATE),
                .GEMV_STREAM_FUSED(CORE_TIMING_CANDIDATE)
            ) u_ffn_pipeline (
                .clk(clk),
                .rst_n(rst_n && !weight_abort),
                .start(swiglu_start),
                .ready(swiglu_ready),
                .done(swiglu_done),
                .busy(swiglu_busy),
                .write_valid(linear_result_valid && linear_result_ready_to_engine),
                .write_command_id(linear_engine_command_id),
                .write_row_start(linear_result_row_start),
                .write_rows(linear_result_rows),
                .write_result_q12(linear_result_q12),
                .write_ready(ffn_pipeline_write_ready),
                .in_ready(swiglu_in_ready),
                .out_valid(swiglu_out_valid),
                .out_last(swiglu_out_last),
                .output_q4_12(swiglu_output_q4_12),
                .protocol_error(swiglu_protocol_error),
                .activation_valid(ffn_activation_valid),
                .activation_window_index(linear_activation_window_index),
                .activation_window(ffn_activation_window),
                .activation_scale_fp16(ffn_activation_scale_fp16)
            );
        end else begin : g_external_ffn_pipeline
            assign ffn_pipeline_write_ready = 1'b1;
            assign ffn_activation_valid = 1'b0;
            assign ffn_activation_window = '0;
            assign ffn_activation_scale_fp16 = 16'h3c00;
            rtwsr_swiglu_residual_unit #(
                .VECTOR_LEN(INTERMEDIATE_SIZE),
                .STREAM_FUSED(CORE_TIMING_CANDIDATE)
            ) u_swiglu_residual (
                .clk(clk),
                .rst_n(rst_n),
                .start(swiglu_start),
                .in_valid(swiglu_in_valid),
                .in_ready(swiglu_in_ready),
                .gate_q4_12(swiglu_gate_q4_12),
                .up_q4_12(swiglu_up_q4_12),
                .residual_q4_12(swiglu_residual_q4_12),
                .in_last(swiglu_in_last),
                .residual_rate_q15(swiglu_residual_rate_q15),
                .ready(swiglu_ready),
                .out_valid(swiglu_out_valid),
                .out_ready(swiglu_out_ready),
                .output_q4_12(swiglu_output_q4_12),
                .out_last(swiglu_out_last),
                .busy(swiglu_busy),
                .done(swiglu_done),
                .protocol_error(swiglu_protocol_error)
            );
        end
    endgenerate

    always_comb begin
        scheduler_command_ready = dispatch_command_ready;
        scheduler_command_done = dispatch_command_done;
        norm_start = 1'b0;
        swiglu_start = 1'b0;

        case (scheduler_command_id)
            CMD_ROPE_KV: begin
                scheduler_command_ready = bridge_ready;
                scheduler_command_done = bridge_done;
            end
            CMD_SCORE_SOFTMAX: begin
                scheduler_command_ready = attention_activation_buffer_valid_q;
                scheduler_command_done = attention_activation_buffer_valid_q;
            end
            CMD_CONTEXT: begin
                // Score, online softmax, and PV share one streaming attention pass.
                scheduler_command_ready = 1'b1;
                scheduler_command_done = 1'b1;
            end
            CMD_CONTEXT_GATE_NORM: begin
                scheduler_command_ready = attention_activation_buffer_valid_q;
                scheduler_command_done = attention_activation_buffer_valid_q;
            end
            CMD_PRE_ATTN_NORM, CMD_ATTN_POST, CMD_PRE_FFN_NORM,
            CMD_PRE_DOWN_JUSTNORM, CMD_MLP_POST, CMD_RECURRENCE_POST: begin
                scheduler_command_ready = norm_ready;
                scheduler_command_done = norm_done;
                norm_start = command_valid;
            end
            CMD_UP_PROJ: begin
                if (CORE_TIMING_CANDIDATE)
                    swiglu_start = command_valid;
            end
            CMD_SWIGLU: begin
                if (CORE_TIMING_CANDIDATE)
                    scheduler_command_ready = swiglu_busy || swiglu_done;
                else
                    scheduler_command_ready = swiglu_ready;
                scheduler_command_done = swiglu_done;
                if (!CORE_TIMING_CANDIDATE)
                    swiglu_start = command_valid;
            end
            default: begin
                scheduler_command_ready = dispatch_command_ready;
                scheduler_command_done = dispatch_command_done;
            end
        endcase
    end

    initial begin
        if (MODEL_ID < MODEL_HUGINN || MODEL_ID > MODEL_DORY)
            $error("MODEL_ID must select Huginn, Ouro, or Dory");
        if (LINEAR_CHANNELS != 96 && LINEAR_CHANNELS != 192)
            $error("LINEAR_CHANNELS must be 96 or 192");
        if (LINEAR_CHANNELS == 192 &&
            (MODEL_ID != MODEL_HUGINN || !POOL_READ_PARALLEL_SLOTS))
            $error("192-channel mode requires Huginn and parallel pool reads");
        if (RESIDUAL_NORM_TILE_PRELOAD && !RESIDUAL_NORM_FUSION)
            $error("Norm tile preload requires residual Norm fusion");
    end
endmodule
