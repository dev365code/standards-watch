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


def test_a_source_that_first_saw_nothing_still_reports_its_first_arrival():
    """An issue watcher's first look uses `since=now` and legitimately finds
    nothing. Treating "found nothing" as "never looked" makes the next arrival
    look like first sight, and the watcher swallows the one event it exists for.

    Five sources were in that state when this was found, including every issue
    watcher — the ones that tell us a standards body answered.
    """
    state = {}
    assert diff_seen(state, [], "issues", "day1") == []          # first look: quiet
    assert "seen" in state, "the first look must record that it happened"
    events = diff_seen(state, [("i#38", "a reply arrived", "u")], "issues", "day2")
    assert [e["title"] for e in events] == ["a reply arrived"]


def test_a_genuine_first_sight_is_still_silent():
    state = {}
    assert diff_seen(state, [("a", "A", "u"), ("b", "B", "u")], "releases", "day1") == []
    assert diff_seen(state, [("a", "A", "u"), ("c", "C", "u")], "releases", "day2") != []
