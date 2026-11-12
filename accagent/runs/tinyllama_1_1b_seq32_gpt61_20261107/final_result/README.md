# TinyLlama-1.1B seq32 最终选定候选

- 上游GPT-6.1-Sol；W4A8；VU9P；512-bit DDR；sequence length=32。
- 综合Fmax：155.8117793705204 MHz；上一候选124.47099825740604 MHz，提升25.18%。
- 综合资源：LUT 517356、FF 186151、DSP 4046、BRAM36 394、BRAM18 28、URAM 150。
- 当前结构DSE周期39626273，估算125.82502875949633 token/s。周期不是RTL仿真实测，结构模型没有证明逐周期校准全部新增流水开销；频率不是布局布线后或上板测量。
- 已测源码归档SHA256：2e34ad2ac3df99b95d19bb28aab0399a78ad4a22415f52ded05f7088cd630227。
- source/是选定闭包的解包。archive、timing、utilization、runtime报告均绑定该候选；history.json保存16轮已有记录。
- 选定RTL已逐文件与23:36时刻的已归档single-layer compile-only证书核对，所有匹配；同目录保存当时的board compile PASS报告及多层compile-only证书。
- 按用户达到150 MHz后停止的指令，优化进程已停止。旧200 tok/s目标曾触发一个多余的后续修改，其快照在post_target_unselected目录中，不属于选定结果。
- 后续使用本目录source或该SHA归档；run/generated和当前board manifest已被未选定的后续候选更新，不能与155.81 MHz报告混用。selection.json记录全部来源和停止原因。
