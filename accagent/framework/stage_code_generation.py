"""Code generation stage entrypoint.

The implementation lives in stage_artifacts.py for compatibility with older
run records, but the public stage name is code_generation.
"""

from __future__ import annotations

from accagent.framework.stage_artifacts import main


if __name__ == "__main__":
    raise SystemExit(main())
