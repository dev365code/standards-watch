"""How much of an answer this tower will read.

`timeout=30` bounds how long a source may take and says nothing about how much
it may send. A body arrives from a machine nobody here controls, and the read
was `response.read()` — whatever comes.

Truncating instead of refusing would be worse than either: the hash of a
prefix is a hash that changes whenever the prefix does, so a source too large
to read would report a move on every run, and a feed that cries every day is
a feed nobody reads.
"""
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from watch import MAX_BODY_BYTES, TooLarge, diff_seen, oversize_item, read_capped  # noqa: E402


def test_a_body_under_the_cap_comes_back_whole():
    body = b"x" * 1000
    assert read_capped(io.BytesIO(body), 4096) == body


def test_a_body_at_the_cap_comes_back_whole():
    body = b"x" * 4096
    assert read_capped(io.BytesIO(body), 4096) == body


def test_one_byte_over_is_refused():
    with pytest.raises(TooLarge):
        read_capped(io.BytesIO(b"x" * 4097), 4096)


def test_the_refusal_says_the_limit():
    with pytest.raises(TooLarge) as raised:
        read_capped(io.BytesIO(b"x" * 4097), 4096)
    assert "4096" in str(raised.value)


def test_the_cap_is_far_above_what_a_source_sends():
    """A release listing is a few hundred kilobytes and a watched page is
    around one megabyte at worst. The cap is not a tuning knob; it is the line
    past which the answer is not the kind of thing this tower reads."""
    assert MAX_BODY_BYTES >= 8 * 1024 * 1024


def test_an_oversized_source_is_reported_rather_than_left_stale():
    """The S12 lesson from the validator, in a second tool: a check that gave
    up and a check that finished quietly look the same to a reader, and only
    one of them is a reason to go and look."""
    entry = {"seen": ["release-1"]}
    events = diff_seen(entry, [oversize_item("https://example.org/a", 4096)],
                       "a source", "2026-09-08T00:00:00Z")
    assert len(events) == 1, events
    assert "4096" in events[0]["title"]
    assert events[0]["url"] == "https://example.org/a"
