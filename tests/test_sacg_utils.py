from pathlib import Path

from accagent.framework.sacg_utils import run_dir_from_state


def test_run_dir_from_nested_repair_state_finds_run_markers(tmp_path: Path) -> None:
    run_dir = tmp_path / "gpt2_medium"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input/prepared_inputs.json").touch()
    state = run_dir / "backend_board/repair_execution/sacg_state.json"
    state.parent.mkdir(parents=True)
    state.touch()

    assert run_dir_from_state(state) == run_dir.resolve()


def test_run_dir_from_standard_stage_state_finds_run_markers(tmp_path: Path) -> None:
    run_dir = tmp_path / "gpt2_medium"
    (run_dir / "agent").mkdir(parents=True)
    (run_dir / "agent/agent_run_report.json").touch()
    state = run_dir / "verification/sacg_state.json"
    state.parent.mkdir(parents=True)
    state.touch()

    assert run_dir_from_state(state) == run_dir.resolve()


def test_run_dir_from_state_preserves_legacy_fallback(tmp_path: Path) -> None:
    state = tmp_path / "run" / "stage" / "sacg_state.json"
    state.parent.mkdir(parents=True)
    state.touch()

    assert run_dir_from_state(state) == (tmp_path / "run").resolve()
