# Generated SpatialAccAgent Chisel Package

This package is generated from SACG artifacts for `gpt2_deepseek_v4pro_20261020`.
It is template-constrained: files under `spatialaccagent/templates` are copied
from the trusted template library, while files under `spatialaccagent/generated`
bind model, pipeline, parameter, and board facts for this run.

Model: `gpt2`
Top wrapper: `GPT2PreLNBlock`
FPGA AXI/DDR top: `GeneratedAxiDdrTop`
Target sequence length: `16`
Clock target MHz: `0`
Bit policy: input `8`, internal `8`, output `8`

Pipeline stages:
- 0: stage_00_layer_norm_1 op=layer_norm_1 template=norm
- 1: stage_01_self_attention op=self_attention template=attention
- 2: stage_02_residual_add_1 op=residual_add_1 template=residual
- 3: stage_03_layer_norm_2 op=layer_norm_2 template=norm
- 4: stage_04_mlp_fc op=mlp_fc template=ffn
- 5: stage_05_activation op=activation template=activation
- 6: stage_06_mlp_proj op=mlp_proj template=ffn
- 7: stage_07_residual_add_2 op=residual_add_2 template=residual

Run:

```bash
sbt "runMain spatialaccagent.generated.GeneratedContractCheck"
sbt "runMain spatialaccagent.generated.ElaborateGeneratedAccelerator"
sbt "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop"
sbt "runMain spatialaccagent.generated.ElaborateGeneratedAcceleratorVivado"
sbt "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado"
```

This package contains the accelerator compute top and the FPGA-facing AXI/DDR
top boundary, plus generated memory/runtime manifests for later verification
and board integration stages. It does not claim DDR image, VCS, Vivado, or
board pass; those must be produced, bound, and verified by later stages. Chisel
compile/elaboration, simulation, synthesis, implementation, and board run
evidence must be attached through SACG checkers before design pass can be
claimed.
