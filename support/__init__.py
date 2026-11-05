"""Test helpers shared by every lesson.

`target(__file__)` imports the lesson's *exercise* code, or its *solution* code
when the SOLUTIONS=1 environment variable is set (`python check.py f05 --solution`).
"""
import importlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def using_solutions() -> bool:
    return os.environ.get("SOLUTIONS") == "1"


def target(test_file: str, submodule: str | None = None):
    """Import `<lesson>.exercise[.submodule]` (or `.solution`) for the test at `test_file`."""
    lesson_dir = Path(test_file).resolve().parent
    package = ".".join(lesson_dir.relative_to(ROOT).parts)
    kind = "solution" if using_solutions() else "exercise"
    name = f"{package}.{kind}" + (f".{submodule}" if submodule else "")
    return importlib.import_module(name)
