`timescale 1ns / 1ps

module rtwsr_plan6_huginn_9p_axi #(
    parameter int S_AXI_DATA_WIDTH = 32,
    parameter int S_AXI_ADDR_WIDTH = 12,
    parameter int LINEAR_CHANNELS = 96,
    parameter int MAX_CONTEXT = 2048,
    parameter int HBM_PCS = 32,
    parameter int HBM_POOL_LANES = 24,
    parameter int HBM_MAX_OUTSTANDING = 16,
    parameter int HBM_RING_RECORDS = 73728,
    parameter logic [36:0] DDR_WEIGHT_BASE = 37'h0800000000,
    parameter logic [36:0] DDR_GAMMA_BASE = 37'h0a00000000,
    parameter logic [36:0] NORM_GAMMA_DDR_BASE = DDR_GAMMA_BASE + 37'h01032000,
    parameter bit HBM_PARALLEL_LOAD = 1'b0,
    parameter bit GAMMA_PARALLEL_LOAD = 1'b0,
    parameter bit CORE_TIMING_CANDIDATE = 1'b0,
    parameter bit CORE_128TRIT_CANDIDATE = 1'b0,
    parameter bit POOL_READ_PARALLEL_SLOTS = 1'b0,
    parameter bit RESIDUAL_NORM_FUSION = 1'b0,
    parameter bit RESIDUAL_NORM_TILE_PRELOAD = 1'b0,
    parameter bit NORM_GAMMA_FROM_HOST = 1'b0,
    parameter bit ATTENTION_PARALLEL_CANDIDATE = 1'b0,
    parameter bit ADAPTER_STATIC_REUSE = 1'b0,
    parameter int ATTENTION_PARALLEL_HEADS = 4,
    parameter bit ATTENTION_QUANT_STREAM_PIPELINE = 1'b0,
    parameter int RECURRENCES_OVERRIDE = 0
)(
    input  logic                         s_axi_aclk,
    input  logic                         s_axi_aresetn,
    input  logic [S_AXI_ADDR_WIDTH-1:0]  s_axi_awaddr,
    input  logic [2:0]                   s_axi_awprot,
    input  logic                         s_axi_awvalid,
    output logic                         s_axi_awready,
    input  logic [S_AXI_DATA_WIDTH-1:0]  s_axi_wdata,
    input  logic [S_AXI_DATA_WIDTH/8-1:0] s_axi_wstrb,
    input  logic                         s_axi_wvalid,
    output logic                         s_axi_wready,
    output logic [1:0]                   s_axi_bresp,
    output logic                         s_axi_bvalid,
    input  logic                         s_axi_bready,
    input  logic [S_AXI_ADDR_WIDTH-1:0]  s_axi_araddr,
    input  logic [2:0]                   s_axi_arprot,
    input  logic                         s_axi_arvalid,
    output logic                         s_axi_arready,
    output logic [S_AXI_DATA_WIDTH-1:0]  s_axi_rdata,
    output logic [1:0]                   s_axi_rresp,
    output logic                         s_axi_rvalid,
    input  logic                         s_axi_rready,
    output logic [36:0]                  m_axi_araddr,
    output logic [4:0]                   m_axi_arid,
    output logic [7:0]                   m_axi_arlen,
    output logic [2:0]                   m_axi_arsize,
    output logic [1:0]                   m_axi_arburst,
    output logic                         m_axi_arvalid,
    input  logic                         m_axi_arready,
    input  logic [4:0]                   m_axi_rid,
    input  logic [511:0]                 m_axi_rdata,
    input  logic [1:0]                   m_axi_rresp,
    input  logic                         m_axi_rlast,
    input  logic                         m_axi_rvalid,
    output logic                         m_axi_rready,
    input  logic                         hbm_axi_clk,
    input  logic                         hbm_axi_rst_n,
    output logic [HBM_PCS*33-1:0]           hbm_m_axi_araddr,
    output logic [HBM_PCS*6-1:0]            hbm_m_axi_arid,
    output logic [HBM_PCS*4-1:0]            hbm_m_axi_arlen,
    output logic [HBM_PCS*3-1:0]            hbm_m_axi_arsize,
    output logic [HBM_PCS*2-1:0]            hbm_m_axi_arburst,
    output logic [HBM_PCS-1:0]              hbm_m_axi_arvalid,
    input  logic [HBM_PCS-1:0]              hbm_m_axi_arready,
    input  logic [HBM_PCS*6-1:0]            hbm_m_axi_rid,
    input  logic [HBM_PCS*256-1:0]          hbm_m_axi_rdata,
    input  logic [HBM_PCS*2-1:0]            hbm_m_axi_rresp,
    input  logic [HBM_PCS-1:0]              hbm_m_axi_rlast,
    input  logic [HBM_PCS-1:0]              hbm_m_axi_rvalid,
    output logic [HBM_PCS-1:0]              hbm_m_axi_rready
);
    localparam logic [36:0] ADAPTER_WEIGHT_BASE = DDR_WEIGHT_BASE;
    localparam logic [36:0] CORE_WEIGHT_BASE = DDR_WEIGHT_BASE + 37'h001000000;
    localparam logic [36:0] CORE_GAMMA_BASE = DDR_GAMMA_BASE + 37'h00100000;
    localparam logic [36:0] ADAPTER_GAMMA_BYTES = 37'd337920;

    typedef enum logic [4:0] {
        IDLE,
        WAIT_COMMAND,
        WAIT_ENGINE,
        DMA_WEIGHT_COMMAND,
        DMA_WEIGHT_STREAM,
        WAIT_WEIGHT_STORE,
        HBM_WAIT_WEIGHT,
        START_GAMMA,
        DMA_GAMMA_COMMAND,
        DMA_GAMMA_STREAM,
        WAIT_GAMMA_STORE,
        RUN_OPERATOR,
        COMPLETE,
        FAILED,
        NORM_GAMMA_COMMAND,
        NORM_GAMMA_STREAM,
        START_CORE
    } state_t;

    typedef enum logic [2:0] {
        PREFETCH_IDLE,
        PREFETCH_START,
        PREFETCH_COMMAND,
        PREFETCH_STREAM,
        PREFETCH_WAIT_STORE,
        PREFETCH_HBM_WAIT,
        PREFETCH_READY
    } prefetch_state_t;

    state_t state_q;
    prefetch_state_t prefetch_state_q;
    logic [S_AXI_ADDR_WIDTH-1:0] awaddr_q, araddr_q;
    logic [S_AXI_DATA_WIDTH-1:0] wdata_q;
    logic [S_AXI_DATA_WIDTH/8-1:0] wstrb_q;
    logic aw_pending, w_pending;
    logic [S_AXI_ADDR_WIDTH-1:0] write_addr;
    logic [S_AXI_DATA_WIDTH-1:0] write_data, read_value, merged_value;
    logic [S_AXI_DATA_WIDTH/8-1:0] write_strb;
    logic [9:0] write_index, read_index;
    logic write_commit;
    logic start_pulse_q;
    logic [15:0] context_tokens_q;
    logic [31:0] status_word;
    logic [63:0] run_cycles_q;
    logic [31:0] nonzero_chunks_q, output_digest_q;
    logic shell_error_q;
    logic software_error_set_q, software_error_clear_q;

    logic core_start, core_done, core_error;
    logic hbm_weight_load_start;
    logic [15:0] hbm_weight_load_rows, hbm_weight_load_columns;
    logic [4:0] hbm_weight_load_command_id;
    logic [5:0] hbm_weight_load_block_index;
    logic hbm_weight_skip_adapter_static;
    logic [HBM_POOL_LANES-1:0] hbm_pool_load_enable;
    logic [HBM_POOL_LANES*14-1:0] hbm_pool_load_address;
    logic [HBM_POOL_LANES*512-1:0] hbm_pool_load_data;
    logic hbm_pool_load_valid, hbm_pool_load_ready;
    logic hbm_path_busy, hbm_path_done, hbm_path_error;
    logic command_valid, payload_descriptor_valid, payload_adapter_file;
    logic [4:0] command_id, recurrence_index, linear_engine_command_id;
    logic [5:0] block_index, linear_engine_block_index;
    logic [4:0] next_weight_command_id, next_weight_recurrence_index;
    logic [5:0] next_weight_block_index;
    logic [31:0] payload_weight_offset, payload_weight_bytes, payload_weight_words;
    logic [31:0] payload_gamma_offset, payload_gamma_bytes, payload_gamma_words;
    logic [15:0] payload_rows, payload_columns;
    logic linear_engine_valid, weight_load_request_ready, weight_start;
    logic weight_prefetch_start, weight_prefetch_ready, saved_prefetch_match_q;
    logic prefetch_target_valid_q, prefetch_done_seen_q;
    logic [4:0] prefetch_command_q, prefetch_recurrence_q;
    logic [5:0] prefetch_block_q;
    logic [15:0] prefetch_rows_q, prefetch_columns_q;
    logic [31:0] prefetch_weight_words_q;
    logic [36:0] prefetch_weight_address_q;
    logic next_payload_valid, next_payload_adapter_file;
    logic [31:0] next_payload_weight_offset, next_payload_weight_bytes;
    logic [31:0] next_payload_weight_words, next_payload_gamma_offset;
    logic [31:0] next_payload_gamma_bytes, next_payload_gamma_words;
    logic [15:0] next_payload_rows, next_payload_columns;
    logic [8:0] linear_engine_tile_index;
    logic weight_stream_valid, weight_stream_ready, weight_stream_last;
    logic [511:0] weight_stream_data;
    logic weight_store_busy, weight_load_done, weight_protocol_error;
    logic gamma_load_start, gamma_load_start_ready;
    logic gamma_load_valid, gamma_load_ready, gamma_load_last;
    logic [31:0] gamma_load_pair_data;
    logic [511:0] gamma_load_vector_data;
    logic gamma_load_done, gamma_protocol_error;
    logic [4:0] saved_command_q, saved_recurrence_q;
    logic [5:0] saved_block_q;
    logic [15:0] saved_rows_q, saved_columns_q;
    logic [31:0] saved_weight_words_q, saved_gamma_words_q;
    logic [36:0] saved_weight_address_q, saved_gamma_address_q;
    logic weight_load_done_seen_q, gamma_load_done_seen_q;
    logic [3:0] gamma_pair_index_q;

    logic dma_command_valid, dma_command_ready;
    logic [36:0] dma_command_address;
    logic [31:0] dma_command_words;
    logic dma_data_valid, dma_data_ready, dma_data_last;
    logic [511:0] dma_data_word;
    logic dma_busy, dma_done, dma_error;

    logic [2047:0] activation_window;
    logic [4095:0] rope_cos;
    logic rope_cache_read_request, rope_cache_read_request_ready;
    logic [5:0] rope_cache_read_head;
    logic [10:0] rope_cache_read_index;
    logic rope_cache_load_valid_q;
    logic [10:0] rope_cache_load_index_q;
    logic [ATTENTION_PARALLEL_HEADS-1:0] rope_cache_read_request_parallel, rope_cache_read_request_ready_parallel;
    logic [ATTENTION_PARALLEL_HEADS*6-1:0] rope_cache_read_head_parallel;
    logic [ATTENTION_PARALLEL_HEADS*11-1:0] rope_cache_read_index_parallel;
    logic [ATTENTION_PARALLEL_HEADS-1:0] rope_cache_load_valid_parallel_q;
    logic [ATTENTION_PARALLEL_HEADS*11-1:0] rope_cache_load_index_parallel_q;
    logic [255:0] core_output_q4_12;
    logic core_output_valid, core_output_ready, core_output_last, core_output_done;
    localparam int NORM_GAMMA_TILES = 4 * 4 * 55;
    localparam int NORM_GAMMA_BYTES = 4 * 4 * 5280 * 2;
    localparam int NORM_GAMMA_DMA_WORDS = NORM_GAMMA_BYTES / 64;
    logic norm_gamma_loaded_q, norm_gamma_load_commit;
    logic norm_gamma_chunk_request, norm_gamma_tile_request, norm_gamma_tile_valid_q;
    logic [8:0] norm_gamma_chunk_index, norm_gamma_tile_index;
    logic [2:0] norm_gamma_chunk_lane;
    logic [4:0] norm_gamma_tile_command;
    logic [10:0] norm_gamma_read_address;
    logic [1535:0] norm_gamma_tile_data;
    logic [255:0] norm_gamma_chunk_data;
    logic [1:0] norm_gamma_load_beat_q;
    logic [10:0] norm_gamma_load_tile_index_q;
    logic [1535:0] norm_gamma_load_tile_q, norm_gamma_load_tile_data;

    function automatic logic [10:0] norm_gamma_address(
        input logic tile_request,
        input logic [4:0] tile_command,
        input logic [4:0] stream_command,
        input logic [5:0] requested_block,
        input logic [8:0] requested_tile,
        input logic [8:0] requested_chunk
    );
        integer norm_index;
        integer tile_index;
        logic [4:0] selected_command;
        begin
            selected_command = tile_request ? tile_command : stream_command;
            case (selected_command)
                5'd2: norm_index = 0;
                5'd10: norm_index = 1;
                5'd11: norm_index = 2;
                5'd16: norm_index = 3;
                default: norm_index = 0;
            endcase
            tile_index = tile_request ? int'(requested_tile) : int'(requested_chunk) / 6;
            return 11'(int'(requested_block) * 220 + norm_index * 55 + tile_index);
        end
    endfunction

    always_comb begin
        norm_gamma_read_address = norm_gamma_address(
            norm_gamma_tile_request, norm_gamma_tile_command, command_id, block_index,
            norm_gamma_tile_index, norm_gamma_chunk_index);
        norm_gamma_chunk_data = norm_gamma_tile_data >> (int'(norm_gamma_chunk_lane) * 256);
        norm_gamma_load_commit = NORM_GAMMA_FROM_HOST &&
            state_q == NORM_GAMMA_STREAM && dma_data_valid && dma_data_ready &&
            norm_gamma_load_beat_q == 2'd2;
        norm_gamma_load_tile_data = norm_gamma_load_tile_q;
        if (norm_gamma_load_beat_q == 0)
            norm_gamma_load_tile_data[511:0] = dma_data_word;
        else if (norm_gamma_load_beat_q == 1)
            norm_gamma_load_tile_data[1023:512] = dma_data_word;
        else
            norm_gamma_load_tile_data[1535:1024] = dma_data_word;
    end

    generate
        if (NORM_GAMMA_FROM_HOST) begin : g_norm_gamma_store
            for (genvar bank = 0; bank < 48; bank++) begin : g_bank
                (* ram_style = "block" *) logic [31:0] memory [0:879];
                logic [31:0] read_data_q;
                always_ff @(posedge s_axi_aclk) begin
                    if (norm_gamma_load_commit)
                        memory[norm_gamma_load_tile_index_q] <= norm_gamma_load_tile_data[bank*32 +: 32];
                    if (norm_gamma_tile_request || norm_gamma_chunk_request)
                        read_data_q <= memory[norm_gamma_read_address];
                end
                assign norm_gamma_tile_data[bank*32 +: 32] = read_data_q;
            end
            always_ff @(posedge s_axi_aclk) begin
                if (!s_axi_aresetn)
                    norm_gamma_tile_valid_q <= 1'b0;
                else
                    norm_gamma_tile_valid_q <= norm_gamma_tile_request;
            end
        end else begin : g_no_norm_gamma_store
            assign norm_gamma_tile_data = '0;
            assign norm_gamma_tile_valid_q = 1'b0;
        end
    endgenerate

    function automatic logic [S_AXI_DATA_WIDTH-1:0] merge_wstrb(
        input logic [S_AXI_DATA_WIDTH-1:0] previous,
        input logic [S_AXI_DATA_WIDTH-1:0] incoming,
        input logic [S_AXI_DATA_WIDTH/8-1:0] strobes
    );
        logic [S_AXI_DATA_WIDTH-1:0] result;
        begin
            result = previous;
            for (integer byte_index = 0; byte_index < S_AXI_DATA_WIDTH/8; byte_index++)
                if (strobes[byte_index])
                    result[byte_index*8 +: 8] = incoming[byte_index*8 +: 8];
            return result;
        end
    endfunction

    always_comb begin
        s_axi_awready = !aw_pending && !s_axi_bvalid;
        s_axi_wready = !w_pending && !s_axi_bvalid;
        s_axi_arready = !s_axi_rvalid;
        write_addr = aw_pending ? awaddr_q : s_axi_awaddr;
        write_data = w_pending ? wdata_q : s_axi_wdata;
        write_strb = w_pending ? wstrb_q : s_axi_wstrb;
        write_commit = !s_axi_bvalid && (aw_pending || (s_axi_awvalid && s_axi_awready)) &&
                       (w_pending || (s_axi_wvalid && s_axi_wready));
        write_index = write_addr[11:2];
        read_index = s_axi_rvalid ? araddr_q[11:2] : s_axi_araddr[11:2];

        status_word = '0;
        status_word[0] = (state_q == COMPLETE);
        status_word[1] = (state_q != IDLE && state_q != COMPLETE && state_q != FAILED);
        status_word[2] = shell_error_q || core_error || dma_error || hbm_path_error ||
                         weight_protocol_error || gamma_protocol_error;
        status_word[3] = core_output_done;
        status_word[4] = dma_busy || hbm_path_busy;
        status_word[5] = weight_store_busy;
        status_word[6] = core_done;
        status_word[7] = core_error;

        read_value = '0;
        case (read_index)
            10'h001: read_value = status_word;
            10'h002: read_value = run_cycles_q[31:0];
            10'h003: read_value = run_cycles_q[63:32];
            10'h004: read_value = nonzero_chunks_q;
            10'h005: read_value = output_digest_q;
            10'h006: read_value = {16'd0, context_tokens_q};
            10'h007: read_value = {27'd0, command_id};
            10'h009: read_value = {31'd0, norm_gamma_loaded_q};
            default: read_value = '0;
        endcase

        core_start = NORM_GAMMA_FROM_HOST ? state_q == START_CORE : start_pulse_q;
        core_output_ready = 1'b1;
        weight_start = (state_q == WAIT_ENGINE) && !saved_prefetch_match_q &&
                       weight_load_request_ready;
        weight_prefetch_start = (prefetch_state_q == PREFETCH_START);
        gamma_load_start = (state_q == START_GAMMA);
        gamma_load_valid = (state_q == DMA_GAMMA_STREAM) && dma_data_valid;
        gamma_load_pair_data = dma_data_word[gamma_pair_index_q*32 +: 32];
        gamma_load_vector_data = dma_data_word;
        gamma_load_last = GAMMA_PARALLEL_LOAD ? dma_data_last :
            (dma_data_last && (gamma_pair_index_q == 4'd15));
        dma_data_ready = 1'b0;
        weight_stream_valid = !HBM_PARALLEL_LOAD &&
            (((state_q == DMA_WEIGHT_STREAM) ||
              (prefetch_state_q == PREFETCH_STREAM)) && dma_data_valid);
        weight_stream_data = dma_data_word;
        weight_stream_last = dma_data_last;
        if (!HBM_PARALLEL_LOAD && ((state_q == DMA_WEIGHT_STREAM) ||
            (prefetch_state_q == PREFETCH_STREAM)))
            dma_data_ready = weight_stream_ready;
        else if (state_q == DMA_GAMMA_STREAM)
            dma_data_ready = GAMMA_PARALLEL_LOAD ? gamma_load_ready :
                ((gamma_pair_index_q == 4'd15) && gamma_load_ready);
        else if (state_q == NORM_GAMMA_STREAM)
            dma_data_ready = 1'b1;

        dma_command_valid = HBM_PARALLEL_LOAD ?
            (state_q == DMA_GAMMA_COMMAND) :
            ((state_q == DMA_WEIGHT_COMMAND) || (state_q == DMA_GAMMA_COMMAND) ||
             (prefetch_state_q == PREFETCH_COMMAND));
        if (NORM_GAMMA_FROM_HOST && state_q == NORM_GAMMA_COMMAND) begin
            dma_command_valid = 1'b1;
            dma_command_address = NORM_GAMMA_DDR_BASE;
            dma_command_words = NORM_GAMMA_DMA_WORDS;
        end else if (state_q == DMA_GAMMA_COMMAND) begin
            dma_command_address = saved_gamma_address_q;
            dma_command_words = saved_gamma_words_q;
        end else if (state_q == DMA_WEIGHT_COMMAND) begin
            dma_command_address = saved_weight_address_q;
            dma_command_words = saved_weight_words_q;
        end else begin
            dma_command_address = prefetch_weight_address_q;
            dma_command_words = prefetch_weight_words_q;
        end

        activation_window = {256{8'h01}};
        rope_cos = {256{16'h7fff}};
        rope_cache_read_request_ready = rope_cache_read_request && !rope_cache_load_valid_q;
        rope_cache_read_request_ready_parallel = rope_cache_read_request_parallel &
                                                  ~rope_cache_load_valid_parallel_q;
    end

    always_comb begin
        next_weight_command_id = '0;
        next_weight_block_index = saved_block_q;
        next_weight_recurrence_index = saved_recurrence_q;
        case (saved_command_q)
            5'd0: next_weight_command_id = 5'd3;
            5'd3: next_weight_command_id = 5'd9;
            5'd9: next_weight_command_id = 5'd21;
            5'd21: next_weight_command_id = 5'd22;
            5'd22: next_weight_command_id = 5'd15;
            5'd15: begin
                if (saved_block_q < 6'd3) begin
                    next_weight_command_id = 5'd3;
                    next_weight_block_index = saved_block_q + 1'b1;
                end else if (saved_recurrence_q < 5'd31) begin
                    next_weight_command_id = 5'd0;
                    next_weight_block_index = '0;
                    next_weight_recurrence_index = saved_recurrence_q + 1'b1;
                end
            end
            default: begin end
        endcase
    end

    rtwsr_huginn_payload_descriptor u_prefetch_descriptor (
        .command_id(next_weight_command_id), .block_index(next_weight_block_index),
        .recurrence_index(next_weight_recurrence_index), .valid(next_payload_valid),
        .adapter_file(next_payload_adapter_file),
        .weight_offset_bytes(next_payload_weight_offset),
        .weight_bytes(next_payload_weight_bytes), .weight_words(next_payload_weight_words),
        .gamma_offset_bytes(next_payload_gamma_offset), .gamma_bytes(next_payload_gamma_bytes),
        .gamma_words(next_payload_gamma_words), .matrix_rows(next_payload_rows),
        .matrix_columns(next_payload_columns)
    );

    rtwsr_weight_dma u_payload_dma (
        .clk(s_axi_aclk), .rst_n(s_axi_aresetn),
        .command_valid(dma_command_valid), .command_ready(dma_command_ready),
        .command_address(dma_command_address), .command_words(dma_command_words),
        .m_axi_arvalid(m_axi_arvalid), .m_axi_arready(m_axi_arready),
        .m_axi_arid(m_axi_arid), .m_axi_araddr(m_axi_araddr),
        .m_axi_arlen(m_axi_arlen), .m_axi_arsize(m_axi_arsize),
        .m_axi_arburst(m_axi_arburst), .m_axi_rvalid(m_axi_rvalid),
        .m_axi_rready(m_axi_rready), .m_axi_rid(m_axi_rid), .m_axi_rdata(m_axi_rdata),
        .m_axi_rresp(m_axi_rresp), .m_axi_rlast(m_axi_rlast),
        .data_valid(dma_data_valid), .data_ready(dma_data_ready),
        .data_word(dma_data_word), .data_last(dma_data_last),
        .busy(dma_busy), .done(dma_done), .error(dma_error)
    );

    rtwsr_transformer_top #(
        .MODEL_ID(0), .LINEAR_CHANNELS(LINEAR_CHANNELS), .MAX_CONTEXT(MAX_CONTEXT),
        .HBM_LOAD_LANES(HBM_POOL_LANES),
        .HBM_PARALLEL_LOAD(HBM_PARALLEL_LOAD),
        .GAMMA_PARALLEL_LOAD(GAMMA_PARALLEL_LOAD),
        .CORE_TIMING_CANDIDATE(CORE_TIMING_CANDIDATE),
        .CORE_128TRIT_CANDIDATE(CORE_128TRIT_CANDIDATE),
        .POOL_READ_PARALLEL_SLOTS(POOL_READ_PARALLEL_SLOTS),
        .RESIDUAL_NORM_FUSION(RESIDUAL_NORM_FUSION),
        .RESIDUAL_NORM_TILE_PRELOAD(RESIDUAL_NORM_TILE_PRELOAD),
        .ATTENTION_PARALLEL_CANDIDATE(ATTENTION_PARALLEL_CANDIDATE),
        .ADAPTER_STATIC_REUSE(ADAPTER_STATIC_REUSE),
        .ATTENTION_PARALLEL_HEADS(ATTENTION_PARALLEL_HEADS),
        .ATTENTION_QUANT_STREAM_PIPELINE(ATTENTION_QUANT_STREAM_PIPELINE),
        .RECURRENCES_OVERRIDE(RECURRENCES_OVERRIDE)
    ) u_recurrent_core (
        .clk(s_axi_aclk), .rst_n(s_axi_aresetn), .start(core_start),
        .context_tokens(context_tokens_q),
        .command_valid(command_valid), .command_id(command_id), .command_stage(),
        .block_index(block_index), .recurrence_index(recurrence_index), .command_index(),
        .matrix_rows(), .matrix_columns(), .vector_length(), .active_context_tokens(),
        .attention_is_full(), .payload_descriptor_valid(payload_descriptor_valid),
        .payload_descriptor_adapter_file(payload_adapter_file),
        .payload_weight_offset_bytes(payload_weight_offset),
        .payload_weight_bytes(payload_weight_bytes), .payload_weight_words(payload_weight_words),
        .payload_gamma_offset_bytes(payload_gamma_offset),
        .payload_gamma_bytes(payload_gamma_bytes), .payload_gamma_words(payload_gamma_words),
        .payload_matrix_rows(payload_rows), .payload_matrix_columns(payload_columns),
        .done(core_done), .error(core_error), .operator_ready(1'b1), .operator_done(1'b0),
        .linear_engine_valid(linear_engine_valid),
        .linear_engine_command_id(linear_engine_command_id),
        .linear_engine_block_index(linear_engine_block_index),
        .linear_engine_recurrence_index(), .linear_engine_rows(), .linear_engine_columns(),
        .linear_engine_window_count(), .linear_engine_pool_words_per_port(),
        .linear_engine_tile_pool_base_per_port(), .linear_engine_tile_index(linear_engine_tile_index),
        .linear_engine_tile_row_start(), .linear_engine_tile_rows(), .linear_engine_tile_ready(),
        .linear_engine_tile_done(), .linear_result_valid(), .linear_result_ready(1'b1),
        .linear_result_q12(), .linear_result_rows(), .linear_activation_window_index(),
        .weight_start(weight_start), .weight_load_request_ready(weight_load_request_ready),
        .weight_abort(1'b0), .weight_prefetch_start(weight_prefetch_start),
        .weight_prefetch_ready(weight_prefetch_ready),
        .weight_prefetch_command_id(prefetch_command_q),
        .weight_prefetch_block_index(prefetch_block_q),
        .weight_prefetch_recurrence_index(prefetch_recurrence_q),
        .weight_prefetch_rows(prefetch_rows_q), .weight_prefetch_columns(prefetch_columns_q),
        .weight_stream_valid(weight_stream_valid), .weight_stream_ready(weight_stream_ready),
        .weight_stream_data(weight_stream_data), .weight_stream_last(weight_stream_last),
        .hbm_weight_load_start(hbm_weight_load_start),
        .hbm_weight_load_rows(hbm_weight_load_rows),
        .hbm_weight_load_columns(hbm_weight_load_columns),
        .hbm_weight_load_command_id(hbm_weight_load_command_id),
        .hbm_weight_load_block_index(hbm_weight_load_block_index),
        .hbm_weight_skip_adapter_static(hbm_weight_skip_adapter_static),
        .hbm_pool_load_valid(hbm_pool_load_valid),
        .hbm_pool_load_ready(hbm_pool_load_ready),
        .hbm_pool_load_enable(hbm_pool_load_enable),
        .hbm_pool_load_address(hbm_pool_load_address),
        .hbm_pool_load_data(hbm_pool_load_data),
        .weight_store_busy(weight_store_busy), .weight_load_done(weight_load_done),
        .weight_protocol_error(weight_protocol_error), .shadow_occupancy(),
        .round_config_valid(3'b111), .round_config_ready(),
        .round_activation_scale_fp16(16'h3c00),
        .gamma_load_start(gamma_load_start), .gamma_load_start_ready(gamma_load_start_ready),
        .gamma_load_command_id(saved_command_q), .gamma_load_block_index(saved_block_q),
        .gamma_load_recurrence_index(saved_recurrence_q),
        .gamma_load_matrix_rows(saved_rows_q), .gamma_load_matrix_columns(saved_columns_q),
        .gamma_load_valid(gamma_load_valid), .gamma_load_ready(gamma_load_ready),
        .gamma_load_pair_data(gamma_load_pair_data),
        .gamma_load_vector_data(gamma_load_vector_data), .gamma_load_last(gamma_load_last),
        .gamma_load_done(gamma_load_done), .gamma_protocol_error(gamma_protocol_error),
        .activation_valid(3'b111), .activation_ready(), .activation_window(activation_window),
        .rope_write_position(11'd0), .rope_active_context_tokens(context_tokens_q[11:0]),
        .rope_window_start(11'd0), .rope_query_q4_12(4096'd0), .rope_key_q4_12(4096'd0),
        .rope_value_q4_12(4096'd0), .rope_sin_q1_15(4096'd0), .rope_cos_q1_15(rope_cos),
        .rope_ready(), .rope_query_valid(), .rope_query_rotated_q4_12(),
        .rope_kv_ready(1'b1), .rope_kv_valid(), .rope_kv_token_index(),
        .rope_kv_chunk_index(), .rope_kv_key_chunk_q4_12(), .rope_kv_value_chunk_q4_12(),
        .rope_kv_last(), .rope_cache_load_valid(rope_cache_load_valid_q),
        .rope_cache_load_index(rope_cache_load_index_q), .rope_cache_load_key_q4_12(4096'd0),
        .rope_cache_load_value_q4_12(4096'd0),
        .rope_cache_load_valid_parallel(rope_cache_load_valid_parallel_q),
        .rope_cache_load_index_parallel(rope_cache_load_index_parallel_q),
        .rope_cache_load_key_q4_12_parallel('0), .rope_cache_load_value_q4_12_parallel('0),
        .rope_cache_read_request_parallel(rope_cache_read_request_parallel),
        .rope_cache_read_request_ready_parallel(rope_cache_read_request_ready_parallel),
        .rope_cache_read_head_parallel(rope_cache_read_head_parallel),
        .rope_cache_read_index_parallel(rope_cache_read_index_parallel),
        .rope_cache_load_ready_parallel(),
        .rope_cache_read_request(rope_cache_read_request),
        .rope_cache_read_request_ready(rope_cache_read_request_ready),
        .rope_cache_read_head(rope_cache_read_head), .rope_cache_read_index(rope_cache_read_index),
        .rope_cache_load_ready(), .rope_busy(), .rope_done(), .rope_protocol_error(),
        .attention_query_q4_12(4096'd0), .attention_kv_valid(1'b0),
        .attention_kv_ready(), .attention_kv_key_q4_12(2048'd0),
        .attention_kv_value_q4_12(2048'd0), .attention_out_valid(),
        .attention_out_ready(1'b1), .attention_out_chunk_q4_12(), .attention_out_last(),
        .attention_ready(), .attention_busy(), .attention_done(), .attention_protocol_error(),
        .norm_in_valid(1'b0), .norm_in_ready(), .norm_in_activation_q4_12(256'd0),
        .norm_in_gamma_q4_12(NORM_GAMMA_FROM_HOST ? norm_gamma_chunk_data : {16{16'h1000}}),
        .norm_gamma_chunk_request(norm_gamma_chunk_request),
        .norm_gamma_chunk_index(norm_gamma_chunk_index), .norm_gamma_chunk_lane(norm_gamma_chunk_lane),
        .norm_preload_gamma_request(norm_gamma_tile_request),
        .norm_preload_gamma_command_id(norm_gamma_tile_command),
        .norm_preload_gamma_tile_index(norm_gamma_tile_index),
        .norm_preload_gamma_valid(norm_gamma_tile_valid_q),
        .norm_preload_gamma_q4_12(norm_gamma_tile_data),
        .norm_in_last(1'b0), .norm_out_valid(),
        .norm_out_ready(1'b1), .norm_out_normalized_q4_12(), .norm_out_quantized_int8(),
        .norm_out_last(), .norm_inv_rms_q15(), .norm_activation_scale_q4_12(),
        .norm_ready(), .norm_busy(), .norm_done(), .norm_protocol_error(),
        .swiglu_in_valid(1'b0), .swiglu_in_ready(), .swiglu_gate_q4_12(256'd0),
        .swiglu_up_q4_12(256'd0), .swiglu_residual_q4_12(256'd0),
        .swiglu_in_last(1'b0), .swiglu_residual_rate_q15(16'h7fff), .swiglu_ready(),
        .swiglu_out_valid(), .swiglu_out_ready(1'b1), .swiglu_output_q4_12(),
        .swiglu_out_last(), .swiglu_busy(), .swiglu_done(), .swiglu_protocol_error(),
        .core_output_valid(core_output_valid), .core_output_ready(core_output_ready),
        .core_output_q4_12(core_output_q4_12), .core_output_last(core_output_last),
        .core_output_done(core_output_done)
    );

    generate
        if (HBM_PARALLEL_LOAD) begin : gen_hbm_weight_path
            rtwsr_plan6_huginn_u280_hbm_weight_path #(
                .HBM_PCS(HBM_PCS), .MAX_OUTSTANDING(HBM_MAX_OUTSTANDING),
                .POOL_LANES(HBM_POOL_LANES),
                .RING_RECORDS(HBM_RING_RECORDS),
                .ADAPTER_STATIC_REUSE(ADAPTER_STATIC_REUSE)
            ) u_weight_path (
                .core_clk(s_axi_aclk), .core_rst_n(s_axi_aresetn),
                .axi_clk(hbm_axi_clk), .axi_rst_n(hbm_axi_rst_n),
                .load_start(hbm_weight_load_start),
                .load_command_id(hbm_weight_load_command_id),
                .load_block_index(hbm_weight_load_block_index),
                .load_rows(hbm_weight_load_rows),
                .load_columns(hbm_weight_load_columns),
                .load_skip_adapter_static(hbm_weight_skip_adapter_static),
                .load_busy(hbm_path_busy), .load_done(hbm_path_done),
                .protocol_error(hbm_path_error),
                .m_axi_araddr(hbm_m_axi_araddr), .m_axi_arid(hbm_m_axi_arid),
                .m_axi_arlen(hbm_m_axi_arlen), .m_axi_arsize(hbm_m_axi_arsize),
                .m_axi_arburst(hbm_m_axi_arburst),
                .m_axi_arvalid(hbm_m_axi_arvalid),
                .m_axi_arready(hbm_m_axi_arready), .m_axi_rid(hbm_m_axi_rid),
                .m_axi_rdata(hbm_m_axi_rdata), .m_axi_rresp(hbm_m_axi_rresp),
                .m_axi_rlast(hbm_m_axi_rlast), .m_axi_rvalid(hbm_m_axi_rvalid),
                .m_axi_rready(hbm_m_axi_rready),
                .pool_wr_valid(hbm_pool_load_valid),
                .pool_wr_ready(hbm_pool_load_ready),
                .pool_wr_enable(hbm_pool_load_enable),
                .pool_wr_address(hbm_pool_load_address),
                .pool_wr_data(hbm_pool_load_data), .ring_occupancy()
            );
        end else begin : gen_ddr_weight_path
            assign hbm_m_axi_araddr = '0;
            assign hbm_m_axi_arid = '0;
            assign hbm_m_axi_arlen = '0;
            assign hbm_m_axi_arsize = '0;
            assign hbm_m_axi_arburst = '0;
            assign hbm_m_axi_arvalid = '0;
            assign hbm_m_axi_rready = '0;
            assign hbm_pool_load_valid = 1'b0;
            assign hbm_pool_load_enable = '0;
            assign hbm_pool_load_address = '0;
            assign hbm_pool_load_data = '0;
            assign hbm_path_busy = 1'b0;
            assign hbm_path_done = 1'b0;
            assign hbm_path_error = 1'b0;
        end
    endgenerate

    always_ff @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            awaddr_q <= '0;
            wdata_q <= '0;
            wstrb_q <= '0;
            aw_pending <= 1'b0;
            w_pending <= 1'b0;
            araddr_q <= '0;
            s_axi_bresp <= 2'b00;
            s_axi_bvalid <= 1'b0;
            s_axi_rdata <= '0;
            s_axi_rresp <= 2'b00;
            s_axi_rvalid <= 1'b0;
            start_pulse_q <= 1'b0;
            software_error_set_q <= 1'b0;
            software_error_clear_q <= 1'b0;
            context_tokens_q <= 16'd512;
        end else begin
            start_pulse_q <= 1'b0;
            software_error_set_q <= 1'b0;
            software_error_clear_q <= 1'b0;
            if (s_axi_awvalid && s_axi_awready) begin
                awaddr_q <= s_axi_awaddr;
                aw_pending <= 1'b1;
            end
            if (s_axi_wvalid && s_axi_wready) begin
                wdata_q <= s_axi_wdata;
                wstrb_q <= s_axi_wstrb;
                w_pending <= 1'b1;
            end
            if (write_commit) begin
                aw_pending <= 1'b0;
                w_pending <= 1'b0;
                s_axi_bvalid <= 1'b1;
                s_axi_bresp <= 2'b00;
                if (|write_addr[1:0]) begin
                    software_error_set_q <= 1'b1;
                end else if (write_index == 10'h000) begin
                    if (write_strb[0] && write_data[1])
                        software_error_clear_q <= 1'b1;
                    if (write_strb[0] && write_data[0]) begin
                        if (state_q == IDLE || state_q == COMPLETE || state_q == FAILED)
                            start_pulse_q <= 1'b1;
                        else
                            software_error_set_q <= 1'b1;
                    end
                end else if (write_index == 10'h006) begin
                    if (write_data[15:0] == 0 || write_data[15:0] > MAX_CONTEXT)
                        software_error_set_q <= 1'b1;
                    else
                        context_tokens_q <= write_data[15:0];
                end else begin
                    software_error_set_q <= 1'b1;
                end
            end
            if (s_axi_bvalid && s_axi_bready)
                s_axi_bvalid <= 1'b0;

            if (s_axi_arvalid && s_axi_arready) begin
                araddr_q <= s_axi_araddr;
                s_axi_rdata <= read_value;
                s_axi_rresp <= 2'b00;
                s_axi_rvalid <= 1'b1;
            end else if (s_axi_rvalid && s_axi_rready) begin
                s_axi_rvalid <= 1'b0;
            end
        end
    end

    always_ff @(posedge s_axi_aclk) begin
        logic [31:0] folded_output;
        if (!s_axi_aresetn) begin
            state_q <= IDLE;
            prefetch_state_q <= PREFETCH_IDLE;
            saved_command_q <= '0;
            saved_block_q <= '0;
            saved_recurrence_q <= '0;
            saved_rows_q <= '0;
            saved_columns_q <= '0;
            saved_weight_words_q <= '0;
            saved_gamma_words_q <= '0;
            saved_weight_address_q <= '0;
            saved_gamma_address_q <= '0;
            weight_load_done_seen_q <= 1'b0;
            gamma_load_done_seen_q <= 1'b0;
            gamma_pair_index_q <= '0;
            norm_gamma_load_beat_q <= '0;
            norm_gamma_load_tile_index_q <= '0;
            norm_gamma_load_tile_q <= '0;
            norm_gamma_loaded_q <= 1'b0;
            saved_prefetch_match_q <= 1'b0;
            prefetch_target_valid_q <= 1'b0;
            prefetch_done_seen_q <= 1'b0;
            prefetch_command_q <= '0;
            prefetch_block_q <= '0;
            prefetch_recurrence_q <= '0;
            prefetch_rows_q <= '0;
            prefetch_columns_q <= '0;
            prefetch_weight_words_q <= '0;
            prefetch_weight_address_q <= '0;
            rope_cache_load_valid_q <= 1'b0;
            rope_cache_load_index_q <= '0;
            rope_cache_load_valid_parallel_q <= '0;
            rope_cache_load_index_parallel_q <= '0;
            run_cycles_q <= '0;
            nonzero_chunks_q <= '0;
            output_digest_q <= '0;
            shell_error_q <= 1'b0;
        end else begin
            rope_cache_load_valid_q <= 1'b0;
            rope_cache_load_valid_parallel_q <= '0;
            if (rope_cache_read_request && rope_cache_read_request_ready) begin
                rope_cache_load_valid_q <= 1'b1;
                rope_cache_load_index_q <= rope_cache_read_index;
            end
            for (integer cache_port = 0; cache_port < ATTENTION_PARALLEL_HEADS; cache_port = cache_port + 1) begin
                if (rope_cache_read_request_parallel[cache_port] &&
                    rope_cache_read_request_ready_parallel[cache_port]) begin
                    rope_cache_load_valid_parallel_q[cache_port] <= 1'b1;
                    rope_cache_load_index_parallel_q[cache_port*11 +: 11] <=
                        rope_cache_read_index_parallel[cache_port*11 +: 11];
                end
            end
            if (weight_load_done)
                weight_load_done_seen_q <= 1'b1;
            if ((prefetch_state_q == PREFETCH_STREAM ||
                 prefetch_state_q == PREFETCH_WAIT_STORE ||
                 prefetch_state_q == PREFETCH_HBM_WAIT) && weight_load_done)
                prefetch_done_seen_q <= 1'b1;
            if (gamma_load_done)
                gamma_load_done_seen_q <= 1'b1;
            if (gamma_load_valid && gamma_load_ready) begin
                if (GAMMA_PARALLEL_LOAD || gamma_pair_index_q == 4'd15)
                    gamma_pair_index_q <= '0;
                else
                    gamma_pair_index_q <= gamma_pair_index_q + 1'b1;
            end
            if (state_q == NORM_GAMMA_COMMAND && dma_command_valid && dma_command_ready) begin
                norm_gamma_load_beat_q <= '0;
                norm_gamma_load_tile_index_q <= '0;
                norm_gamma_load_tile_q <= '0;
            end
            if (state_q == NORM_GAMMA_STREAM && dma_data_valid && dma_data_ready) begin
                norm_gamma_load_tile_q <= norm_gamma_load_tile_data;
                if (norm_gamma_load_beat_q == 2'd2) begin
                    norm_gamma_load_beat_q <= '0;
                    norm_gamma_load_tile_index_q <= norm_gamma_load_tile_index_q + 1'b1;
                    norm_gamma_load_tile_q <= '0;
                end else begin
                    norm_gamma_load_beat_q <= norm_gamma_load_beat_q + 1'b1;
                end
            end
            if (state_q == NORM_GAMMA_STREAM && dma_done && !dma_error)
                norm_gamma_loaded_q <= 1'b1;
            if (start_pulse_q) begin
                run_cycles_q <= '0;
                nonzero_chunks_q <= '0;
                output_digest_q <= '0;
            end else if (state_q != IDLE && state_q != COMPLETE && state_q != FAILED) begin
                run_cycles_q <= run_cycles_q + 1'b1;
            end
            if (core_output_valid && core_output_ready) begin
                folded_output = '0;
                for (integer word_index = 0; word_index < 8; word_index++)
                    folded_output = folded_output ^ core_output_q4_12[word_index*32 +: 32];
                output_digest_q <= {output_digest_q[26:0], output_digest_q[31:27]} ^ folded_output;
                if (|core_output_q4_12)
                    nonzero_chunks_q <= nonzero_chunks_q + 1'b1;
            end

            if (core_error || weight_protocol_error || gamma_protocol_error || dma_error ||
                hbm_path_error)
                shell_error_q <= 1'b1;
            if (software_error_clear_q)
                shell_error_q <= 1'b0;
            if (software_error_set_q)
                shell_error_q <= 1'b1;

            case (prefetch_state_q)
                PREFETCH_IDLE: begin
                    if (state_q == RUN_OPERATOR && next_payload_valid &&
                        weight_prefetch_ready) begin
                        prefetch_command_q <= next_weight_command_id;
                        prefetch_block_q <= next_weight_block_index;
                        prefetch_recurrence_q <= next_weight_recurrence_index;
                        prefetch_rows_q <= next_payload_rows;
                        prefetch_columns_q <= next_payload_columns;
                        prefetch_weight_words_q <= next_payload_weight_words;
                        prefetch_weight_address_q <= next_payload_adapter_file ?
                            ADAPTER_WEIGHT_BASE + {5'd0, next_payload_weight_offset} :
                            CORE_WEIGHT_BASE + {5'd0, next_payload_weight_offset};
                        prefetch_target_valid_q <= 1'b1;
                        prefetch_done_seen_q <= 1'b0;
                        prefetch_state_q <= PREFETCH_START;
                    end
                end
                PREFETCH_START: begin
                    if (weight_prefetch_ready)
                        prefetch_state_q <= HBM_PARALLEL_LOAD ?
                            PREFETCH_HBM_WAIT : PREFETCH_COMMAND;
                end
                PREFETCH_HBM_WAIT: begin
                    if (hbm_path_done || weight_load_done)
                        prefetch_state_q <= PREFETCH_READY;
                end
                PREFETCH_COMMAND: begin
                    if (dma_command_valid && dma_command_ready)
                        prefetch_state_q <= PREFETCH_STREAM;
                end
                PREFETCH_STREAM: begin
                    if (dma_done)
                        prefetch_state_q <= PREFETCH_WAIT_STORE;
                end
                PREFETCH_WAIT_STORE: begin
                    if (prefetch_done_seen_q || weight_load_done)
                        prefetch_state_q <= PREFETCH_READY;
                end
                PREFETCH_READY: begin
                    if (state_q == WAIT_ENGINE && saved_prefetch_match_q &&
                        prefetch_state_q == PREFETCH_READY) begin
                        prefetch_state_q <= PREFETCH_IDLE;
                        prefetch_target_valid_q <= 1'b0;
                        prefetch_done_seen_q <= 1'b0;
                    end
                end
                default: prefetch_state_q <= PREFETCH_IDLE;
            endcase

            if (core_error || weight_protocol_error || gamma_protocol_error || dma_error ||
                hbm_path_error) begin
                if (state_q != IDLE && state_q != COMPLETE)
                    state_q <= FAILED;
            end else case (state_q)
                IDLE, COMPLETE: begin
                    if (start_pulse_q)
                        state_q <= NORM_GAMMA_FROM_HOST && !norm_gamma_loaded_q ?
                            NORM_GAMMA_COMMAND :
                            (NORM_GAMMA_FROM_HOST ? START_CORE : WAIT_COMMAND);
                end
                FAILED: begin
                    if (start_pulse_q)
                        state_q <= NORM_GAMMA_FROM_HOST && !norm_gamma_loaded_q ?
                            NORM_GAMMA_COMMAND :
                            (NORM_GAMMA_FROM_HOST ? START_CORE : WAIT_COMMAND);
                end
                WAIT_COMMAND, RUN_OPERATOR: begin
                    if (core_done)
                        state_q <= COMPLETE;
                    else if (command_valid && payload_descriptor_valid) begin
                        saved_command_q <= command_id;
                        saved_block_q <= block_index;
                        saved_recurrence_q <= recurrence_index;
                        saved_rows_q <= payload_rows;
                        saved_columns_q <= payload_columns;
                        saved_weight_words_q <= payload_weight_words;
                        saved_gamma_words_q <= payload_gamma_words;
                        saved_weight_address_q <= payload_adapter_file ?
                            ADAPTER_WEIGHT_BASE + {5'd0, payload_weight_offset} :
                            CORE_WEIGHT_BASE + {5'd0, payload_weight_offset};
                        saved_gamma_address_q <= payload_adapter_file ?
                            DDR_GAMMA_BASE + {5'd0, payload_gamma_offset} :
                            CORE_GAMMA_BASE + {5'd0, payload_gamma_offset};
                        weight_load_done_seen_q <= 1'b0;
                        gamma_load_done_seen_q <= 1'b0;
                        saved_prefetch_match_q <= prefetch_target_valid_q &&
                            prefetch_command_q == command_id &&
                            prefetch_block_q == block_index &&
                            prefetch_recurrence_q == recurrence_index &&
                            prefetch_rows_q == payload_rows &&
                            prefetch_columns_q == payload_columns;
                        state_q <= WAIT_ENGINE;
                    end
                end
                WAIT_ENGINE: begin
                    if (saved_prefetch_match_q && prefetch_state_q == PREFETCH_READY) begin
                        prefetch_state_q <= PREFETCH_IDLE;
                        prefetch_target_valid_q <= 1'b0;
                        prefetch_done_seen_q <= 1'b0;
                        saved_prefetch_match_q <= 1'b0;
                        state_q <= START_GAMMA;
                    end else if (!saved_prefetch_match_q && weight_start &&
                                 weight_load_request_ready)
                        state_q <= HBM_PARALLEL_LOAD ? HBM_WAIT_WEIGHT : DMA_WEIGHT_COMMAND;
                end
                HBM_WAIT_WEIGHT: begin
                    if (hbm_path_done || weight_load_done_seen_q)
                        state_q <= START_GAMMA;
                end
                DMA_WEIGHT_COMMAND: begin
                    if (dma_command_valid && dma_command_ready)
                        state_q <= DMA_WEIGHT_STREAM;
                end
                DMA_WEIGHT_STREAM: begin
                    if (dma_done) begin
                        if (dma_error)
                            state_q <= FAILED;
                        else
                            state_q <= WAIT_WEIGHT_STORE;
                    end
                end
                WAIT_WEIGHT_STORE: begin
                    if (weight_load_done_seen_q)
                        state_q <= START_GAMMA;
                end
                START_GAMMA: begin
                    if (gamma_load_start && gamma_load_start_ready)
                        state_q <= DMA_GAMMA_COMMAND;
                end
                DMA_GAMMA_COMMAND: begin
                    if (dma_command_valid && dma_command_ready) begin
                        gamma_pair_index_q <= '0;
                        state_q <= DMA_GAMMA_STREAM;
                    end
                end
                DMA_GAMMA_STREAM: begin
                    if (dma_done) begin
                        if (dma_error)
                            state_q <= FAILED;
                        else
                            state_q <= WAIT_GAMMA_STORE;
                    end
                end
                WAIT_GAMMA_STORE: begin
                    if (gamma_load_done_seen_q)
                        state_q <= RUN_OPERATOR;
                end
                NORM_GAMMA_COMMAND: begin
                    if (dma_command_valid && dma_command_ready)
                        state_q <= NORM_GAMMA_STREAM;
                end
                NORM_GAMMA_STREAM: begin
                    if (dma_done) begin
                        if (dma_error)
                            state_q <= FAILED;
                        else
                            state_q <= START_CORE;
                    end
                end
                START_CORE: state_q <= WAIT_COMMAND;
                default: begin end
            endcase
        end
    end

    initial begin
        if (S_AXI_DATA_WIDTH != 32 || S_AXI_ADDR_WIDTH < 12)
            $error("Plan 6 shell requires 32-bit AXI4-Lite and at least 12 address bits");
        if ((DDR_WEIGHT_BASE[5:0] != 0) || (DDR_GAMMA_BASE[5:0] != 0))
            $error("Plan 6 payload bases must be 64-byte aligned");
        if (CORE_GAMMA_BASE < DDR_GAMMA_BASE + ADAPTER_GAMMA_BYTES)
            $error("Plan 6 Adapter and core Gamma DDR regions overlap");
        if (RESIDUAL_NORM_TILE_PRELOAD && (!RESIDUAL_NORM_FUSION || !NORM_GAMMA_FROM_HOST))
            $error("Norm tile preload requires residual fusion and loaded Norm gamma");
    end
endmodule
