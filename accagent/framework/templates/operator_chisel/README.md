# Chisel Operator Templates

These files are simplified, reusable Chisel operator templates distilled from
the OPT case-study experience. They are a standalone template library and do
not depend on the original OPT accelerator source tree at runtime.

They are not direct copies of the current accelerator modules. The extraction
keeps the common operator structure:

- packed valid/ready/st/last/addr streams;
- vector normalization shell;
- sequential tiled linear MAC;
- QKV projection and stream reorder;
- RoPE/QK norm shells for Q/K stream transformation;
- MHA attention shell preserving QKV/V stream structure;
- row-level softmax shell with mask/causal/sliding-window constraints;
- KV cache and attention mask shells;
- activation and elementwise multiply shells;
- residual add;
- dense and gated FFN;
- OPT/GPT2/LLaMA/Gemma-style decoder block wiring.

Current simplifications are intentional:

- board/runtime/debug ports are removed;
- current OPT constants are parameters;
- the linear template uses a sequential tiled MAC instead of the optimized
  double-buffered psum-bank implementation;
- the attention template preserves stream structure and V aggregation first;
- `Softmax.scala` currently uses a masked max-onehot approximation. It keeps the
  stream, mask, causal, and sliding-window boundary explicit; exact exp/sum
  normalization should replace only this arithmetic core later.
- `RMSNorm.scala` behavior is currently represented by `RMSNorm` in
  `Norm.scala`; it preserves the no-mean/no-beta template boundary, but the
  arithmetic core is still a lightweight quantized pass-through.
- `RoPE.scala`, `QKNorm`, activation variants, and gated MLP preserve placement,
  stream shape, and template-binding constraints first. Their math cores are
  minimal placeholders unless explicitly refined later.
- `DecoderBlock.scala` is a wiring sketch that exposes the operator order. A
  production generator should lift all weight/scale/mask ports to the wrapper
  instead of tying them to zero as the sketch does.
- exact FP32 LayerNorm/Softmax arithmetic is left to later numeric template
  refinement.
