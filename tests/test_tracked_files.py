"""What the repository tracks, and what a build makes.

`watch.egg-info/` was committed by accident and then sat in the tree for five
commits while the tests it lists grew from two to five. Nothing noticed,
because nothing reads it: an editable install rewrites it from `pyproject.toml`
and `watch.py`, and the copy in git is whichever build happened to run last on
whichever machine last committed. A tracked file that a build rewrites is a
file that disagrees with the build and has no reader to say so.

The tower's own generated files are a different thing and stay: `state.json`,
`WATCH.md` and `feed.xml` are what the watch job commits, and their history
*is* the log. This is about the artefacts of packaging, which describe the
machine that built them rather than anything observed.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Directories a Python build writes and a checkout must not carry.
BUILD_ARTEFACTS = ("*.egg-info/", "build/", "dist/", "__pycache__/")


def tracked(*paths):
    """`git ls-files`, or None where there is no checkout to ask."""
    result = subprocess.run(["git", "-C", str(ROOT), "ls-files", *paths],
                            capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line]


def test_the_gitignore_names_what_a_build_writes():
    ignore = (ROOT / ".gitignore").read_text("utf-8").splitlines()
    for pattern in BUILD_ARTEFACTS:
        assert pattern in ignore, pattern


#: `ls-files` reports files, so a pathspec naming a directory matches
#: nothing at all -- `*.egg-info` came back empty with four of its files
#: tracked. Every entry here ends at a file.
ARTEFACT_PATHS = ("*.egg-info/*", "build/*", "dist/*", "*/__pycache__/*",
                  "__pycache__/*")


def test_no_build_artefact_is_tracked():
    """The ignore file above is the intention; this is the fact.

    Ignoring a path does nothing to one already tracked, which is exactly how
    the accident survived -- so the two are asked separately.
    """
    found = tracked(*ARTEFACT_PATHS)
    if found is None:
        import pytest
        pytest.skip("not a git checkout")
    assert found == [], found
