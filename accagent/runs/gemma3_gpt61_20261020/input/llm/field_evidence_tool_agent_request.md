<agent>
field_evidence_tool_agent
</agent>

<task>
Act as the source-evidence engineer for the tool input domain. Read the complete supplied domain_materials_text and extract its supported fields; candidate excerpts are optional hints, not a limit on the evidence you can extract.
</task>

<rules>
1. Deterministic regex candidates are hints only, not ground truth.
2. Accept a field only when the cited excerpt semantically supports it.
3. Each evidence item must cite source, chunk_id when available, and a short excerpt from domain_materials_text or its candidate summary.
4. Reject false positives, stale sample/scaffold interfaces, generic paths, or contradicted values.
5. Extract every supported operational host, executable, scope and environment field in tool documents. Omit a field only if the complete supplied material does not establish it; never infer tool availability without the later real probes.
</rules>

<material_corpus_summary>
{
  "complete_domain_material_is_supplied": true,
  "domain": "tool",
  "material_chars": 2241
}
</material_corpus_summary>

<domain_materials_text>
### chunk:tools:000001 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/remote_server.md offset:0-64
```text
# 远程服务器
* 可使用ssh hyyuan@10.12.133.23命令连接
* 已经配置好免密登录

# 使用规范和限制

```

### chunk:tools:000002 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md offset:0-977
```text
# VCS工具位置和使用方式

* 所在机器：hyyuan@10.12.133.23
* 用途：功能验证阶段，用于编译和运行 SystemVerilog testbench。
* 可执行文件：/home/EDA/Software/EDATools/Synopsys/VCSALL/v202206-OLD/bin/vcs
* 版本探测命令：
  * `VCS_TARGET_ARCH=linux64 /home/EDA/Software/EDATools/Synopsys/VCSALL/v202206-OLD/bin/vcs -ID`
* Stage 0 必须通过 SSH 实际探测该命令可调用，不能只因为文档里写了路径就认为 VCS 可用。
* 运行 VCS 时需要设置：
  * `VCS_TARGET_ARCH=linux64`
  * `REMOTE_HOST=hyyuan@10.12.133.23`
  * `REMOTE_VCS_HOME=/home/EDA/Software/EDATools/Synopsys/VCSALL/v202206-OLD`
  * 工具环境 `HOME=/home/hyyuan/workspace/spatialaccagent_artifacts/toolchains/vcs202206_vivado2021_1/home`，其中的 `synopsys_sim.setup` 绑定与 VCS 2022.06 匹配的 Vivado 2021.1 仿真库；不得混用用户默认 HOME 下的 2021.09 预编译库。
* 2026-10-16 已确认 VCS T-2022.06_Full64 完成实际生成设计的编译与链接；旧 2021.09 对相同源码出现 VHDL code-generation native assertion。已有通过记录不因工具材料更新而重复运行。
* 当前框架已有的 Qwen VCS smoke 脚本：
  * `scripts/verification/run_qwen_generated_vcs_smoke_23.sh`
* VCS 主要用于真实功能验证；如果后续用户改用 Verilator，Stage 0 也必须从工具材料中提取 Verilator 的位置和限制。

```

### chunk:tools:000003 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/verilator.md offset:0-62
```text
# Verilator工具位置
* verilator不在远程服务器，而是在本地
* verilator主要用于功能验证阶段
```

### chunk:tools:000004 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md offset:0-539
```text
# Vivado工具位置和使用方式

* 所在机器：hyyuan@10.12.133.23
* 用途：综合、布局布线、生成 bitstream。
* 可执行文件：/home/EDA/Xilinx/Vivado/2021.1/bin/vivado
* 版本探测命令：
  * `/home/EDA/Xilinx/Vivado/2021.1/bin/vivado -version`
* 已确认版本：Vivado v2021.1。
* Stage 0 必须通过 SSH 实际探测该命令可调用，不能只因为文档里写了路径就认为 Vivado 可用。
* 运行 Vivado 时需要设置：
  * `REMOTE_HOST=hyyuan@10.12.133.23`
  * `VIVADO_BIN=/home/EDA/Xilinx/Vivado/2021.1/bin/vivado`
* 当前框架已有的 Qwen Vivado 脚本：
  * `scripts/synthesis/run_qwen_generated_bitstream_23.sh`
* Vivado 是最终综合、实现和 bitstream evidence 的必选工具；缺失或探测失败时 Stage 0 必须失败。

```
</domain_materials_text>

<deterministic_regex_candidate_summary>
{
  "policy": {
    "candidate_only": true,
    "critical_fields_must_match_evidence_when_present": true,
    "llm_output_is_not_accepted_as_evidence_without_source": true,
    "llm_semantic_confirmation_required": true,
    "regex_is_not_semantic_ground_truth": true
  },
  "schema_version": "spatialaccagent.field_evidence_summary.v0",
  "selected_fields": [
    {
      "count": 4,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "me/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md offset:0-977 ```text # VCS\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u529f\u80fd\u9a8c\u8bc1\u9636\u6bb5\uff0c\u7528\u4e8e\u7f16\u8bd1\u548c\u8fd0\u884c SystemVerilog testbench\u3002 * \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Software",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "tool.vcs.host"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "tools/vcs.md offset:0-977 ```text # VCS\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u529f\u80fd\u9a8c\u8bc1\u9636\u6bb5\uff0c\u7528\u4e8e\u7f16\u8bd1\u548c\u8fd0\u884c SystemVerilog testbench\u3002 * \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Software/EDATools/Synopsys/VCSALL/v202206-OLD/bin/vcs * \u7248\u672c\u63a2\u6d4b\u547d\u4ee4\uff1a * `VCS_TARGET_ARC",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "/home/EDA/Software/EDATools/Synopsys/VCSALL/v202206-OLD/bin/vcs"
        }
      ],
      "field": "tool.vcs.executable"
    },
    {
      "count": 4,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "me/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md offset:0-977 ```text # VCS\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u529f\u80fd\u9a8c\u8bc1\u9636\u6bb5\uff0c\u7528\u4e8e\u7f16\u8bd1\u548c\u8fd0\u884c SystemVerilog testbench\u3002 * \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Software",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "tool.vivado.host"
    },
    {
      "count": 3,
      "evidence": [
        {
          "chunk_id": "tools:000004",
          "excerpt": "t_materials/tools/vivado.md offset:0-539 ```text # Vivado\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u7efc\u5408\u3001\u5e03\u5c40\u5e03\u7ebf\u3001\u751f\u6210 bitstream\u3002 * \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Xilinx/Vivado/2021.1/bin/vivado * \u7248\u672c\u63a2\u6d4b\u547d\u4ee4\uff1a * `/home/EDA/Xilinx/Vivado/2021.1/bin/v",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md",
          "value": "/home/EDA/Xilinx/Vivado/2021.1/bin/vivado"
        }
      ],
      "field": "tool.vivado.executable"
    }
  ]
}
</deterministic_regex_candidate_summary>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "evidence": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "chunk_id": {
            "type": [
              "string",
              "null"
            ]
          },
          "confidence": {
            "type": [
              "string",
              "number",
              "null"
            ]
          },
          "excerpt": {
            "type": "string"
          },
          "field": {
            "type": "string"
          },
          "reason": {
            "type": [
              "string",
              "null"
            ]
          },
          "source": {
            "type": [
              "string",
              "null"
            ]
          },
          "value": {}
        },
        "required": [
          "field",
          "value",
          "source",
          "chunk_id",
          "excerpt"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "policy": {
      "additionalProperties": true,
      "type": "object"
    },
    "schema_version": {
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "policy",
    "evidence"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
