"""The tower's provenance file, and the one claim in it that is load-bearing.

NOTICE says the watcher is standard-library only and redistributes no
third-party code. A watcher that needs a dependency update is a watcher that
eventually stops watching, so the sentence is not decoration -- and a sentence
nobody checks drifts. The test that reads it also holds it against what
watch.py actually imports.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def top_level_imports(source: str) -> set:
    """Every module a piece of Python source imports, by top-level name."""
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def is_standard_library(name: str) -> bool:
    known = getattr(sys, "stdlib_module_names", None)  # 3.10 and later
    if known is not None:
        return name in known
    if name in sys.builtin_module_names:
        return True
    spec = importlib.util.find_spec(name)
    origin = getattr(spec, "origin", None) or ""
    return origin.startswith(sysconfig.get_paths()["stdlib"])


def test_the_watcher_imports_nothing_outside_the_standard_library():
    used = top_level_imports((ROOT / "watch.py").read_text("utf-8"))
    outside = sorted(name for name in used if not is_standard_library(name))
    assert outside == [], "watch.py now depends on %s" % outside


def test_the_sweep_would_notice_a_dependency():
    """A sweep that cannot see an import is a sweep that passes for ever."""
    assert top_level_imports("import requests\nfrom bs4 import BeautifulSoup\n") == {
        "requests", "bs4"}
    assert not is_standard_library("requests")
    assert is_standard_library("json")


def test_the_notice_exists_and_says_what_the_readme_says():
    notice = (ROOT / "NOTICE").read_text("utf-8")
    readme = (ROOT / "README.md").read_text("utf-8")
    assert "Apache License, Version 2.0" in notice
    assert "Apache-2.0 © 2026 Wooyong Lee" in readme, "the README licence line moved; align both"
    assert "2026 Wooyong Lee" in notice, "NOTICE and README name different holders or years"
    assert "standard library" in notice.lower(), (
        "NOTICE no longer states the claim the sweep above checks")
