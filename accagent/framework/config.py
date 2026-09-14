"""Editable run settings for the current framework flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from accagent.framework.llm_config import LlmCfg, resolved_llm_cfg


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RunCfg:
    root: Path = ROOT
    out: Path = ROOT / "accagent" / "runs" / "spatialacc_qwen_agent_fast_run"
    design: str = "qwen2_spatialacc_agent_run"
    task_spec: Path = ROOT / "accagent" / "framework" / "examples" / "task_spec.md"
    model_source: Path = ROOT / "accagent" / "runs" / "model_configs" / "qwen2_0_5b" / "model_config.json"
    board_materials_dir: Path = ROOT / "accagent" / "framework" / "input_materials" / "board"
    quantization_materials_dir: Path = ROOT / "accagent" / "framework" / "input_materials" / "quantization"
    tool_materials_dir: Path = ROOT / "accagent" / "framework" / "input_materials" / "tools"
    run_real_tools: bool = True
    real_tool_timeout_sec: int = 0
    resume_existing: bool = True
    llm: LlmCfg = field(default_factory=resolved_llm_cfg)


CFG = RunCfg()
