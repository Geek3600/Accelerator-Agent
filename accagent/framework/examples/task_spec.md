Design a complete board-runnable spatial accelerator for a Qwen2-style decoder-only LLM.

The target model source is Qwen2-0.5B style: 24 decoder layers, hidden_size 896, grouped-query attention
with 14 query heads and 2 KV heads, head_dim 64, RoPE, RMSNorm, and gated SiLU MLP. The first automation
target uses target_max_seq_len 16 from the model_config.

The framework must generate a Qwen spatial accelerator design package from trusted Chisel templates, elaborate
SystemVerilog, run real Vivado synthesis/implementation/bitstream generation on server 23 for the VU9P board part,
and record all tool evidence. Do not run OPT full-sequence verification as Qwen evidence, and do not claim board
runtime pass until a Qwen AXI/DDR board wrapper is connected and checked.
