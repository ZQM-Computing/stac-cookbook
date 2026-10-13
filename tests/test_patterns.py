#!/usr/bin/env python3
"""Tests for stac-patterns."""
import subprocess
import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def test_python_syntax():
    """All Python examples have valid syntax."""
    for py_file in sorted(EXAMPLES_DIR.glob("*/run.py")):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True
        )
        assert result.returncode == 0, f"Syntax error in {py_file}"


def test_readme_exists():
    """README.md exists."""
    assert (Path(__file__).parent.parent / "README.md").exists()


def test_license_exists():
    """LICENSE file exists."""
    assert (Path(__file__).parent.parent / "LICENSE").exists()
