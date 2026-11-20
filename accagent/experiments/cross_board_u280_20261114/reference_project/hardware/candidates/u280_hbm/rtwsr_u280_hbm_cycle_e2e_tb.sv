`timescale 1ps / 1ps

module rtwsr_u280_hbm_cycle_e2e_tb #(
    parameter int CONTEXT_TOKENS = 512,
    parameter int MAX_CONTEXT = 2048,
    parameter int RECURRENCES = 32,
    parameter int CORE_LINEAR_CHANNELS = 96,
    parameter int HBM_POOL_LANES = 24,
    parameter int HBM_RING_RECORDS = 73728,
    parameter bit CORE_TIMING_CANDIDATE = 1'b0,
    parameter bit CORE_128TRIT_CANDIDATE = 1'b0,
    parameter bit POOL_READ_PARALLEL_SLOTS = 1'b0,
    parameter bit GAMMA_PARALLEL_LOAD = 1'b0,
    parameter bit ATTENTION_PARALLEL_CANDIDATE = 1'b0,
    parameter bit ADAPTER_STATIC_REUSE = 1'b0,
    parameter bit RESIDUAL_NORM_FUSION = 1'b0,
    parameter bit RESIDUAL_NORM_TILE_PRELOAD = 1'b0,
    parameter bit NORM_GAMMA_FROM_HOST = 1'b0,
    parameter int ATTENTION_PARALLEL_HEADS = 4,
    parameter bit ATTENTION_QUANT_STREAM_PIPELINE = 1'b0
);
    localparam int HBM_PCS = 32;
    localparam int MAX_OUTSTANDING = 16;
    localparam int HBM_READ_LATENCY = 77;
    localparam int CORE_HZ = 225_000_000;
    localparam time POLL_INTERVAL_PS = 1_000_000_000;
    localparam time TIMEOUT_PS = 64'd3_000_000_000_000;

    logic core_clk = 1'b0;
    logic core_reset_n = 1'b0;
    logic hbm_clk = 1'b0;
    logic hbm_reset_n = 1'b0;

    logic [11:0] awaddr, araddr_axil;
    logic [2:0] awprot, arprot_axil;
    logic awvalid, awready, wvalid, wready, bvalid, bready;
    logic [31:0] wdata, rdata_axil;
    logic [3:0] wstrb;
    logic [1:0] bresp, rresp_axil;
    logic arvalid_axil, arready_axil, rvalid_axil, rready_axil;

    logic [36:0] gamma_araddr;
    logic [4:0] gamma_arid;
    logic [7:0] gamma_arlen;
    logic [2:0] gamma_arsize;
    logic [1:0] gamma_arburst;
    logic gamma_arvalid, gamma_arready;
    logic [4:0] gamma_rid;
    logic [511:0] gamma_rdata;
    logic [1:0] gamma_rresp;
    logic gamma_rlast, gamma_rvalid, gamma_rready;
    logic [63:0] gamma_read_beats;

    logic [HBM_PCS*33-1:0] hbm_araddr;
    logic [HBM_PCS*6-1:0] hbm_arid;
    logic [HBM_PCS*4-1:0] hbm_arlen;
    logic [HBM_PCS*3-1:0] hbm_arsize;
    logic [HBM_PCS*2-1:0] hbm_arburst;
    logic [HBM_PCS-1:0] hbm_arvalid, hbm_arready;
    logic [HBM_PCS*6-1:0] hbm_rid;
    logic [HBM_PCS*256-1:0] hbm_rdata;
    logic [HBM_PCS*2-1:0] hbm_rresp;
    logic [HBM_PCS-1:0] hbm_rlast, hbm_rvalid, hbm_rready;
    logic [HBM_PCS-1:0] hbm_protocol_error;

    logic [63:0] hbm_ar_count;
    logic [63:0] hbm_r_beats;
    logic [63:0] hbm_pc_beats [0:HBM_PCS-1];
    logic [31:0] read_status;
    logic [31:0] cycles_low, cycles_high;
    logic [31:0] output_chunks, output_digest, final_context;
    logic [31:0] poll_count;
    logic [31:0] status_word;
    logic [63:0] shell_cycles;
    logic run_started;
    logic [63:0] error_mask;
    real elapsed_ms;
    logic [63:0] gamma_read_beats_unused;
    logic pool_reject_logged;
    logic [4:0] recurrence_log_index;
    logic [63:0] recurrence_log_cycles;
    logic [63:0] recurrence_log_previous_cycles;

    always #2222 core_clk = ~core_clk;
    always #1111 hbm_clk = ~hbm_clk;

    initial begin
        recurrence_log_index = '0;
        recurrence_log_cycles = '0;
        recurrence_log_previous_cycles = '0;
    end

    always @(negedge core_clk) begin
        if (run_started) begin
            recurrence_log_cycles <= recurrence_log_cycles + 1'b1;
            if (u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_recurrence_index !=
                recurrence_log_index) begin
                $display("U280_CYCLE_E2E_RECURRENCE recurrence=%0d cycles=%0d delta_cycles=%0d hbm_bytes=%0d",
                    u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_recurrence_index,
                    recurrence_log_cycles,
                    recurrence_log_cycles - recurrence_log_previous_cycles,
                    hbm_r_beats * 64'd32);
                $fflush();
                recurrence_log_index <=
                    u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_recurrence_index;
                recurrence_log_previous_cycles <= recurrence_log_cycles;
            end
        end
    end

    rtwsr_plan6_huginn_u280_hbm_shell #(
        .HBM_PCS(HBM_PCS), .HBM_MAX_OUTSTANDING(MAX_OUTSTANDING),
        .HBM_POOL_LANES(HBM_POOL_LANES),
        .LINEAR_CHANNELS(CORE_LINEAR_CHANNELS),
        .MAX_CONTEXT(MAX_CONTEXT),
        .HBM_RING_RECORDS(HBM_RING_RECORDS),
        .RECURRENCES_OVERRIDE(RECURRENCES),
        .CORE_TIMING_CANDIDATE(CORE_TIMING_CANDIDATE),
        .CORE_128TRIT_CANDIDATE(CORE_128TRIT_CANDIDATE),
        .POOL_READ_PARALLEL_SLOTS(POOL_READ_PARALLEL_SLOTS),
        .GAMMA_PARALLEL_LOAD(GAMMA_PARALLEL_LOAD),
        .ATTENTION_PARALLEL_CANDIDATE(ATTENTION_PARALLEL_CANDIDATE),
        .ADAPTER_STATIC_REUSE(ADAPTER_STATIC_REUSE),
        .RESIDUAL_NORM_FUSION(RESIDUAL_NORM_FUSION),
        .RESIDUAL_NORM_TILE_PRELOAD(RESIDUAL_NORM_TILE_PRELOAD),
        .NORM_GAMMA_FROM_HOST(NORM_GAMMA_FROM_HOST),
        .ATTENTION_PARALLEL_HEADS(ATTENTION_PARALLEL_HEADS),
        .ATTENTION_QUANT_STREAM_PIPELINE(ATTENTION_QUANT_STREAM_PIPELINE)
    ) u_shell (
        .core_clk(core_clk), .core_rst_n(core_reset_n),
        .hbm_axi_clk(hbm_clk), .hbm_axi_rst_n(hbm_reset_n),
        .s_axi_awaddr(awaddr), .s_axi_awprot(awprot),
        .s_axi_awvalid(awvalid), .s_axi_awready(awready),
        .s_axi_wdata(wdata), .s_axi_wstrb(wstrb),
        .s_axi_wvalid(wvalid), .s_axi_wready(wready),
        .s_axi_bresp(bresp), .s_axi_bvalid(bvalid), .s_axi_bready(bready),
        .s_axi_araddr(araddr_axil), .s_axi_arprot(arprot_axil),
        .s_axi_arvalid(arvalid_axil), .s_axi_arready(arready_axil),
        .s_axi_rdata(rdata_axil), .s_axi_rresp(rresp_axil),
        .s_axi_rvalid(rvalid_axil), .s_axi_rready(rready_axil),
        .gamma_m_axi_araddr(gamma_araddr), .gamma_m_axi_arid(gamma_arid),
        .gamma_m_axi_arlen(gamma_arlen), .gamma_m_axi_arsize(gamma_arsize),
        .gamma_m_axi_arburst(gamma_arburst), .gamma_m_axi_arvalid(gamma_arvalid),
        .gamma_m_axi_arready(gamma_arready), .gamma_m_axi_rid(gamma_rid),
        .gamma_m_axi_rdata(gamma_rdata), .gamma_m_axi_rresp(gamma_rresp),
        .gamma_m_axi_rlast(gamma_rlast), .gamma_m_axi_rvalid(gamma_rvalid),
        .gamma_m_axi_rready(gamma_rready),
        .hbm_m_axi_araddr(hbm_araddr), .hbm_m_axi_arid(hbm_arid),
        .hbm_m_axi_arlen(hbm_arlen), .hbm_m_axi_arsize(hbm_arsize),
        .hbm_m_axi_arburst(hbm_arburst), .hbm_m_axi_arvalid(hbm_arvalid),
        .hbm_m_axi_arready(hbm_arready), .hbm_m_axi_rid(hbm_rid),
        .hbm_m_axi_rdata(hbm_rdata), .hbm_m_axi_rresp(hbm_rresp),
        .hbm_m_axi_rlast(hbm_rlast), .hbm_m_axi_rvalid(hbm_rvalid),
        .hbm_m_axi_rready(hbm_rready)
    );

    rtwsr_u280_axil_bfm u_axil (
        .clk(core_clk), .rst_n(core_reset_n),
        .awaddr(awaddr), .awprot(awprot), .awvalid(awvalid), .awready(awready),
        .wdata(wdata), .wstrb(wstrb), .wvalid(wvalid), .wready(wready),
        .bresp(bresp), .bvalid(bvalid), .bready(bready),
        .araddr(araddr_axil), .arprot(arprot_axil),
        .arvalid(arvalid_axil), .arready(arready_axil), .rdata(rdata_axil),
        .rresp(rresp_axil), .rvalid(rvalid_axil), .rready(rready_axil)
    );

    rtwsr_u280_gamma_axi_bfm u_gamma (
        .clk(core_clk), .rst_n(core_reset_n),
        .araddr(gamma_araddr), .arid(gamma_arid), .arlen(gamma_arlen),
        .arsize(gamma_arsize), .arburst(gamma_arburst),
        .arvalid(gamma_arvalid), .arready(gamma_arready),
        .rid(gamma_rid), .rdata(gamma_rdata), .rresp(gamma_rresp),
        .rlast(gamma_rlast), .rvalid(gamma_rvalid), .rready(gamma_rready),
        .read_beats(gamma_read_beats)
    );

    rtwsr_u280_hbm_axi_cycle_model #(
        .HBM_PCS(HBM_PCS), .MAX_OUTSTANDING(MAX_OUTSTANDING),
        .READ_LATENCY(HBM_READ_LATENCY)
    ) u_hbm_cycle_model (
        .hbm_clk(hbm_clk), .hbm_rst_n(hbm_reset_n),
        .araddr(hbm_araddr), .arid(hbm_arid), .arlen(hbm_arlen),
        .arsize(hbm_arsize), .arburst(hbm_arburst), .arvalid(hbm_arvalid),
        .arready(hbm_arready), .rid(hbm_rid), .rdata(hbm_rdata),
        .rresp(hbm_rresp), .rlast(hbm_rlast), .rvalid(hbm_rvalid),
        .rready(hbm_rready), .protocol_error(hbm_protocol_error)
    );

    always @(posedge core_clk) begin
        if (!core_reset_n)
            pool_reject_logged <= 1'b0;
        if (core_reset_n &&
            !pool_reject_logged &&
            u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.load_busy &&
            u_shell.u_plan6_huginn_hbm_shell.hbm_pool_load_valid &&
            !u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.parallel_group_valid) begin
            $display("U280_CYCLE_E2E_POOL_REJECT sim_ns=%0.3f pool_group=%0d/%0d pool_expected_address=%0d pool_expected_mask=0x%06x adapter_output_group=%0d adapter_address=%0d adapter_mask=0x%06x writable_words=%0d",
                $realtime / 1000.0,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.group_count_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.requested_groups,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.expected_group_address,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.expected_group_mask,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_adapter.output_group_q,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_adapter.output_address_q,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_adapter.output_mask_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.writable_words);
            pool_reject_logged <= 1'b1;
        end
    end

    always_ff @(posedge hbm_clk) begin
        if (!hbm_reset_n) begin
            hbm_ar_count <= '0;
            hbm_r_beats <= '0;
            for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
                hbm_pc_beats[lane] <= '0;
        end else begin
            hbm_ar_count <= hbm_ar_count + $countones(hbm_arvalid & hbm_arready);
            hbm_r_beats <= hbm_r_beats + $countones(hbm_rvalid & hbm_rready);
            for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
                if (hbm_rvalid[lane] && hbm_rready[lane])
                    hbm_pc_beats[lane] <= hbm_pc_beats[lane] + 1'b1;
        end
    end


    `define SHELL u_shell.u_plan6_huginn_hbm_shell
    `define CORE u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core
    `define PATH u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path

    longint unsigned shell_state_cycles [0:13];
    longint unsigned exclusive_cycles [0:7];
    longint unsigned raw_busy_cycles [0:7];
    longint unsigned profile_cycles;
    longint unsigned profile_sum;
    longint unsigned pool_write_groups, pool_write_records, prefetch_starts;
    longint unsigned adapter_peak_occupancy;
    longint unsigned hbm_burst_count [0:15];
    longint unsigned hbm_ar_stall_lane_cycles, hbm_r_stall_lane_cycles;
    longint unsigned hbm_offered_beats, hbm_requested_beats;
    longint unsigned hbm_active_cycles;
    integer unsigned hbm_outstanding [0:HBM_PCS-1];
    integer unsigned hbm_outstanding_peak [0:HBM_PCS-1];
    logic [HBM_PCS-1:0] hbm_scoreboard_error;
    logic [7:0] profile_busy;
    integer exclusive_category;

    // Exclusive priority: linear, attention, norm, SwiGLU, pool backpressure,
    // shell memory-wait states, RoPE/KV, control. Raw counters may overlap.
    always_comb begin
        profile_busy[0] = !`CORE.tile_execution_ready;
        profile_busy[1] = `CORE.attention_busy;
        profile_busy[2] = `CORE.norm_busy;
        profile_busy[3] = `CORE.swiglu_busy;
        profile_busy[4] = `SHELL.hbm_pool_load_valid && !`SHELL.hbm_pool_load_ready;
        profile_busy[5] = `SHELL.state_q == 2 || `SHELL.state_q == 6 ||
            `SHELL.state_q == 7 || `SHELL.state_q == 8 ||
            `SHELL.state_q == 9 || `SHELL.state_q == 10;
        profile_busy[6] = `CORE.rope_busy;
        profile_busy[7] = `SHELL.hbm_path_busy;
        exclusive_category = 7;
        for (integer category = 6; category >= 0; category = category - 1)
            if (profile_busy[category]) exclusive_category = category;
    end

    always_ff @(posedge core_clk) begin
        if (!core_reset_n || `SHELL.start_pulse_q) begin
            profile_cycles <= 0;
            pool_write_groups <= 0;
            pool_write_records <= 0;
            prefetch_starts <= 0;
            adapter_peak_occupancy <= 0;
            for (integer category = 0; category < 8; category = category + 1) begin
                exclusive_cycles[category] <= 0;
                raw_busy_cycles[category] <= 0;
            end
            for (integer state_index = 0; state_index < 14; state_index = state_index + 1)
                shell_state_cycles[state_index] <= 0;
        end else if (`SHELL.state_q != 0 && `SHELL.state_q != 12 && `SHELL.state_q != 13) begin
            profile_cycles <= profile_cycles + 1;
            exclusive_cycles[exclusive_category] <= exclusive_cycles[exclusive_category] + 1;
            shell_state_cycles[`SHELL.state_q] <= shell_state_cycles[`SHELL.state_q] + 1;
            for (integer category = 0; category < 8; category = category + 1)
                raw_busy_cycles[category] <= raw_busy_cycles[category] + 64'(profile_busy[category]);
            if (`SHELL.hbm_pool_load_valid && `SHELL.hbm_pool_load_ready) begin
                pool_write_groups <= pool_write_groups + 1;
                pool_write_records <= pool_write_records + 64'($countones(`SHELL.hbm_pool_load_enable));
            end
            if (`SHELL.weight_prefetch_start && `SHELL.weight_prefetch_ready)
                prefetch_starts <= prefetch_starts + 1;
            if (64'(`PATH.u_weight_adapter.ring_occupancy) > adapter_peak_occupancy)
                adapter_peak_occupancy <= 64'(`PATH.u_weight_adapter.ring_occupancy);
        end
    end

    always_ff @(posedge hbm_clk) begin
        integer accepted_beats;
        integer accepted_bursts_by_length [0:15];
        if (!hbm_reset_n) begin
            hbm_ar_stall_lane_cycles <= 0;
            hbm_r_stall_lane_cycles <= 0;
            hbm_offered_beats <= 0;
            hbm_requested_beats <= 0;
            hbm_active_cycles <= 0;
            hbm_scoreboard_error <= '0;
            for (integer length_index = 0; length_index < 16; length_index = length_index + 1)
                hbm_burst_count[length_index] <= 0;
            for (integer pc = 0; pc < HBM_PCS; pc = pc + 1) begin
                hbm_outstanding[pc] <= 0;
                hbm_outstanding_peak[pc] <= 0;
            end
        end else begin
            hbm_ar_stall_lane_cycles <= hbm_ar_stall_lane_cycles +
                64'($countones(hbm_arvalid & ~hbm_arready));
            hbm_r_stall_lane_cycles <= hbm_r_stall_lane_cycles +
                64'($countones(hbm_rvalid & ~hbm_rready));
            hbm_offered_beats <= hbm_offered_beats + 64'($countones(hbm_rvalid));
            if (`PATH.dma_busy) hbm_active_cycles <= hbm_active_cycles + 1;
            accepted_beats = 0;
            for (integer length_index = 0; length_index < 16; length_index = length_index + 1)
                accepted_bursts_by_length[length_index] = 0;
            for (integer pc = 0; pc < HBM_PCS; pc = pc + 1) begin
                if (hbm_arvalid[pc] && hbm_arready[pc]) begin
                    accepted_beats = accepted_beats + int'(hbm_arlen[pc*4 +: 4]) + 1;
                    accepted_bursts_by_length[hbm_arlen[pc*4 +: 4]] =
                        accepted_bursts_by_length[hbm_arlen[pc*4 +: 4]] + 1;
                end
                case ({hbm_arvalid[pc] && hbm_arready[pc],
                       hbm_rvalid[pc] && hbm_rready[pc] && hbm_rlast[pc]})
                    2'b10: begin
                        hbm_outstanding[pc] <= hbm_outstanding[pc] + 1;
                        if (hbm_outstanding[pc] + 1 > hbm_outstanding_peak[pc])
                            hbm_outstanding_peak[pc] <= hbm_outstanding[pc] + 1;
                        if (hbm_outstanding[pc] >= MAX_OUTSTANDING)
                            hbm_scoreboard_error[pc] <= 1'b1;
                    end
                    2'b01: begin
                        hbm_outstanding[pc] <= hbm_outstanding[pc] - 1;
                        if (hbm_outstanding[pc] == 0)
                            hbm_scoreboard_error[pc] <= 1'b1;
                    end
                    default: begin end
                endcase
            end
            hbm_requested_beats <= hbm_requested_beats + 64'(accepted_beats);
            for (integer length_index = 0; length_index < 16; length_index = length_index + 1)
                hbm_burst_count[length_index] <= hbm_burst_count[length_index] +
                    64'(accepted_bursts_by_length[length_index]);
        end
    end

    initial begin
        run_started = 1'b0;
        core_reset_n = 1'b0;
        hbm_reset_n = 1'b0;
        #100_000;
        core_reset_n = 1'b1;
        hbm_reset_n = 1'b1;
        repeat (16) @(posedge core_clk);
        u_axil.write_reg(12'h018, CONTEXT_TOKENS);
        u_axil.read_reg(12'h018, final_context);
        if (final_context != CONTEXT_TOKENS)
            $fatal(1, "AXI-Lite context readback mismatch: %0d", final_context);

        run_started = 1'b1;
        u_axil.write_reg(12'h000, 32'd1);
        $display("U280_CYCLE_E2E_START model=Huginn-3.5B blocks=4 recurrences=%0d context=%0d max_context=%0d hbm_pcs=%0d pool_lanes=%0d hbm_ring_records=%0d hbm_hz=450000000 core_hz=%0d read_latency_hbm_cycles=%0d max_outstanding=%0d core_timing_candidate=%0d core_128trit_candidate=%0d pool_read_parallel_slots=%0d gamma_parallel_load=%0d attention_parallel_candidate=%0d attention_parallel_heads=%0d attention_quant_stream_pipeline=%0d adapter_static_reuse=%0d residual_norm_fusion=%0d residual_norm_tile_preload=%0d norm_gamma_from_host=%0d payload=zero scheduling_only=1",
            RECURRENCES, final_context, MAX_CONTEXT, HBM_PCS, HBM_POOL_LANES, HBM_RING_RECORDS, CORE_HZ, HBM_READ_LATENCY, MAX_OUTSTANDING,
            CORE_TIMING_CANDIDATE, CORE_128TRIT_CANDIDATE, POOL_READ_PARALLEL_SLOTS,
            GAMMA_PARALLEL_LOAD,
            ATTENTION_PARALLEL_CANDIDATE, ATTENTION_PARALLEL_HEADS,
            ATTENTION_QUANT_STREAM_PIPELINE,
            ADAPTER_STATIC_REUSE, RESIDUAL_NORM_FUSION, RESIDUAL_NORM_TILE_PRELOAD,
            NORM_GAMMA_FROM_HOST);
        $fflush();
        poll_count = 0;
        status_word = '0;
        while (!status_word[0] && !status_word[2] && poll_count < TIMEOUT_PS / POLL_INTERVAL_PS) begin
            #(POLL_INTERVAL_PS);
            u_axil.read_reg(12'h004, read_status);
            status_word = read_status;
            poll_count = poll_count + 1;
            $display("U280_CYCLE_E2E_PROGRESS poll=%0d sim_ns=%0.3f status=0x%08x hbm_ar=%0d hbm_r_beats=%0d",
                poll_count, $realtime / 1000.0, status_word, hbm_ar_count, hbm_r_beats);
            $fflush();
        end

        if (!status_word[0]) begin
            $display("U280_CYCLE_E2E_FAIL status=0x%08x shell_state=%0d shell_error=%0d core_error=%0d dma_error=%0d hbm_path_error=%0d weight_protocol_error=%0d gamma_protocol_error=%0d hbm_protocol_error=0x%08x",
                status_word,
                u_shell.u_plan6_huginn_hbm_shell.state_q,
                u_shell.u_plan6_huginn_hbm_shell.shell_error_q,
                u_shell.u_plan6_huginn_hbm_shell.core_error,
                u_shell.u_plan6_huginn_hbm_shell.dma_error,
                u_shell.u_plan6_huginn_hbm_shell.hbm_path_error,
                u_shell.u_plan6_huginn_hbm_shell.weight_protocol_error,
                u_shell.u_plan6_huginn_hbm_shell.gamma_protocol_error,
                hbm_protocol_error);
            $display("U280_CYCLE_E2E_CORE_ERRORS scheduler=%0d linear_command=%0d weight_memory=%0d weight_control=%0d gamma=%0d tile=%0d rope=%0d attention=%0d norm=%0d swiglu=%0d bridge=%0d command=%0d stage=%0d block=%0d recurrence=%0d context=%0d",
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.linear_command_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.weight_memory_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.weight_control_error_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.gamma_protocol_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.tile_execution_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.rope_protocol_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.attention_protocol_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.norm_protocol_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.swiglu_protocol_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.bridge_error,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_command_id,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_command_stage,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_block_index,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_recurrence_index,
                u_shell.u_plan6_huginn_hbm_shell.context_tokens_q);
            $fflush();
            $display("U280_CYCLE_E2E_WEIGHT_ERRORS pool_last=%0d pool_read=%0d pool_overlap=%0d pool_busy=%0d pool_groups=%0d/%0d pool_rows=%0d pool_columns=%0d adapter_error=%0d adapter_groups=%0d/%0d adapter_occupancy=%0d path_error=%0d dma_error=%0d dma_lane_error=0x%08x",
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.last_error_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.read_error_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.overlap_error_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.load_busy,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.group_count_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.requested_groups,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.rows_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.windows_q,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_adapter.protocol_error,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_adapter.output_group_q,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_adapter.total_groups_q,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_adapter.ring_occupancy,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.path_error_q,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.dma_error,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_dma.lane_error_q);
            $display("U280_CYCLE_E2E_GROUP_CHECK adapter_address=%0d pool_expected_address=%0d adapter_mask=0x%06x pool_expected_mask=0x%06x pool_group_valid=%0d pool_writable_words=%0d load_valid=%0d pool_ready=%0d",
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_adapter.output_address_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.expected_group_address,
                u_shell.u_plan6_huginn_hbm_shell.gen_hbm_weight_path.u_weight_path.u_weight_adapter.output_mask_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.expected_group_mask,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.parallel_group_valid,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.writable_words,
                u_shell.u_plan6_huginn_hbm_shell.hbm_pool_load_valid,
                u_shell.u_plan6_huginn_hbm_shell.hbm_pool_load_ready);
            $fatal(1, "FlightCore run failed or timed out: status=0x%08x", status_word);
        end
        u_axil.read_reg(12'h008, cycles_low);
        u_axil.read_reg(12'h00c, cycles_high);
        u_axil.read_reg(12'h010, output_chunks);
        u_axil.read_reg(12'h014, output_digest);
        u_axil.read_reg(12'h018, final_context);
        shell_cycles = {cycles_high, cycles_low};
        elapsed_ms = real'(shell_cycles) * 1000.0 / real'(CORE_HZ);
        $display("U280_CYCLE_E2E_RESULT model=Huginn-3.5B scope=recurrent_core blocks=4 recurrences=%0d context=%0d max_context=%0d status=0x%08x shell_cycles=%0d core_clock_hz=%0d latency_ms=%0.6f hbm_ring_records=%0d core_timing_candidate=%0d core_128trit_candidate=%0d pool_read_parallel_slots=%0d gamma_parallel_load=%0d attention_parallel_candidate=%0d attention_parallel_heads=%0d attention_quant_stream_pipeline=%0d adapter_static_reuse=%0d residual_norm_fusion=%0d residual_norm_tile_preload=%0d norm_gamma_from_host=%0d output_chunks=%0d output_digest=0x%08x hbm_ar_bursts=%0d hbm_r_beats=%0d hbm_bytes=%0d gamma_r_beats=%0d hbm_protocol_error=0x%08x",
            RECURRENCES, final_context, MAX_CONTEXT, status_word, shell_cycles, CORE_HZ, elapsed_ms,
            HBM_RING_RECORDS,
            CORE_TIMING_CANDIDATE, CORE_128TRIT_CANDIDATE, POOL_READ_PARALLEL_SLOTS,
            GAMMA_PARALLEL_LOAD, ATTENTION_PARALLEL_CANDIDATE,
            ATTENTION_PARALLEL_HEADS,
            ATTENTION_QUANT_STREAM_PIPELINE,
            ADAPTER_STATIC_REUSE, RESIDUAL_NORM_FUSION, RESIDUAL_NORM_TILE_PRELOAD,
            NORM_GAMMA_FROM_HOST,
            output_chunks, output_digest, hbm_ar_count, hbm_r_beats,
            hbm_r_beats * 64'd32, gamma_read_beats, hbm_protocol_error);
        for (integer lane = 0; lane < HBM_PCS; lane = lane + 1)
            $display("U280_CYCLE_E2E_PC pc=%0d r_beats=%0d", lane, hbm_pc_beats[lane]);
        profile_sum = 0;
        for (integer category = 0; category < 8; category = category + 1) begin
            profile_sum = profile_sum + exclusive_cycles[category];
            $display("U280_CYCLE_E2E_BREAKDOWN category=%0d exclusive_cycles=%0d raw_cycles=%0d",
                category, exclusive_cycles[category], raw_busy_cycles[category]);
        end
        for (integer state_index = 0; state_index < 14; state_index = state_index + 1)
            $display("U280_CYCLE_E2E_SHELL_STATE state=%0d cycles=%0d",
                state_index, shell_state_cycles[state_index]);
        for (integer length_index = 0; length_index < 16; length_index = length_index + 1)
            if (hbm_burst_count[length_index] != 0)
                $display("U280_CYCLE_E2E_BURSTS beats_per_burst=%0d count=%0d",
                    length_index + 1, hbm_burst_count[length_index]);
        for (integer pc = 0; pc < HBM_PCS; pc = pc + 1)
            $display("U280_CYCLE_E2E_OUTSTANDING pc=%0d peak=%0d remaining=%0d",
                pc, hbm_outstanding_peak[pc], hbm_outstanding[pc]);
        $display("U280_CYCLE_E2E_MEMORY scheduling_only=1 zero_payload=1 pool_lanes=%0d pool_write_groups=%0d pool_valid_records=%0d adapter_peak_records=%0d prefetch_starts=%0d ar_stall_lane_cycles=%0d r_stall_lane_cycles=%0d offered_beats=%0d requested_beats=%0d received_beats=%0d hbm_dma_active_cycles=%0d scoreboard_error=0x%08x profile_cycles=%0d profile_sum=%0d",
            HBM_POOL_LANES, pool_write_groups, pool_write_records, adapter_peak_occupancy, prefetch_starts,
            hbm_ar_stall_lane_cycles, hbm_r_stall_lane_cycles, hbm_offered_beats,
            hbm_requested_beats, hbm_r_beats, hbm_active_cycles, hbm_scoreboard_error,
            profile_cycles, profile_sum);
        if (profile_cycles != shell_cycles || profile_sum != shell_cycles)
            $fatal(1, "Exclusive cycle counters do not sum to shell cycle count");
        if (hbm_requested_beats != hbm_r_beats || hbm_scoreboard_error != 0)
            $fatal(1, "HBM accepted-request/response scoreboard mismatch");
        error_mask = 64'(hbm_protocol_error);
        if (status_word[2] || error_mask != 0 || hbm_r_beats == 0)
            $fatal(1, "FlightCore status or HBM AXI protocol error");
        $display("U280_CYCLE_E2E_TEST_PASS");
        $fflush();
        $finish;
    end

    initial begin
        wait (run_started);
        forever begin
            #POLL_INTERVAL_PS;
            $display("U280_CYCLE_E2E_HEARTBEAT sim_ns=%0.3f status=0x%08x shell_state=%0d command=%0d stage=%0d block=%0d recurrence=%0d context=%0d pool_busy=%0d pool_groups=%0d/%0d hbm_ar=%0d hbm_r_beats=%0d",
                $realtime / 1000.0, u_shell.u_plan6_huginn_hbm_shell.status_word,
                u_shell.u_plan6_huginn_hbm_shell.state_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_command_id,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_command_stage,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_block_index,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.scheduler_recurrence_index,
                u_shell.u_plan6_huginn_hbm_shell.context_tokens_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.load_busy,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.group_count_q,
                u_shell.u_plan6_huginn_hbm_shell.u_recurrent_core.u_weight_memory.u_primary_pool.requested_groups,
                hbm_ar_count, hbm_r_beats);
            $fflush();
        end
    end

    initial begin
        #TIMEOUT_PS;
        $fatal(1, "U280 FlightCore cycle-model E2E timeout");
    end
    `undef SHELL
    `undef CORE
    `undef PATH
endmodule
