"""The pure core: given state and fetched items, which events fire."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from watch import diff_hash, diff_seen  # noqa: E402

TODAY = "2026-08-21T00:00:00Z"


def test_first_sight_seeds_silently():
    state = {}
    events = diff_seen(state, [("a", "A", "u/a"), ("b", "B", "u/b")], "src", TODAY)
    assert events == []
    assert state["seen"] == ["a", "b"]


def test_a_new_item_becomes_one_event():
    state = {"seen": ["a"]}
    events = diff_seen(state, [("a", "A", "u/a"), ("b", "B", "u/b")], "src", TODAY)
    assert [e["title"] for e in events] == ["B"]
    assert "b" in state["seen"]


def test_vanished_items_stay_seen_so_they_cannot_refire():
    state = {"seen": ["a", "b"]}
    assert diff_seen(state, [("b", "B", "u/b")], "src", TODAY) == []
    assert state["seen"] == ["a", "b"]


def test_hash_change_fires_once_then_settles():
    state = {}
    assert diff_hash(state, "h1", "page", "u", TODAY) == []      # baseline
    assert diff_hash(state, "h1", "page", "u", TODAY) == []      # no change
    changed = diff_hash(state, "h2", "page", "u", TODAY)
    assert len(changed) == 1 and changed[0]["url"] == "u"
    assert diff_hash(state, "h2", "page", "u", TODAY) == []
