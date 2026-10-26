"""The front page says what the tower watches and what stands beside it.

Both halves drifted while nothing held them. The watched list in the README
named the sources of the tower's first weeks while `sources.json` kept
growing, and the line about the neighbouring validator kept a rule count from
the week it was written.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def readme():
    return (ROOT / "README.md").read_text("utf-8")


def test_the_full_list_is_the_table_the_tower_writes():
    """The page names the table rather than repeating it: of a list kept by
    hand and a list the cron writes, the hand-kept one is the one that goes
    stale."""
    assert "## Watched sources" in (ROOT / "watch.py").read_text("utf-8")
    assert "(WATCH.md#watched-sources)" in readme()


def test_the_page_quotes_no_figure_a_neighbour_keeps():
    """Another repository's rule count is true the day it is copied here and
    false at that repository's next release; this page links instead."""
    counts = re.findall(r"\b\d+[- ]rules?\b", readme())
    assert counts == [], counts
