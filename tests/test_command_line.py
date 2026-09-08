"""What the tower does when it is asked something it does not understand.

`python3 watch.py --help` fetched every source, rewrote `WATCH.md`,
`feed.xml` and `state.json`, and marked two pending events as seen -- because
the tool took no arguments, so every argument was ignored and the only thing
left to do was run. A tool that answers a typo by doing its work is a tool
whose most destructive path is also its easiest to reach by accident.

So the command line is parsed before anything is read or written, and there is
a way to ask what a run would do without a run happening.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_watch():
    """The module, imported without running it."""
    spec = importlib.util.spec_from_file_location("watch_under_test", ROOT / "watch.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


watch = load_watch()


@pytest.fixture()
def quiet_tower(tmp_path, monkeypatch):
    """A tower with no sources: nothing to fetch, so nothing can be fetched.

    The writes are what this file is about, and a source list of zero takes
    the network out of the question entirely rather than mocking it away.
    """
    (tmp_path / "sources.json").write_text(json.dumps({"sources": []}), "utf-8")
    monkeypatch.setattr(watch, "ROOT", tmp_path)
    return tmp_path


WRITTEN = ("state.json", "WATCH.md", "feed.xml")


def test_a_run_writes_the_three_files(quiet_tower):
    """The discriminating half: a main that never wrote anything would pass
    the dry-run test below for the wrong reason."""
    watch.main([])
    for name in WRITTEN:
        assert (quiet_tower / name).exists(), name


def test_a_dry_run_writes_nothing(quiet_tower):
    watch.main(["--dry-run"])
    for name in WRITTEN:
        assert not (quiet_tower / name).exists(), name


def test_an_unknown_argument_stops_the_tool(quiet_tower):
    """The accident itself. `--helpp` must not be a run."""
    with pytest.raises(SystemExit) as exit_:
        watch.main(["--helpp"])
    assert exit_.value.code != 0
    for name in WRITTEN:
        assert not (quiet_tower / name).exists(), name


def test_help_is_help(quiet_tower, capsys):
    with pytest.raises(SystemExit) as exit_:
        watch.main(["--help"])
    assert exit_.value.code == 0
    assert "--dry-run" in capsys.readouterr().out
    for name in WRITTEN:
        assert not (quiet_tower / name).exists(), name
