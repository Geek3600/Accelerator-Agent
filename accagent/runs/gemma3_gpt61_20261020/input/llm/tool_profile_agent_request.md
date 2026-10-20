<agent>
tool_profile_agent
</agent>

<task>
Act as the EDA toolchain engineer. Extract the external EDA tool profile from current-run tool materials.
</task>

<rules>
1. Treat the tool materials directory as the complete current-run tool input.
2. Read the supplied tool_materials_text directly. A missing field in the extracted evidence summary does not mean that field is absent from the original tool documents. Extract supported host, executable, scope and environment values from those documents; never invent them.
3. Field evidence summary is the source-of-truth audit trail. Critical host, executable, environment, and script fields must match evidence when evidence exists.
4. The formal framework needs VCS or Verilator for functional verification and Vivado for synthesis, implementation, and bitstream generation.
5. Do not assume a fixed host, path, license server, version, or command unless it appears in the provided documents or target_board_profile.
6. Use common tool names such as vcs, verilator, and vivado when present.
7. Use scope=local for tools on the current machine, scope=remote for tools accessed through ssh, and null when unknown.
8. Put missing host/path/port/env/workdir fields as null or empty objects rather than inventing defaults.
9. Record limitations, license requirements, sandbox restrictions, or version constraints in constraints.
10. For remote tools, record host and any required environment variables. For Vivado, executable must identify the Vivado binary when provided.
</rules>

<tool_materials_summary>
{
  "chunk_count": 4,
  "file_count": 4,
  "files": [
    {
      "chars": 64,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/remote_server.md",
      "suffix": ".md"
    },
    {
      "chars": 977,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
      "suffix": ".md"
    },
    {
      "chars": 62,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/verilator.md",
      "suffix": ".md"
    },
    {
      "chars": 539,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md",
      "suffix": ".md"
    }
  ],
  "label": "tools",
  "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools",
  "schema_version": "spatialaccagent.material_index_summary.v0",
  "skipped": [],
  "skipped_count": 0
}
</tool_materials_summary>

<tool_materials_text>
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
</tool_materials_text>

<target_board_profile>
{
  "_llm_provenance": {
    "mode": "llm",
    "sub_agent": "board_profile_agent",
    "used_fallback": false
  },
  "board": {
    "board_name": "MIMIC Computer v6.0",
    "fpga_part": "xcvu9p_CIV-flgb2104-2-i"
  },
  "board_pass_criteria": {
    "smoke_test_script": "scripts/board/run_pyjm12_smoke.sh"
  },
  "memory_system": {
    "address_map": {
      "control_registers": "0x3000000000",
      "ddr_base": "0x2800000000",
      "output_abs": "0x28092f1000"
    },
    "axi_addr_width_bits": 37,
    "axi_clock": "c0_ddr4_s_axi_clk",
    "axi_data_bytes": 64,
    "axi_data_width_bits": 512,
    "axi_id_width_bits": 4,
    "axi_reset": "c0_ddr4_s_axi_rst_n",
    "axi_wstrb_width_bits": 64,
    "board_axi_prefix": "c0_ddr4_s_axi_*",
    "calibration_done_signal": "c0_init_calib_complete",
    "core_side_interface_name": "c0_ddr4_s_axi_*",
    "ddr_channel_name": "c0",
    "ddr_channels": 1,
    "ddr_word_width_bits": 512,
    "memory_type": "DDR4",
    "real_board_reference_rtl": "verification/rtl/cnn_core.sv"
  },
  "notes": [
    "The FPGA part is reported for the example Vivado project in vu9p_fpga_\u6837\u4f8b\u5de5\u7a0b.md; confirm it is the exact part for the intended deployment board.",
    "DDR/AXI dimensions, interface signals, XDMA raw-access protocol, runtime command, addresses, device ID, runtime directory, and default DDR image are taken from runtime_axi_ddr.md.",
    "The sample-project host hyyuan@10.12.133.23 identifies a remote sample-project location, not necessarily the board execution host; target remote host and port are therefore unknown.",
    "A board smoke script is identified, but its pass/fail conditions, shell details, memory capacity, and resource or timing limits are not specified in the available evidence."
  ],
  "runtime_interface": {
    "board_run_command": "scripts/board/run_pyjm12_smoke.sh",
    "c2h_device_template": "/dev/xdma${XDMA_ID}_c2h_0",
    "control_base": "0x3000000000",
    "control_protocol": "xdma_raw_register_and_ddr",
    "ctrl_base": "0x3000000000",
    "ddr_base": "0x2800000000",
    "ddr_image_default": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
    "device_id": 1,
    "h2c_device_template": "/dev/xdma${XDMA_ID}_h2c_0",
    "image_path": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
    "mimic_dir": "/home/test/mimic_driver_c6",
    "output_abs": "0x28092f1000",
    "output_address": "0x28092f1000",
    "runtime_directory": "/home/test/mimic_driver_c6",
    "xdma_id_default": 1
  },
  "schema_version": "spatialaccagent.target_board_profile.v0",
  "shell": {
    "calibration_done_signal": "c0_init_calib_complete",
    "core_ddr_axi_interface": "c0_ddr4_s_axi_*",
    "init_calibration_done_signal": "c0_init_calib_complete",
    "real_board_axi_reference_rtl": "verification/rtl/cnn_core.sv"
  }
}
</target_board_profile>

<field_evidence_summary>
{
  "policy": {
    "llm_output_is_not_accepted_as_evidence_without_source": true,
    "llm_semantic_confirmation_required": true,
    "regex_candidates_are_not_ground_truth": true,
    "source": "merged_from_domain_llm_agents",
    "split_domain_agents": [
      "board",
      "tool",
      "quantization"
    ]
  },
  "schema_version": "spatialaccagent.field_evidence_summary.v0",
  "selected_fields": [
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "\u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "tool.vcs.host"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "\u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Software/EDATools/Synopsys/VCSALL/v202206-OLD/bin/vcs",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "/home/EDA/Software/EDATools/Synopsys/VCSALL/v202206-OLD/bin/vcs"
        }
      ],
      "field": "tool.vcs.executable"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "tools:000004",
          "excerpt": "\u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "tool.vivado.host"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "tools:000004",
          "excerpt": "\u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Xilinx/Vivado/2021.1/bin/vivado",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md",
          "value": "/home/EDA/Xilinx/Vivado/2021.1/bin/vivado"
        }
      ],
      "field": "tool.vivado.executable"
    }
  ]
}
</field_evidence_summary>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "notes": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "schema_version": {
      "type": "string"
    },
    "tools": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "constraints": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "env": {
            "additionalProperties": true,
            "type": "object"
          },
          "executable": {
            "type": [
              "string",
              "null"
            ]
          },
          "host": {
            "type": [
              "string",
              "null"
            ]
          },
          "name": {
            "type": "string"
          },
          "port": {
            "type": [
              "integer",
              "null"
            ]
          },
          "role": {
            "type": "string"
          },
          "scope": {
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
          "workdir": {
            "type": [
              "string",
              "null"
            ]
          }
        },
        "required": [
          "name",
          "role",
          "scope",
          "host",
          "port",
          "executable",
          "env",
          "workdir",
          "constraints",
          "source"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "schema_version",
    "tools",
    "notes"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
