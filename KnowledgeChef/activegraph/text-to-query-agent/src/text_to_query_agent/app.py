"""Application boundary placeholder for the TextToQueryAgent baseline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PackContext:
    """Resolved pack resources passed into the agent runtime.

    This will replace scattered path/default arguments as the new implementation
    migrates behavior from the frozen text-to-sql-agent baseline.
    """

    pack_id: str
    db_file: Path | None
    event_store: Path | None
    system_model_file: Path
    schema_root: Path | None
    eval_cases_file: Path | None
    tests_dir: Path
    eval_runs_dir: Path


class TextToQueryAgent:
    """Thin future service boundary over ActiveGraph Runtime.

    The first implementation target is DB-only parity with the frozen v11.5
    Text-to-SQL baseline. OKF KB/RAG behavior must be added only after parity
    is proven by evals and event evidence.
    """

    def __init__(self, context: PackContext) -> None:
        self.context = context

    def describe(self) -> dict[str, str | None]:
        return {
            "pack_id": self.context.pack_id,
            "system_model_file": str(self.context.system_model_file),
            "db_file": str(self.context.db_file) if self.context.db_file else None,
            "schema_root": str(self.context.schema_root) if self.context.schema_root else None,
        }
