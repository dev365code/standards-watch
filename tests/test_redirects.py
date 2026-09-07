"""What happens when a watched URL points somewhere else.

`urllib` follows redirects by default and carries the request's headers to the
new location: `HTTPRedirectHandler.redirect_request` copies everything except
`content-length` and `content-type`, whatever the new host is. So a source
that redirects off its own host takes this tower's credential with it, and no
configuration here would be wrong for that to happen.

It is also, on its own terms, the thing this tower exists to notice. A source
moving to another host is news about that source. So the redirect is not
followed and not silently dropped: it is refused, and the refusal becomes an
event a reader sees, next to every other thing that moved.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from watch import CrossHostRedirect, diff_seen, moved_item, redirect_allowed  # noqa: E402


def test_a_redirect_within_the_host_is_followed():
    assert redirect_allowed("https://example.org/a", "https://example.org/b")
    assert redirect_allowed("https://example.org/a", "https://example.org/a/")


def test_a_redirect_to_another_host_is_not():
    for target in ("https://other.example/a",
                   "https://example.org.other.example/a",
                   "https://sub.example.org/a"):
        assert not redirect_allowed("https://example.org/a", target), target


def test_a_downgrade_on_the_same_host_is_not():
    """The host is right and the credential would ride in the clear."""
    assert not redirect_allowed("https://example.org/a", "http://example.org/a")


def test_an_upgrade_is_fine():
    assert redirect_allowed("http://example.org/a", "https://example.org/a")


def test_the_refusal_carries_both_ends():
    error = CrossHostRedirect("https://example.org/a", "https://other.example/b")
    assert "example.org" in str(error) and "other.example" in str(error)


def test_the_refusal_becomes_something_a_reader_sees():
    """A skipped source is a stale row in a table; a source that moved is a
    line in the feed, which is the difference between a tower that noticed and
    a tower that went quiet.

    Through `diff_seen`, in the shape a fetcher returns, so the move is kept
    and reported once like everything else. The source is an established one
    -- it has been seen before -- because that is the case that matters: a
    brand-new source seeds its memory silently, and a move is only news about
    a source somebody was already watching.
    """
    entry = {"seen": ["release-1"]}
    events = diff_seen(entry, [moved_item("https://example.org/a",
                                          "https://other.example/b")],
                       "iiRDS spec", "2026-09-08T00:00:00Z")
    assert len(events) == 1, events
    assert events[0]["source"] == "iiRDS spec"
    assert events[0]["url"] == "https://example.org/a"
    assert "other.example" in events[0]["title"]
    assert events[0]["date"] == "2026-09-08T00:00:00Z"


def test_the_same_move_is_not_reported_twice():
    entry = {"seen": ["release-1"]}
    item = moved_item("https://example.org/a", "https://other.example/b")
    assert diff_seen(entry, [item], "iiRDS spec", "2026-09-08T00:00:00Z")
    assert diff_seen(entry, [item], "iiRDS spec", "2026-09-09T00:00:00Z") == []


def test_the_handler_refuses_rather_than_rewriting():
    import urllib.request

    from watch import _NoCrossHostRedirect

    handler = _NoCrossHostRedirect()
    request = urllib.request.Request("https://example.org/a")
    with pytest.raises(CrossHostRedirect):
        handler.redirect_request(request, None, 302, "Found", {},
                                 "https://other.example/b")
