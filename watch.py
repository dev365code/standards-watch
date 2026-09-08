"""A watch tower for quiet standards.

iiRDS, VDI 2770 and the AAS submodels move slowly and announce quietly —
a new template directory here, a spec release there, a funding call that
opens for eight weeks. The people affected are exactly the people who do
not refresh eight pages daily. So a cron does: every source is diffed
against committed state, anything new becomes an event, and events become
a feed (feed.xml) and a human page (WATCH.md).

Standard library only, on purpose: a watcher that needs a dependency
update is a watcher that eventually stops watching.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
MAX_EVENTS = 300
SHOWN_IN_MD = 40
SHOWN_IN_FEED = 50


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


#: The one host this tower's credential belongs to.
API_HOST = "api.github.com"


#: How much of one answer this tower will read. A release listing runs to a
#: few hundred kilobytes and a watched page to about a megabyte at worst, so
#: this is roughly eight times the largest thing any source here sends. It is
#: not a tuning knob: past it the answer is not the kind of thing this tower
#: reads, and `timeout` bounds how long a source may take rather than how much
#: it may send.
MAX_BODY_BYTES = 8 * 1024 * 1024


class TooLarge(Exception):
    """A source answered with more than this tower will read."""

    def __init__(self, limit: int, url: str = ""):
        super().__init__("more than %d bytes from %s" % (limit, url or "the source"))
        self.limit, self.url = limit, url


def read_capped(stream, limit: int = MAX_BODY_BYTES) -> bytes:
    """The body, or nothing at all.

    Refuse rather than truncate. A hash of a prefix is a hash that moves when
    the prefix does, so a source too large to read would report a change on
    every run — and a tower that cries every day is one nobody reads.
    """
    body = stream.read(limit + 1)
    if len(body) > limit:
        raise TooLarge(limit)
    return body


class CrossHostRedirect(Exception):
    """A watched URL answered by pointing at a different host."""

    def __init__(self, url: str, target: str):
        super().__init__("%s redirects to %s" % (url, target))
        self.url, self.target = url, target


def redirect_allowed(url: str, target: str) -> bool:
    """Whether a redirect stays inside the source it started from.

    Same host, and not a step down from https to http: `urllib` carries the
    request's headers to wherever it is sent -- everything but content-length
    and content-type, whatever the new host is -- so a redirect is where a
    credential leaves without anyone configuring it to.
    """
    here, there = urllib.parse.urlsplit(url), urllib.parse.urlsplit(target)
    if here.hostname != there.hostname:
        return False
    return not (here.scheme == "https" and there.scheme != "https")


def oversize_item(url: str, limit: int):
    """A source answering with more than this tower reads, in a fetcher's
    shape, so it is reported once and kept like anything else."""
    return ("oversize:%s:%d" % (url, limit),
            "source answered with more than %d bytes" % limit, url)


def moved_item(url: str, target: str):
    """A source that points elsewhere, in the shape a fetcher returns.

    `(id, title, url)`, the same triple every fetcher yields, so the move goes
    through `diff_seen` like anything else: seen once, reported once, and kept
    in the same list. Refusing and moving on would leave a stale row in a
    table instead, and a source that moved is news about that source.
    """
    return ("moved:%s->%s" % (url, target),
            "source now redirects to %s" % target, url)


class _NoCrossHostRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse rather than follow, so the credential cannot ride along and the
    move is reported instead of absorbed."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not redirect_allowed(req.full_url, newurl):
            raise CrossHostRedirect(req.full_url, newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_NoCrossHostRedirect())


def wants_credential(url: str) -> bool:
    """Whether a request to this URL is a request to the GitHub API.

    Decided on the parsed host and the scheme, not on whether the name occurs
    somewhere in the string. It occurs in `https://example.invalid/api.github.com`
    as well, and in a host that merely ends with it, and after an `@` — and a
    source here is a row in `sources.json` rather than a patch, so the row is
    all it would take.
    """
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return parts.scheme == "https" and parts.hostname == API_HOST


def fetch(url: str, accept: str = "application/vnd.github+json") -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "standards-watch (github.com/dev365code/standards-watch)",
        "Accept": accept,
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token and wants_credential(url):
        request.add_header("Authorization", "Bearer " + token)
    with _OPENER.open(request, timeout=30) as response:
        try:
            return read_capped(response)
        except TooLarge as large:
            raise TooLarge(large.limit, url) from None


# -- fetchers: each returns a list of (id, title, url) ----------------------

def fetch_gh_releases(repo: str):
    data = json.loads(fetch("https://api.github.com/repos/%s/releases?per_page=10" % repo))
    return [(str(r["id"]), "%s: %s" % (repo, r.get("name") or r["tag_name"]),
             r["html_url"]) for r in data]


def fetch_gh_dir(repo: str, path: str):
    data = json.loads(fetch("https://api.github.com/repos/%s/contents/%s" % (repo, path)))
    return [(entry["name"], "new template: %s" % entry["name"], entry["html_url"])
            for entry in data if entry["type"] == "dir"]


def fetch_gh_issues(repo: str, since: str):
    url = ("https://api.github.com/repos/%s/issues?state=all&sort=updated"
           "&direction=desc&per_page=30&since=%s" % (repo, since))
    data = json.loads(fetch(url))
    return [(("%s#%s@%s" % (repo, item["number"], item["updated_at"])),
             "%s#%d %s" % (repo.split("/")[1], item["number"], item["title"]),
             item["html_url"]) for item in data]


def fetch_html_hash(url: str) -> str:
    return hashlib.sha256(fetch(url, accept="text/html")).hexdigest()


# -- the pure part: state + fetched -> events (this is what the test holds) --

def diff_seen(state: dict, fetched, label: str, today: str):
    """Set-diff kinds. First sight seeds silently: a tower that fires 300
    'new' events on day one has taught its readers to ignore it by day two."""
    seen = set(state.get("seen", []))
    events = []
    # "have we looked before", not "did we find anything". An issue watcher's
    # first look uses `since=now` and legitimately returns nothing, so testing
    # the set for truthiness makes the *next* arrival look like first sight and
    # swallows it — which is exactly the event the watcher exists for.
    if "seen" in state:
        for item_id, title, url in fetched:
            if item_id not in seen:
                events.append({"date": today, "source": label, "title": title, "url": url})
    state["seen"] = sorted(seen | {item_id for item_id, _t, _u in fetched})[-500:]
    return events


def diff_hash(state: dict, digest: str, label: str, url: str, today: str):
    events = []
    if state.get("hash") and state["hash"] != digest:
        events.append({"date": today, "source": label,
                       "title": "page changed — worth a look", "url": url})
    state["hash"] = digest
    return events


# -- outputs -----------------------------------------------------------------

#: Markdown characters that change what a line *means* rather than what it
#: says, in the middle of a line: link and emphasis markers, a raw angle
#: bracket, and the table separator. Not `#`, `-`, `.` or `!`, which matter at
#: the start of a line and never appear there here -- escaping those turns
#: "iiRDS 1.3" into "iiRDS 1\.3" on a page whose purpose is to be read, and a
#: page nobody reads is its own kind of failure.
#:
#: A line break has no escape and becomes a space: the tables here are one row
#: per line, so a title carrying one would write rows nobody added.
_MD_MARKERS = "\\`*_[]()<>|"


def md_url(url: str) -> str:
    """A URL from somewhere else, safe to put inside `[...](here)`.

    Brackets and spaces end a Markdown link target, so a URL carrying one can
    close the link and open another with a destination the source chose.
    Percent-encoding them is what a URL does with them anyway; everything a
    URL needs is left alone, so an ordinary link stays readable.
    """
    return urllib.parse.quote(str(url), safe=":/?#[]@!$&'*+,;=~")


def md_text(text: str) -> str:
    """A string from somewhere else, safe to put in a line of Markdown.

    `feed.xml` has escaped its titles since it was written and `WATCH.md` did
    not, so a release name carrying `](` could move the link beside it. Both
    files are built by formatting text this tower did not write.
    """
    out = []
    for character in str(text):
        if character in "\r\n":
            out.append(" ")
        elif character in _MD_MARKERS:
            out.append("\\" + character)
        else:
            out.append(character)
    return "".join(out)


def write_watch_md(sources, state, events):
    lines = ["# What moved",
             "",
             "Auto-generated by [watch.py](watch.py) on a daily cron; newest first.",
             "Subscribe via [feed.xml](feed.xml) in any RSS reader.",
             "", "## Latest", ""]
    if events:
        for event in events[:SHOWN_IN_MD]:
            lines.append("- **%s** · [%s](%s) · %s" % (
                event["date"][:10], md_text(event["title"]),
                md_url(event["url"]),
                md_text(event["source"])))
    else:
        lines.append("- (baseline established; events appear as the world moves)")
    lines += ["", "## Watched sources", "",
              "| source | kind | last checked |", "|---|---|---|"]
    for source in sources:
        checked = state.get(source["key"], {}).get("checked", "—")
        lines.append("| %s | %s | %s |" % (md_text(source["label"]),
                                            md_text(source["kind"]), md_text(checked[:16])))
    (ROOT / "WATCH.md").write_text("\n".join(lines) + "\n", "utf-8")


def write_feed(events):
    items = []
    for event in events[:SHOWN_IN_FEED]:
        items.append(
            "<item><title>%s</title><link>%s</link><pubDate>%s</pubDate>"
            "<description>%s</description></item>"
            % (escape(event["title"]), escape(event["url"]),
               event["date"], escape(event["source"])))
    feed = ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
            "<rss version=\"2.0\"><channel>"
            "<title>standards-watch: iiRDS / VDI 2770 / AAS</title>"
            "<link>https://github.com/dev365code/standards-watch</link>"
            "<description>Releases, templates, issue activity and funding "
            "calls around industrial documentation standards.</description>"
            + "".join(items) + "</channel></rss>\n")
    (ROOT / "feed.xml").write_text(feed, "utf-8")


def parse_args(argv=None) -> argparse.Namespace:
    """The command line, parsed before anything is read, fetched or written.

    There was none: every argument was ignored, so `--help` was a run. The
    parser exists to make an argument the tool does not understand stop it,
    which is the whole of its job -- `--dry-run` is the second reason and the
    smaller one.
    """
    parser = argparse.ArgumentParser(
        prog="watch.py",
        description="Check every watched source and record what moved.",
        epilog="A plain run rewrites state.json, WATCH.md and feed.xml, and an "
               "event recorded once is never recorded again -- so a run started "
               "by accident is not free.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="fetch as usual and say what would change, but write no file "
             "(the sources are still asked, so this is not free either)")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    sources = json.loads((ROOT / "sources.json").read_text("utf-8"))["sources"]
    state_path = ROOT / "state.json"
    state = json.loads(state_path.read_text("utf-8")) if state_path.exists() else {}
    today = now_iso()
    fresh = []

    for source in sources:
        entry = state.setdefault(source["key"], {})
        try:
            if source["kind"] == "gh_releases":
                fresh += diff_seen(entry, fetch_gh_releases(source["repo"]),
                                   source["label"], today)
            elif source["kind"] == "gh_dir":
                fresh += diff_seen(entry, fetch_gh_dir(source["repo"], source["path"]),
                                   source["label"], today)
            elif source["kind"] == "gh_issues":
                since = entry.get("checked", today)
                fresh += diff_seen(entry, fetch_gh_issues(source["repo"], since),
                                   source["label"], today)
            elif source["kind"] == "html":
                fresh += diff_hash(entry, fetch_html_hash(source["url"]),
                                   source["label"], source["url"], today)
        except TooLarge as large:
            # Same reasoning as a move: "this source is answering with more
            # than a source of its kind sends" is a fact about the source, and
            # a stale row in a table does not say it.
            fresh += diff_seen(entry, [oversize_item(large.url, large.limit)],
                               source["label"], today)
            print("oversize %s: %s" % (source["key"], large))
            continue
        except CrossHostRedirect as moved:
            # Not a failure to pass over in silence: a source pointing at
            # another host is the kind of thing this tower is for.
            fresh += diff_seen(entry, [moved_item(moved.url, moved.target)],
                               source["label"], today)
            print("moved %s: %s" % (source["key"], moved))
            continue
        except Exception as error:                          # noqa: BLE001
            # A dead source must not kill the tower; it shows up as a stale
            # "last checked" in the table instead, which a reader can see.
            print("skip %s: %s" % (source["key"], error))
            continue
        entry["checked"] = today

    events = (fresh + state.get("_events", []))[:MAX_EVENTS]
    if args.dry_run:
        # Before any write, and before the state dict is touched: an event
        # this run would record is an event a real run would then never
        # record again, and a dry run that consumed one would be a run.
        print("dry run: %d new, %d would be kept; nothing written" % (len(fresh), len(events)))
        return
    state["_events"] = events
    state_path.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", "utf-8")
    write_watch_md(sources, state, events)
    write_feed(events)
    print("events: %d new, %d kept" % (len(fresh), len(events)))


if __name__ == "__main__":
    main()
