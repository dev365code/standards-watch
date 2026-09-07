"""Text this tower did not write, in the files this tower publishes.

Every title here comes from somewhere else — a release name, an issue title, a
directory entry — and both published artefacts are built by formatting those
strings into markup. `feed.xml` escapes them. `WATCH.md` did not, and a title
is enough to change where a link on that page points, which is the one thing a
reader of a page about links should be able to trust.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from watch import md_text, md_url, write_watch_md  # noqa: E402


def test_a_title_cannot_close_the_link_it_is_inside():
    """`[title](url)` with a `]` in the title ends the link early and leaves
    the rest of the title as page text — and a `(` after it starts a target
    the source chose."""
    hostile = "release ](https://example.invalid) and"
    assert "](" not in md_text(hostile)


def test_the_markers_that_carry_meaning_are_neutralised():
    """Escaped, not removed: the reader still sees the character the source
    wrote, and Markdown stops reading it as an instruction."""
    for character in "[]()`*_<>|\\":
        assert md_text("a %s b" % character) == "a \\%s b" % character, character


def test_ordinary_text_survives_readable():
    """Escaping that mangles every title would be paid for on every line of a
    page whose whole purpose is to be read. `.`, `-`, `#` and `!` carry
    meaning at the start of a line and are never at the start of one here."""
    for plain in ("iiRDS 1.3 release: metadata.rdf clarified",
                  "VDI 2770 — reference implementation",
                  "NLnet open call #2 closes 1 October"):
        assert md_text(plain) == plain, plain


def test_a_newline_cannot_start_a_new_row():
    """The sources table is one row per line, so a title with a line break in
    it would write rows nobody added."""
    assert "\n" not in md_text("first\nsecond")
    assert "\r" not in md_text("first\rsecond")


def test_a_link_target_cannot_end_its_own_link():
    """The other half of the same line. A title carrying `](` is one way to
    move the link; a URL carrying `)` is the other, and only one of them was
    obvious."""
    hostile = "https://example.org/a) [click](https://example.invalid"
    escaped = md_url(hostile)
    assert ")" not in escaped and " " not in escaped and "(" not in escaped


def test_an_ordinary_link_is_left_alone():
    for plain in ("https://github.com/dev365code/standards-watch/releases/tag/v1.3",
                  "https://api.github.com/repos/o/r/issues?since=2026-01-01",
                  "https://example.org/a#b"):
        assert md_url(plain) == plain, plain


def test_the_page_that_gets_written_is_the_escaped_one(tmp_path, monkeypatch):
    """The two above test the escapers. This tests that the page uses them.

    Written after taking the call out of `write_watch_md` and watching every
    other test here stay green: a helper with cases behind it says nothing
    about whether anybody calls it, and the missing call is the whole defect.
    """
    import watch

    monkeypatch.setattr(watch, "ROOT", tmp_path)
    hostile = "release ](https://example.invalid) and"
    write_watch_md(
        [{"key": "k", "label": "a | b", "kind": "html"}],
        {"k": {"checked": "2026-09-08T00:00:00Z"}},
        [{"date": "2026-09-08T00:00:00Z", "title": hostile,
          "url": "https://example.org/a) x", "source": "src"}])
    page = (tmp_path / "WATCH.md").read_text("utf-8")
    assert "](https://example.invalid)" not in page, page
    assert ") x" not in page, page
    #: and the table row cannot grow a column
    assert "| a | b |" not in page, page
