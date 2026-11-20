`timescale 1ns / 1ps

module rtwsr_top #(
    parameter int P_CH = 32,
    parameter int C_OUT = 1760,
    parameter int K = 17920,
    parameter int ROUNDS = 32,
    parameter int ACT_W = 8,
    parameter int ACC_W = 24,
    parameter int WINDOW_COUNT = (K + 255) / 256,
    parameter int TILE_COUNT = (C_OUT + P_CH - 1) / P_CH,
    parameter int WINDOW_WIDTH = (WINDOW_COUNT <= 1) ? 1 : $clog2(WINDOW_COUNT),
    parameter int TILE_WIDTH = (TILE_COUNT <= 1) ? 1 : $clog2(TILE_COUNT),
    parameter int ROUND_WIDTH = (ROUNDS <= 1) ? 1 : $clog2(ROUNDS),
    parameter int CHANNEL_WIDTH = (C_OUT <= 1) ? 1 : $clog2(C_OUT),
    parameter int BANK_GROUPS = P_CH / 4,
    parameter int BANK_WORDS = TILE_COUNT * WINDOW_COUNT * 4,
    parameter int BANK_DEPTH = 2 ** $clog2(BANK_WORDS),
    parameter int BANK_ADDR_WIDTH = $clog2(BANK_DEPTH)
)(
    input  logic                              clk,
    input  logic                              rst_n,

    input  logic                              weight_load_valid,
    output logic                              weight_load_ready,
    input  logic [CHANNEL_WIDTH-1:0]          weight_load_channel,
    input  logic [WINDOW_WIDTH-1:0]            weight_load_window,
    input  logic [511:0]                      weight_load_data,

    input  logic                              round_config_valid,
    output logic                              round_config_ready,
    input  logic [P_CH*16-1:0]                round_gamma_fp16,
    input  logic [15:0]                       round_activation_scale_fp16,

    input  logic                              activation_valid,
    output logic                              activation_ready,
    input  logic [256*ACT_W-1:0]              activation_window,

    output logic                              tile_result_valid,
    output logic [TILE_WIDTH-1:0]             output_tile_index,
    output logic [P_CH*32-1:0]                tile_result_q12,
    output logic                              round_result_valid,
    output logic [ROUND_WIDTH-1:0]            round_index,
    output logic                              done
);
    localparam logic [WINDOW_WIDTH-1:0] LAST_WINDOW = WINDOW_WIDTH'(WINDOW_COUNT - 1);
    localparam logic [TILE_WIDTH-1:0] LAST_TILE = TILE_WIDTH'(TILE_COUNT - 1);

    typedef enum logic [2:0] {
        WAIT_CONFIG,
        WAIT_WINDOW,
        WAIT_INITIAL_READ,
        PROCESS_WINDOW,
        WAIT_RESULT,
        ADVANCE_TILE,
        ADVANCE_ROUND,
        FINISHED
    } state_t;

    state_t state;
    logic [ROUND_WIDTH-1:0] round_counter;
    logic [TILE_WIDTH-1:0] tile_counter;
    logic [WINDOW_WIDTH-1:0] window_index;
    logic active_weight_locked;
    logic [TILE_COUNT-1:0] released_weight_tiles;
    logic load_tile_released;
    logic [1:0] subchunk_index;
    logic [P_CH*16-1:0] gamma_q;
    logic [15:0] activation_scale_q;
    logic [256*ACT_W-1:0] activation_q;
    logic [P_CH*512-1:0] weight_words_q;
    logic [P_CH*512-1:0] prefetch_words_q;
    logic [TILE_WIDTH-1:0] prefetch_tile_q;
    logic [WINDOW_WIDTH-1:0] prefetch_window_q;
    logic prefetch_valid;
    logic fetch_busy;
    logic [2:0] fetch_issue_count;
    logic [2:0] fetch_return_count;
    logic [1:0] return_slot_q;

    logic [BANK_GROUPS-1:0] bank_rd_valid;
    logic [BANK_GROUPS*512-1:0] bank_rd_data;
    logic bank_rd_en;
    logic [BANK_ADDR_WIDTH-1:0] bank_rd_addr;
    logic launch_next_fetch;
    logic [P_CH*512-1:0] prefetch_words_with_return;
    logic fetch_complete_now;
    logic prefetch_ready;
    logic [TILE_WIDTH-1:0] next_fetch_tile;
    logic [WINDOW_WIDTH-1:0] next_fetch_window;
    logic next_fetch_exists;

    logic array_valid;
    logic array_first_subchunk;
    logic array_last_subchunk;
    logic [1:0] array_subchunk_index;
    logic [P_CH*512-1:0] array_weight_words;
    logic [256*ACT_W-1:0] array_activation_window;
    logic [P_CH-1:0] array_row_done;
    logic [P_CH*32-1:0] array_result_q12;

    always_comb begin
        load_tile_released = 1'b0;
        if ((int'(weight_load_channel) / P_CH) < TILE_COUNT)
            load_tile_released = released_weight_tiles[int'(weight_load_channel) / P_CH];
        weight_load_ready = !active_weight_locked || (state == FINISHED) ||
                            ((round_counter == ROUND_WIDTH'(ROUNDS - 1)) && load_tile_released);
        round_config_ready = ((state == WAIT_CONFIG) && !done) || (state == FINISHED);

        fetch_complete_now = fetch_busy && bank_rd_valid[0] &&
                             (fetch_return_count == 3'd3);
        prefetch_ready = prefetch_valid || fetch_complete_now;

        activation_ready = 1'b0;
        if (state == WAIT_WINDOW) begin
            if (prefetch_ready ||
                ((window_index == '0) && !fetch_busy && !prefetch_valid))
                activation_ready = 1'b1;
        end

        next_fetch_tile = tile_counter;
        next_fetch_window = window_index;
        next_fetch_exists = 1'b1;
        if (window_index != LAST_WINDOW) begin
            next_fetch_window = window_index + 1'b1;
        end else if (tile_counter != LAST_TILE) begin
            next_fetch_tile = tile_counter + 1'b1;
            next_fetch_window = '0;
        end else if (round_counter != ROUND_WIDTH'(ROUNDS - 1)) begin
            next_fetch_tile = '0;
            next_fetch_window = '0;
        end else begin
            next_fetch_exists = 1'b0;
        end

        launch_next_fetch = (state == WAIT_WINDOW) && activation_valid &&
            activation_ready && prefetch_ready && next_fetch_exists &&
            (!fetch_busy || fetch_complete_now);
        bank_rd_en = (fetch_busy && (fetch_issue_count < 3'd4)) || launch_next_fetch;
        if (launch_next_fetch)
            bank_rd_addr = BANK_ADDR_WIDTH'(
                ((int'(next_fetch_tile) * WINDOW_COUNT + int'(next_fetch_window)) * 4)
            );
        else
            bank_rd_addr = BANK_ADDR_WIDTH'(
                ((int'(prefetch_tile_q) * WINDOW_COUNT + int'(prefetch_window_q)) * 4) +
                int'(fetch_issue_count)
            );

        prefetch_words_with_return = prefetch_words_q;
        if (bank_rd_valid[0]) begin
            for (integer group_index = 0; group_index < BANK_GROUPS; group_index = group_index + 1)
                prefetch_words_with_return[
                    (group_index*4 + int'(return_slot_q))*512 +: 512
                ] = bank_rd_data[group_index*512 +: 512];
        end

        array_valid = (state == PROCESS_WINDOW) ||
                      ((state == WAIT_WINDOW) && activation_valid &&
                       activation_ready && prefetch_ready);
        array_subchunk_index = (state == WAIT_WINDOW) ? 2'b00 : subchunk_index;
        array_first_subchunk = (window_index == '0) && (array_subchunk_index == 2'b00);
        array_last_subchunk = (window_index == LAST_WINDOW) && (array_subchunk_index == 2'b11);
        array_weight_words = weight_words_q;
        array_activation_window = activation_q;
        if ((state == WAIT_WINDOW) && activation_valid && activation_ready && prefetch_ready) begin
            array_weight_words = prefetch_words_with_return;
            array_activation_window = activation_window;
        end
    end

    genvar group_index;
    generate
        for (group_index = 0; group_index < BANK_GROUPS; group_index = group_index + 1) begin : gen_weight_bank
            logic group_wr_en;

            assign group_wr_en = weight_load_valid && weight_load_ready &&
                (weight_load_channel % P_CH / 4 == group_index);

            uram_active_pool_bank #(
                .DEPTH(BANK_DEPTH),
                .ADDR_WIDTH(BANK_ADDR_WIDTH),
                .WR_ADDR_MODE(1),
                .CHANNELS_PER_TILE(P_CH),
                .WINDOW_COUNT(WINDOW_COUNT),
                .CHANNEL_WIDTH(CHANNEL_WIDTH),
                .WINDOW_WIDTH(WINDOW_WIDTH)
            ) u_active_pool_bank (
                .clk(clk),
                .wr_en(group_wr_en),
                .wr_addr('0),
                .wr_channel(weight_load_channel),
                .wr_window(weight_load_window),
                .wr_data(weight_load_data),
                .rd_en(bank_rd_en),
                .rd_addr(bank_rd_addr),
                .rd_valid(bank_rd_valid[group_index]),
                .rd_data(bank_rd_data[group_index*512 +: 512])
            );
        end
    endgenerate

    usw512_channel_array #(
        .P_CH(P_CH),
        .ACT_W(ACT_W),
        .ACC_W(ACC_W)
    ) u_channel_array (
        .clk(clk),
        .rst_n(rst_n),
        .valid_in(array_valid),
        .first_subchunk(array_first_subchunk),
        .last_subchunk(array_last_subchunk),
        .subchunk_index(array_subchunk_index),
        .usw_words(array_weight_words),
        .activation_window(array_activation_window),
        .fused_gamma_fp16(gamma_q),
        .activation_scale_fp16(activation_scale_q),
        .row_done_valid(array_row_done),
        .final_channels_q12(array_result_q12)
    );

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= WAIT_CONFIG;
            round_counter <= '0;
            tile_counter <= '0;
            window_index <= '0;
            active_weight_locked <= 1'b0;
            released_weight_tiles <= '0;
            subchunk_index <= '0;
            gamma_q <= '0;
            activation_scale_q <= '0;
            activation_q <= '0;
            weight_words_q <= '0;
            prefetch_words_q <= '0;
            prefetch_tile_q <= '0;
            prefetch_window_q <= '0;
            prefetch_valid <= 1'b0;
            fetch_busy <= 1'b0;
            fetch_issue_count <= '0;
            fetch_return_count <= '0;
            return_slot_q <= '0;
            tile_result_valid <= 1'b0;
            tile_result_q12 <= '0;
            round_result_valid <= 1'b0;
            done <= 1'b0;
        end else begin
            tile_result_valid <= 1'b0;
            round_result_valid <= 1'b0;

            if (bank_rd_en) begin
                return_slot_q <= fetch_issue_count[1:0];
                fetch_issue_count <= fetch_issue_count + 1'b1;
            end
            if (bank_rd_valid[0]) begin
                for (integer group_index = 0; group_index < BANK_GROUPS; group_index = group_index + 1)
                    prefetch_words_q[
                        (group_index*4 + int'(return_slot_q))*512 +: 512
                    ] <= bank_rd_data[group_index*512 +: 512];
                if (fetch_return_count == 3'd3) begin
                    fetch_busy <= 1'b0;
                    fetch_return_count <= '0;
                    prefetch_valid <= 1'b1;
                end else begin
                    fetch_return_count <= fetch_return_count + 1'b1;
                end
            end

            case (state)
                WAIT_CONFIG: begin
                    if (round_config_valid && round_config_ready) begin
                        gamma_q <= round_gamma_fp16;
                        activation_scale_q <= round_activation_scale_fp16;
                        if (!active_weight_locked && round_counter == '0 && tile_counter == '0)
                            released_weight_tiles <= '0;
                        active_weight_locked <= 1'b1;
                        window_index <= '0;
                        subchunk_index <= '0;
                        if (prefetch_valid &&
                            (prefetch_tile_q != tile_counter ||
                             prefetch_window_q != '0)) begin
                            prefetch_valid <= 1'b0;
                            fetch_busy <= 1'b0;
                        end
                        state <= WAIT_WINDOW;
                    end
                end

                WAIT_WINDOW: begin
                    if (activation_valid && activation_ready) begin
                        activation_q <= activation_window;
                        subchunk_index <= 2'd1;
                        if (prefetch_ready) begin
                            weight_words_q <= prefetch_words_with_return;
                            prefetch_valid <= 1'b0;
                            if (next_fetch_exists) begin
                                fetch_busy <= 1'b1;
                                fetch_issue_count <= launch_next_fetch ? 3'd1 : 3'd0;
                                fetch_return_count <= '0;
                                prefetch_tile_q <= next_fetch_tile;
                                prefetch_window_q <= next_fetch_window;
                                if (launch_next_fetch)
                                    return_slot_q <= 2'b00;
                                state <= PROCESS_WINDOW;
                            end else begin
                                state <= PROCESS_WINDOW;
                            end
                        end else begin
                            if (!fetch_busy) begin
                                fetch_busy <= 1'b1;
                                fetch_issue_count <= '0;
                                fetch_return_count <= '0;
                                prefetch_tile_q <= tile_counter;
                                prefetch_window_q <= window_index;
                            end
                            state <= WAIT_INITIAL_READ;
                        end
                    end
                end

                WAIT_INITIAL_READ: begin
                    if (fetch_complete_now) begin
                        weight_words_q <= prefetch_words_with_return;
                        prefetch_valid <= 1'b0;
                        subchunk_index <= '0;
                        if (next_fetch_exists) begin
                            fetch_busy <= 1'b1;
                            fetch_issue_count <= '0;
                            fetch_return_count <= '0;
                            prefetch_tile_q <= next_fetch_tile;
                            prefetch_window_q <= next_fetch_window;
                        end
                        state <= PROCESS_WINDOW;
                    end
                end

                PROCESS_WINDOW: begin
                    if (subchunk_index == 2'd3) begin
                        if (window_index == LAST_WINDOW) begin
                            state <= WAIT_RESULT;
                        end else begin
                            window_index <= window_index + 1'b1;
                            subchunk_index <= '0;
                            if (activation_valid && activation_ready) begin
                                activation_q <= activation_window;
                                weight_words_q <= prefetch_words_with_return;
                                prefetch_valid <= 1'b0;
                                state <= PROCESS_WINDOW;
                            end else begin
                                state <= WAIT_WINDOW;
                            end
                        end
                    end else begin
                        subchunk_index <= subchunk_index + 1'b1;
                    end
                end

                WAIT_RESULT: begin
                    if (|array_row_done) begin
`ifndef SYNTHESIS
                        if (array_row_done != {P_CH{1'b1}})
                            $error("channel completion pulses are not cycle-aligned");
`endif
                        tile_result_valid <= 1'b1;
                        tile_result_q12 <= array_result_q12;
                        if (round_counter == ROUND_WIDTH'(ROUNDS - 1))
                            released_weight_tiles[tile_counter] <= 1'b1;
                        if (tile_counter == LAST_TILE) begin
                            round_result_valid <= 1'b1;
                            if (round_counter == ROUND_WIDTH'(ROUNDS - 1)) begin
                                done <= 1'b1;
                                state <= FINISHED;
                            end else begin
                                state <= ADVANCE_ROUND;
                            end
                        end else begin
                            state <= ADVANCE_TILE;
                        end
                    end
                end

                ADVANCE_TILE: begin
                    tile_counter <= tile_counter + 1'b1;
                    window_index <= '0;
                    subchunk_index <= '0;
                    state <= WAIT_CONFIG;
                end

                ADVANCE_ROUND: begin
                    round_counter <= round_counter + 1'b1;
                    tile_counter <= '0;
                    window_index <= '0;
                    subchunk_index <= '0;
                    state <= WAIT_CONFIG;
                end

                FINISHED: begin
                    if (round_config_valid && round_config_ready) begin
                        done <= 1'b0;
                        round_counter <= '0;
                        tile_counter <= '0;
                        released_weight_tiles <= '0;
                        gamma_q <= round_gamma_fp16;
                        activation_scale_q <= round_activation_scale_fp16;
                        active_weight_locked <= 1'b1;
                        window_index <= '0;
                        subchunk_index <= '0;
                        state <= WAIT_WINDOW;
                    end
                end
                default: state <= WAIT_CONFIG;
            endcase
        end
    end

    assign output_tile_index = tile_counter;
    assign round_index = round_counter;

    initial begin
        if (P_CH != 32 || P_CH % 4 != 0)
            $error("The current channel array requires P_CH=32 and groups of four");
        if (C_OUT < 1 || K < 1 || ROUNDS < 1 || WINDOW_COUNT < 1)
            $error("C_OUT, K, and ROUNDS must be positive");
        if (BANK_DEPTH < BANK_WORDS || (2 ** BANK_ADDR_WIDTH) != BANK_DEPTH)
            $error("BANK_DEPTH must be a power of two holding all local weights");
        if (ACT_W != 8)
            $error("usw512_channel_array currently requires ACT_W=8");
    end
endmodule
