"""In-place package shim for the copied ActiveGraph source tree.

The copied runtime keeps package modules directly under ``src``. Editable
installation can map that directory to the ``activegraph`` package, but local
checkout execution via ``PYTHONPATH=.../src`` needs an actual package directory.
This shim makes ``python -m activegraph`` and ``import activegraph.cli`` resolve
against the copied source rather than a globally installed package.
"""
from __future__ import annotations

from pathlib import Path

_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_SOURCE_ROOT_TEXT = str(_SOURCE_ROOT)
if _SOURCE_ROOT_TEXT not in __path__:
    __path__.append(_SOURCE_ROOT_TEXT)

_SOURCE_INIT = _SOURCE_ROOT / "__init__.py"
exec(compile(_SOURCE_INIT.read_text(encoding="utf-8"), str(_SOURCE_INIT), "exec"), globals())
