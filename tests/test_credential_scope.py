"""Which requests the tower's credential is attached to.

The cron gives `watch.py` a `GITHUB_TOKEN` so the GitHub API answers with a
useful rate limit. That token belongs on requests to the GitHub API and
nowhere else, and "nowhere else" has to be decided by something narrower than
asking whether the host's name appears somewhere in the URL: it appears in
`https://example.invalid/api.github.com` too, and adding a source here is a
row in `sources.json` rather than a patch.

The decision is a pure function of a URL so a case for it is a string, and
each case below is wrong on one axis only — the host — with the rest of the
URL left ordinary.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from watch import wants_credential  # noqa: E402


def test_the_api_host_gets_it():
    assert wants_credential("https://api.github.com/repos/o/r/releases")
    assert wants_credential("https://api.github.com/repos/o/r/issues?since=x")


def test_a_host_that_merely_contains_the_name_does_not():
    """Each of these carries the string and none of them is the API."""
    for url in ("https://example.invalid/api.github.com",
                "https://api.github.com.example.invalid/repos/o/r",
                "https://example.invalid/?ref=api.github.com",
                "https://example.invalid/#api.github.com",
                "https://api.github.com@example.invalid/repos/o/r"):
        assert not wants_credential(url), url


def test_the_scheme_is_part_of_it():
    """A plaintext request to the right host is still the wrong request to
    put a bearer token on."""
    assert not wants_credential("http://api.github.com/repos/o/r")


def test_nonsense_is_not_the_api():
    for url in ("", "not a url", "file:///etc/passwd", "https://"):
        assert not wants_credential(url), url
