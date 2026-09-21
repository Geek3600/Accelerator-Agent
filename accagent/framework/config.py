"""Editable run settings for the current framework flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from accagent.framework.llm_config import LlmCfg, resolved_llm_cfg


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RunCfg:
    root: Path = ROOT
    out: Path = ROOT / "accagent" / "runs" / "spatialacc_agent_run"
    design: str = "spatialacc_agent_run"
    task_spec: Path = ROOT / "accagent" / "framework" / "examples" / "task_spec.md"
    model_source: Path | None = None
    model_dir: Path | None = None
    board_materials_dir: Path = ROOT / "accagent" / "framework" / "input_materials" / "board"
    quantization_materials_dir: Path = ROOT / "accagent" / "framework" / "input_materials" / "quantization"
    tool_materials_dir: Path = ROOT / "accagent" / "framework" / "input_materials" / "tools"
    run_real_tools: bool = True
    real_tool_timeout_sec: int = 0
    resume_existing: bool = True
    llm: LlmCfg = field(default_factory=resolved_llm_cfg)


CFG = RunCfg()
