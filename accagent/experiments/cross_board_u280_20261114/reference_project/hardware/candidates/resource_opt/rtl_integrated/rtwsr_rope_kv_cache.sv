`timescale 1ns / 1ps

module rtwsr_rope_kv_cache #(
    parameter int HEAD_DIM = 128,
    parameter int MAX_CONTEXT = 2048,
    parameter int DATA_W = 16,
    parameter int TRIG_W = 16,
    parameter bit EXTERNAL_CACHE = 1'b0,
    parameter bit EXTERNAL_ROTATION = 1'b0,
    parameter int LANES = 128,
    parameter int TOKEN_INDEX_W = (MAX_CONTEXT <= 1) ? 1 : $clog2(MAX_CONTEXT),
    parameter int CONTEXT_COUNT_W = $clog2(MAX_CONTEXT + 1),
    parameter int CHUNK_COUNT = (HEAD_DIM + LANES - 1) / LANES,
    parameter int CHUNK_INDEX_W = (CHUNK_COUNT <= 1) ? 1 : $clog2(CHUNK_COUNT),
    parameter int VECTOR_WIDTH = HEAD_DIM * DATA_W,
    parameter int TRIG_VECTOR_WIDTH = HEAD_DIM * TRIG_W,
    parameter int CHUNK_WIDTH = LANES * DATA_W
)(
    input  logic                           clk,
    input  logic                           rst_n,
    input  logic                           start,
    input  logic [TOKEN_INDEX_W-1:0]       write_position,
    input  logic [CONTEXT_COUNT_W-1:0]     active_context_tokens,
    input  logic [TOKEN_INDEX_W-1:0]       window_start,
    input  logic [VECTOR_WIDTH-1:0]        query_q4_12,
    input  logic [VECTOR_WIDTH-1:0]        key_q4_12,
    input  logic [VECTOR_WIDTH-1:0]        value_q4_12,
    input  logic [VECTOR_WIDTH-1:0]        query_rotated_override,
    input  logic [VECTOR_WIDTH-1:0]        key_rotated_override,
    input  logic [TRIG_VECTOR_WIDTH-1:0]   rope_sin_q1_15,
    input  logic [TRIG_VECTOR_WIDTH-1:0]   rope_cos_q1_15,
    output logic                           ready,
    output logic                           query_valid,
    output logic [VECTOR_WIDTH-1:0]        query_rotated_q4_12,
    input  logic                           kv_ready,
    output logic                           kv_valid,
    output logic [TOKEN_INDEX_W-1:0]       kv_token_index,
    output logic [CHUNK_INDEX_W-1:0]       kv_chunk_index,
    output logic [CHUNK_WIDTH-1:0]         kv_key_chunk_q4_12,
    output logic [CHUNK_WIDTH-1:0]         kv_value_chunk_q4_12,
    output logic                           kv_last,
    output logic                           cache_load_ready,
    input  logic                           cache_load_valid,
    input  logic [TOKEN_INDEX_W-1:0]       cache_load_index,
    input  logic [VECTOR_WIDTH-1:0]        cache_load_key_q4_12,
    input  logic [VECTOR_WIDTH-1:0]        cache_load_value_q4_12,
    output logic                           cache_read_request,
    input  logic                           cache_read_request_ready,
    output logic [TOKEN_INDEX_W-1:0]       cache_read_index,
    output logic                           busy,
    output logic                           done,
    output logic                           protocol_error
);
    typedef enum logic [2:0] {
        IDLE,
        ROTATE_WRITE,
        STREAM_READ,
        STREAM_REQUEST,
        STREAM_WAIT,
        STREAM_OUTPUT
    } state_t;
    state_t state_q;

    (* ram_style = "block" *) logic [VECTOR_WIDTH-1:0] key_cache [0:MAX_CONTEXT-1];
    (* ram_style = "block" *) logic [VECTOR_WIDTH-1:0] value_cache [0:MAX_CONTEXT-1];

    logic [VECTOR_WIDTH-1:0] query_q;
    logic [VECTOR_WIDTH-1:0] key_q;
    logic [VECTOR_WIDTH-1:0] value_q;
    logic [TRIG_VECTOR_WIDTH-1:0] rope_sin_q;
    logic [TRIG_VECTOR_WIDTH-1:0] rope_cos_q;
    logic [TOKEN_INDEX_W-1:0] write_position_q;
    logic [TOKEN_INDEX_W-1:0] stream_token_q;
    logic [TOKEN_INDEX_W-1:0] stream_end_q;
    logic [CHUNK_INDEX_W-1:0] stream_chunk_q;
    logic [TOKEN_INDEX_W-1:0] kv_token_q;
    logic [CHUNK_INDEX_W-1:0] kv_chunk_q;
    logic [VECTOR_WIDTH-1:0] key_read_vector_q;
    logic [VECTOR_WIDTH-1:0] value_read_vector_q;
    logic [VECTOR_WIDTH-1:0] current_key_q;
    logic [VECTOR_WIDTH-1:0] current_value_q;
    logic protocol_error_q;

    logic [VECTOR_WIDTH-1:0] rotated_query;
    logic [VECTOR_WIDTH-1:0] rotated_key;

    function automatic logic signed [DATA_W-1:0] rotate_fixed(
        input logic signed [DATA_W-1:0] value,
        input logic signed [DATA_W-1:0] paired_value,
        input logic signed [TRIG_W-1:0] cosine,
        input logic signed [TRIG_W-1:0] sine
    );
        logic signed [DATA_W+TRIG_W:0] product_a;
        logic signed [DATA_W+TRIG_W:0] product_b;
        logic signed [DATA_W+TRIG_W+1:0] sum;
        logic signed [DATA_W+TRIG_W+1:0] shifted;
        begin
            product_a = value * cosine;
            product_b = paired_value * sine;
            sum = product_a + product_b;
            shifted = sum >>> 15;
            if (shifted > 32767)
                rotate_fixed = 16'sd32767;
            else if (shifted < -32768)
                rotate_fixed = -16'sd32768;
            else
                rotate_fixed = shifted[DATA_W-1:0];
        end
    endfunction

    always_comb begin
        integer dimension;
        integer paired_dimension;
        logic signed [DATA_W-1:0] query_value;
        logic signed [DATA_W-1:0] query_paired;
        logic signed [DATA_W-1:0] key_value;
        logic signed [DATA_W-1:0] key_paired;
        logic signed [TRIG_W-1:0] cosine;
        logic signed [TRIG_W-1:0] sine;

        rotated_query = '0;
        rotated_key = '0;
        query_value = '0;
        query_paired = '0;
        key_value = '0;
        key_paired = '0;
        cosine = '0;
        sine = '0;
        for (dimension = 0; dimension < HEAD_DIM; dimension = dimension + 1) begin
            paired_dimension = (dimension < HEAD_DIM / 2) ? dimension + HEAD_DIM / 2 : dimension - HEAD_DIM / 2;
            query_value = $signed(query_q[dimension*DATA_W +: DATA_W]);
            query_paired = $signed(query_q[paired_dimension*DATA_W +: DATA_W]);
            key_value = $signed(key_q[dimension*DATA_W +: DATA_W]);
            key_paired = $signed(key_q[paired_dimension*DATA_W +: DATA_W]);
            cosine = $signed(rope_cos_q[dimension*TRIG_W +: TRIG_W]);
            sine = $signed(rope_sin_q[dimension*TRIG_W +: TRIG_W]);
            if (dimension < HEAD_DIM / 2) begin
                rotated_query[dimension*DATA_W +: DATA_W] = rotate_fixed(query_value, -query_paired, cosine, sine);
                rotated_key[dimension*DATA_W +: DATA_W] = rotate_fixed(key_value, -key_paired, cosine, sine);
            end else begin
                rotated_query[dimension*DATA_W +: DATA_W] = rotate_fixed(query_value, query_paired, cosine, sine);
                rotated_key[dimension*DATA_W +: DATA_W] = rotate_fixed(key_value, key_paired, cosine, sine);
            end
        end
    end


    assign ready = (state_q == IDLE);
    assign cache_load_ready = EXTERNAL_CACHE ? (state_q == STREAM_WAIT) : (state_q == IDLE);
    assign cache_read_request = EXTERNAL_CACHE && (state_q == STREAM_REQUEST);
    assign cache_read_index = stream_token_q;
    assign query_valid = (state_q == ROTATE_WRITE);
    assign query_rotated_q4_12 = EXTERNAL_ROTATION ? query_rotated_override : rotated_query;
    assign kv_valid = (state_q == STREAM_OUTPUT);
    assign kv_token_index = kv_token_q;
    assign kv_chunk_index = kv_chunk_q;
    always_comb begin
        integer lane;
        integer dimension;
        kv_key_chunk_q4_12 = '0;
        kv_value_chunk_q4_12 = '0;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            dimension = int'(stream_chunk_q) * LANES + lane;
            if (dimension < HEAD_DIM) begin
                kv_key_chunk_q4_12[lane*DATA_W +: DATA_W] =
                    key_read_vector_q[dimension*DATA_W +: DATA_W];
                kv_value_chunk_q4_12[lane*DATA_W +: DATA_W] =
                    value_read_vector_q[dimension*DATA_W +: DATA_W];
            end
        end
    end
    assign kv_last = kv_valid && (kv_token_q == stream_end_q) &&
                     (kv_chunk_q == CHUNK_INDEX_W'(CHUNK_COUNT - 1));
    assign busy = (state_q != IDLE);
    assign protocol_error = protocol_error_q;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_q <= IDLE;
            query_q <= '0;
            key_q <= '0;
            value_q <= '0;
            rope_sin_q <= '0;
            rope_cos_q <= '0;
            write_position_q <= '0;
            stream_token_q <= '0;
            stream_end_q <= '0;
            stream_chunk_q <= '0;
            kv_token_q <= '0;
            kv_chunk_q <= '0;
            key_read_vector_q <= '0;
            value_read_vector_q <= '0;
            current_key_q <= '0;
            current_value_q <= '0;
            protocol_error_q <= 1'b0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            if (!EXTERNAL_CACHE && cache_load_valid && cache_load_ready) begin
                key_cache[cache_load_index] <= cache_load_key_q4_12;
                value_cache[cache_load_index] <= cache_load_value_q4_12;
            end

            if (start && ready) begin
                if (int'(write_position) >= MAX_CONTEXT || active_context_tokens == 0 ||
                    int'(active_context_tokens) > MAX_CONTEXT || int'(window_start) >= int'(active_context_tokens) ||
                    int'(write_position) >= int'(active_context_tokens)) begin
                    protocol_error_q <= 1'b1;
                end else begin
                    query_q <= query_q4_12;
                    key_q <= key_q4_12;
                    value_q <= value_q4_12;
                    rope_sin_q <= rope_sin_q1_15;
                    rope_cos_q <= rope_cos_q1_15;
                    write_position_q <= write_position;
                    stream_token_q <= window_start;
                    stream_end_q <= TOKEN_INDEX_W'(active_context_tokens - 1'b1);
                    stream_chunk_q <= '0;
                    protocol_error_q <= 1'b0;
                    state_q <= ROTATE_WRITE;
                end
            end else begin
                case (state_q)
                    ROTATE_WRITE: begin
                        current_key_q <= EXTERNAL_ROTATION ? key_rotated_override : rotated_key;
                        current_value_q <= value_q;
                        if (!EXTERNAL_CACHE) begin
                            key_cache[write_position_q] <= rotated_key;
                            value_cache[write_position_q] <= value_q;
                        end
                        state_q <= STREAM_READ;
                    end
                    STREAM_READ: begin
                        if (EXTERNAL_CACHE && stream_token_q != write_position_q) begin
                            state_q <= STREAM_REQUEST;
                        end else begin
                            if (EXTERNAL_CACHE) begin
                                key_read_vector_q <= current_key_q;
                                value_read_vector_q <= current_value_q;
                            end else begin
                                key_read_vector_q <= key_cache[stream_token_q];
                                value_read_vector_q <= value_cache[stream_token_q];
                            end
                            kv_token_q <= stream_token_q;
                            kv_chunk_q <= stream_chunk_q;
                            state_q <= STREAM_OUTPUT;
                        end
                    end
                    STREAM_REQUEST: begin
                        if (cache_read_request_ready)
                            state_q <= STREAM_WAIT;
                    end
                    STREAM_WAIT: begin
                        if (cache_load_valid) begin
                            if (cache_load_index != stream_token_q) begin
                                protocol_error_q <= 1'b1;
                            end else begin
                                key_read_vector_q <= cache_load_key_q4_12;
                                value_read_vector_q <= cache_load_value_q4_12;
                                kv_token_q <= stream_token_q;
                                kv_chunk_q <= stream_chunk_q;
                                state_q <= STREAM_OUTPUT;
                            end
                        end
                    end
                    STREAM_OUTPUT: begin
                        if (kv_ready) begin
                            if (stream_chunk_q == CHUNK_INDEX_W'(CHUNK_COUNT - 1)) begin
                                if (stream_token_q == stream_end_q) begin
                                    state_q <= IDLE;
                                    done <= 1'b1;
                                end else begin
                                    stream_token_q <= stream_token_q + 1'b1;
                                    stream_chunk_q <= '0;
                                    state_q <= STREAM_READ;
                                end
                            end else begin
                                stream_chunk_q <= stream_chunk_q + 1'b1;
                                state_q <= STREAM_READ;
                            end
                        end
                    end
                    default: state_q <= IDLE;
                endcase
            end
        end
    end

    initial begin
        if (HEAD_DIM < 2 || (HEAD_DIM % 2) != 0 || LANES != 128 || DATA_W != 16 || TRIG_W != 16 || MAX_CONTEXT < 2048)
            $error("Plan 6 RoPE/KV cache requires even head dimension, 128 lanes, 16-bit data/trig, context >= 2048");
    end
endmodule

module rtwsr_rope_rotation_shared #(
    parameter int HEAD_DIM = 96,
    parameter int DATA_W = 16,
    parameter int TRIG_W = 16,
    parameter int VECTOR_WIDTH = HEAD_DIM * DATA_W
)(
    input  logic [VECTOR_WIDTH-1:0] query_q4_12,
    input  logic [VECTOR_WIDTH-1:0] key_q4_12,
    input  logic [HEAD_DIM*TRIG_W-1:0] rope_sin_q1_15,
    input  logic [HEAD_DIM*TRIG_W-1:0] rope_cos_q1_15,
    output logic [VECTOR_WIDTH-1:0] query_rotated_q4_12,
    output logic [VECTOR_WIDTH-1:0] key_rotated_q4_12
);
    function automatic logic signed [DATA_W-1:0] rotate_fixed(
        input logic signed [DATA_W-1:0] value,
        input logic signed [DATA_W-1:0] paired_value,
        input logic signed [TRIG_W-1:0] cosine,
        input logic signed [TRIG_W-1:0] sine
    );
        logic signed [DATA_W+TRIG_W:0] product_a;
        logic signed [DATA_W+TRIG_W:0] product_b;
        logic signed [DATA_W+TRIG_W+1:0] sum;
        logic signed [DATA_W+TRIG_W+1:0] shifted;
        begin
            product_a = value * cosine;
            product_b = paired_value * sine;
            sum = product_a + product_b;
            shifted = sum >>> 15;
            if (shifted > 32767)
                rotate_fixed = 16'sd32767;
            else if (shifted < -32768)
                rotate_fixed = -16'sd32768;
            else
                rotate_fixed = shifted[DATA_W-1:0];
        end
    endfunction

    always_comb begin
        integer dimension;
        integer paired_dimension;
        logic signed [DATA_W-1:0] query_value;
        logic signed [DATA_W-1:0] query_paired;
        logic signed [DATA_W-1:0] key_value;
        logic signed [DATA_W-1:0] key_paired;
        logic signed [TRIG_W-1:0] cosine;
        logic signed [TRIG_W-1:0] sine;

        query_rotated_q4_12 = '0;
        key_rotated_q4_12 = '0;
        query_value = '0;
        query_paired = '0;
        key_value = '0;
        key_paired = '0;
        cosine = '0;
        sine = '0;
        for (dimension = 0; dimension < HEAD_DIM; dimension++) begin
            paired_dimension = (dimension < HEAD_DIM / 2) ?
                               dimension + HEAD_DIM / 2 : dimension - HEAD_DIM / 2;
            query_value = $signed(query_q4_12[dimension*DATA_W +: DATA_W]);
            query_paired = $signed(query_q4_12[paired_dimension*DATA_W +: DATA_W]);
            key_value = $signed(key_q4_12[dimension*DATA_W +: DATA_W]);
            key_paired = $signed(key_q4_12[paired_dimension*DATA_W +: DATA_W]);
            cosine = $signed(rope_cos_q1_15[dimension*TRIG_W +: TRIG_W]);
            sine = $signed(rope_sin_q1_15[dimension*TRIG_W +: TRIG_W]);
            if (dimension < HEAD_DIM / 2) begin
                query_rotated_q4_12[dimension*DATA_W +: DATA_W] =
                    rotate_fixed(query_value, -query_paired, cosine, sine);
                key_rotated_q4_12[dimension*DATA_W +: DATA_W] =
                    rotate_fixed(key_value, -key_paired, cosine, sine);
            end else begin
                query_rotated_q4_12[dimension*DATA_W +: DATA_W] =
                    rotate_fixed(query_value, query_paired, cosine, sine);
                key_rotated_q4_12[dimension*DATA_W +: DATA_W] =
                    rotate_fixed(key_value, key_paired, cosine, sine);
            end
        end
    end
endmodule
